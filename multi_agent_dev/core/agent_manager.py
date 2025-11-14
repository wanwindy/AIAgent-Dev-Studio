"""
Agent管理器
"""

import logging
from typing import Dict, List, Optional, Any
import asyncio

from ..api.claude_client import ClaudeAPIClient
from ..models.task import Task, AgentResult, AgentType, TaskStatus
from ..agents.base_agent import BaseAgent
# 延迟导入避免循环依赖
# from ..agents.project_manager_agent import ProjectManagerAgent
# from ..agents.architect_agent import ArchitectAgent
# from ..agents.developer_agent import DeveloperAgent
# from ..agents.tester_agent import TesterAgent
# from ..agents.reviewer_agent import ReviewerAgent


logger = logging.getLogger(__name__)


class AgentManager:
    """Agent管理器"""
    
    def __init__(self, api_client: ClaudeAPIClient):
        """
        初始化Agent管理器
        
        Args:
            api_client: Claude API客户端
        """
        self.api_client = api_client
        self.agents: Dict[AgentType, BaseAgent] = {}
        self._initialize_agents()
        
    def _initialize_agents(self):
        """初始化所有Agent"""
        # 延迟导入避免循环依赖
        from ..agents.project_manager_agent import ProjectManagerAgent
        from ..agents.architect_agent import ArchitectAgent
        from ..agents.developer_agent import DeveloperAgent
        from ..agents.tester_agent import TesterAgent
        from ..agents.reviewer_agent import ReviewerAgent

        self.agents = {
            AgentType.PROJECT_MANAGER: ProjectManagerAgent(
                name="项目经理",
                api_client=self.api_client
            ),
            AgentType.ARCHITECT: ArchitectAgent(
                name="架构师",
                api_client=self.api_client
            ),
            AgentType.DEVELOPER: DeveloperAgent(
                name="开发者",
                api_client=self.api_client
            ),
            AgentType.TESTER: TesterAgent(
                name="测试员",
                api_client=self.api_client
            ),
            AgentType.REVIEWER: ReviewerAgent(
                name="审查员",
                api_client=self.api_client
            )
        }
        
        logger.info(f"初始化了 {len(self.agents)} 个Agent")
    
    def get_agent(self, agent_type: AgentType) -> Optional[BaseAgent]:
        """
        获取指定类型的Agent
        
        Args:
            agent_type: Agent类型
            
        Returns:
            Agent实例，如果不存在则返回None
        """
        return self.agents.get(agent_type)
    
    async def execute_task(self, task: Task) -> AgentResult:
        """
        执行单个任务
        
        Args:
            task: 要执行的任务
            
        Returns:
            执行结果
        """
        if not task.assigned_agent:
            raise ValueError(f"任务 {task.id} 未分配Agent")
        
        agent = self.get_agent(task.assigned_agent)
        if not agent:
            raise ValueError(f"未找到类型为 {task.assigned_agent} 的Agent")
        
        logger.info(f"开始执行任务 {task.title}，分配给 {agent.name}")
        
        # 更新任务状态
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = task.updated_at
        
        try:
            result = await agent.process(task)
            
            if result.success:
                task.status = TaskStatus.COMPLETED
                task.completed_at = task.updated_at
                task.output_data = result.output
            else:
                task.status = TaskStatus.FAILED
                task.error_message = result.error
                task.retry_count += 1
            
            return result
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.retry_count += 1
            
            logger.error(f"任务执行异常: {str(e)}")
            
            return AgentResult(
                agent_type=task.assigned_agent,
                task_id=task.id,
                success=False,
                error=str(e)
            )
    
    async def execute_tasks_parallel(
        self,
        tasks: List[Task],
        max_concurrency: int = 3
    ) -> List[AgentResult]:
        """
        并行执行多个任务
        
        Args:
            tasks: 任务列表
            max_concurrency: 最大并发数
            
        Returns:
            执行结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def execute_with_semaphore(task: Task) -> AgentResult:
            async with semaphore:
                return await self.execute_task(task)
        
        logger.info(f"开始并行执行 {len(tasks)} 个任务，最大并发数: {max_concurrency}")
        
        tasks_coroutines = [execute_with_semaphore(task) for task in tasks]
        results = await asyncio.gather(*tasks_coroutines, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"任务 {tasks[i].id} 执行异常: {str(result)}")
                processed_results.append(AgentResult(
                    agent_type=tasks[i].assigned_agent,
                    task_id=tasks[i].id,
                    success=False,
                    error=str(result)
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def execute_tasks_sequential(self, tasks: List[Task]) -> List[AgentResult]:
        """
        顺序执行多个任务
        
        Args:
            tasks: 任务列表
            
        Returns:
            执行结果列表
        """
        results = []
        
        for task in tasks:
            logger.info(f"顺序执行任务: {task.title}")
            result = await self.execute_task(task)
            results.append(result)
            
            # 如果任务失败且不允许继续，则停止执行
            if not result.success and task.retry_count >= task.max_retries:
                logger.error(f"任务 {task.title} 失败且超过最大重试次数，停止后续任务执行")
                break
        
        return results
    
    def get_all_stats(self) -> Dict[str, Any]:
        """
        获取所有Agent的统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            "api_client_stats": self.api_client.get_stats(),
            "agents_stats": {}
        }
        
        for agent_type, agent in self.agents.items():
            stats["agents_stats"][agent_type.value] = agent.get_stats()
        
        return stats
    
    def reset_all_stats(self):
        """重置所有统计信息"""
        self.api_client.reset_stats()
        for agent in self.agents.values():
            agent.reset_stats()
    
    def get_agent_by_name(self, name: str) -> Optional[BaseAgent]:
        """
        根据名称获取Agent
        
        Args:
            name: Agent名称
            
        Returns:
            Agent实例，如果不存在则返回None
        """
        for agent in self.agents.values():
            if agent.name == name:
                return agent
        return None
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """
        列出所有Agent信息
        
        Returns:
            Agent信息列表
        """
        agent_list = []
        for agent_type, agent in self.agents.items():
            agent_list.append({
                "type": agent_type.value,
                "name": agent.name,
                "stats": agent.get_stats()
            })
        return agent_list
