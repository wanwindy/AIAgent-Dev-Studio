"""
工作流编排引擎
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

from .agent_manager import AgentManager
from .task_queue import TaskQueue
from .result_store import ResultStore
from ..models.task import (
    Task, TaskStatus, TaskPriority, AgentType,
    ProjectRequirements, ProjectResult, AgentResult
)


logger = logging.getLogger(__name__)


class WorkflowEngine:
    """工作流编排引擎"""
    
    def __init__(
        self,
        agent_manager: AgentManager,
        task_queue: Optional[TaskQueue] = None,
        result_store: Optional[ResultStore] = None
    ):
        """
        初始化工作流引擎
        
        Args:
            agent_manager: Agent管理器
            task_queue: 任务队列
            result_store: 结果存储
        """
        self.agent_manager = agent_manager
        self.task_queue = task_queue or TaskQueue()
        self.result_store = result_store or ResultStore()
        
        # 工作流状态
        self.current_project: Optional[ProjectResult] = None
        self.is_running = False
        
    async def execute_development_workflow(
        self,
        requirements: ProjectRequirements,
        workflow_config: Optional[Dict[str, Any]] = None
    ) -> ProjectResult:
        """
        执行完整的开发工作流
        
        Args:
            requirements: 项目需求
            workflow_config: 工作流配置
            
        Returns:
            项目开发结果
        """
        start_time = time.time()
        
        # 创建项目结果对象
        project_result = ProjectResult(
            requirements=requirements,
            status=TaskStatus.IN_PROGRESS
        )
        self.current_project = project_result
        self.is_running = True
        
        logger.info(f"开始执行开发工作流: {requirements.title}")
        
        try:
            # 阶段1: 项目经理分析需求
            logger.info("阶段1: 项目经理分析需求")
            pm_result = await self._execute_pm_analysis(requirements)
            project_result.agent_results.append(pm_result)
            
            if not pm_result.success:
                raise Exception(f"项目经理分析失败: {pm_result.error}")
            
            # 阶段2: 架构师设计系统架构
            logger.info("阶段2: 架构师设计系统架构")
            arch_result = await self._execute_architecture_design(requirements, pm_result)
            project_result.agent_results.append(arch_result)
            
            if not arch_result.success:
                raise Exception(f"架构设计失败: {arch_result.error}")
            
            # 阶段3: 开发者实现代码
            logger.info("阶段3: 开发者实现代码")
            dev_results = await self._execute_development(requirements, pm_result, arch_result)
            project_result.agent_results.extend(dev_results)
            
            # 收集所有生成的代码
            all_code_files = {}
            for result in dev_results:
                if result.success and 'files' in result.output:
                    all_code_files.update(result.output['files'])
            
            project_result.final_code = all_code_files
            
            # 阶段4: 测试员进行测试
            logger.info("阶段4: 测试员进行测试")
            test_results = await self._execute_testing(requirements, all_code_files)
            project_result.agent_results.extend(test_results)
            
            # 收集测试报告
            for result in test_results:
                if result.success:
                    project_result.test_reports.append(result.output)
            
            # 阶段5: 审查员进行代码审查
            logger.info("阶段5: 审查员进行代码审查")
            review_results = await self._execute_code_review(requirements, all_code_files, test_results)
            project_result.agent_results.extend(review_results)
            
            # 收集审查反馈
            for result in review_results:
                if result.success:
                    project_result.review_feedback.append(result.output)
            
            # 计算总体统计
            execution_time = time.time() - start_time
            project_result.total_execution_time = execution_time
            project_result.total_tokens_used = sum(r.tokens_used for r in project_result.agent_results)
            project_result.status = TaskStatus.COMPLETED
            project_result.completed_at = datetime.now()
            
            # 保存项目结果
            await self.result_store.save_project_result(project_result)
            await self.result_store.save_code_files(project_result.project_id, all_code_files)
            
            logger.info(
                f"开发工作流完成，耗时: {execution_time:.2f}s, "
                f"使用token: {project_result.total_tokens_used}"
            )
            
            return project_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            project_result.status = TaskStatus.FAILED
            project_result.total_execution_time = execution_time
            
            logger.error(f"开发工作流失败: {str(e)}")
            
            # 保存失败的项目结果
            await self.result_store.save_project_result(project_result)
            
            raise
        
        finally:
            self.is_running = False
    
    async def _execute_pm_analysis(self, requirements: ProjectRequirements) -> AgentResult:
        """执行项目经理分析"""
        task = Task(
            title="项目需求分析",
            description="分析项目需求并制定开发计划",
            assigned_agent=AgentType.PROJECT_MANAGER,
            priority=TaskPriority.CRITICAL,
            input_data={
                'requirements': f"{requirements.title}\n\n{requirements.description}",
                'constraints': requirements.constraints,
                'features': requirements.features
            }
        )
        
        return await self.agent_manager.execute_task(task)
    
    async def _execute_architecture_design(
        self,
        requirements: ProjectRequirements,
        pm_result: AgentResult
    ) -> AgentResult:
        """执行架构设计"""
        task = Task(
            title="系统架构设计",
            description="设计系统架构和技术规范",
            assigned_agent=AgentType.ARCHITECT,
            priority=TaskPriority.HIGH,
            input_data={
                'requirements': f"{requirements.title}\n\n{requirements.description}",
                'pm_analysis': pm_result.output,
                'constraints': requirements.constraints
            }
        )
        
        return await self.agent_manager.execute_task(task)
    
    async def _execute_development(
        self,
        requirements: ProjectRequirements,
        pm_result: AgentResult,
        arch_result: AgentResult
    ) -> List[AgentResult]:
        """执行代码开发"""
        results = []
        
        # 从项目经理分析中获取任务列表
        pm_output = pm_result.output
        tasks = pm_output.get('tasks', []) if isinstance(pm_output, dict) else []
        
        if not tasks:
            # 如果没有具体任务，创建一个通用开发任务
            tasks = [{
                'title': '核心功能实现',
                'description': '实现项目的核心功能',
                'priority': 'high'
            }]
        
        # 为每个开发任务创建Task并执行
        for i, task_info in enumerate(tasks):
            if isinstance(task_info, dict):
                task = Task(
                    title=task_info.get('title', f'开发任务 {i+1}'),
                    description=task_info.get('description', ''),
                    assigned_agent=AgentType.DEVELOPER,
                    priority=self._convert_priority(task_info.get('priority', 'medium')),
                    input_data={
                        'requirements': f"{requirements.title}\n\n{requirements.description}",
                        'pm_analysis': pm_result.output,
                        'architecture': arch_result.output,
                        'task_details': task_info
                    }
                )
                
                result = await self.agent_manager.execute_task(task)
                results.append(result)
                
                # 如果开发失败，记录但继续其他任务
                if not result.success:
                    logger.warning(f"开发任务失败: {task.title} - {result.error}")
        
        return results
    
    async def _execute_testing(
        self,
        requirements: ProjectRequirements,
        code_files: Dict[str, str]
    ) -> List[AgentResult]:
        """执行测试"""
        results = []
        
        # 创建测试任务
        task = Task(
            title="代码测试",
            description="为生成的代码编写和执行测试",
            assigned_agent=AgentType.TESTER,
            priority=TaskPriority.HIGH,
            input_data={
                'requirements': f"{requirements.title}\n\n{requirements.description}",
                'code_files': code_files
            }
        )
        
        result = await self.agent_manager.execute_task(task)
        results.append(result)
        
        return results
    
    async def _execute_code_review(
        self,
        requirements: ProjectRequirements,
        code_files: Dict[str, str],
        test_results: List[AgentResult]
    ) -> List[AgentResult]:
        """执行代码审查"""
        results = []
        
        # 收集测试文件
        test_files = {}
        for test_result in test_results:
            if test_result.success and 'test_files' in test_result.output:
                test_files.update(test_result.output['test_files'])
        
        # 创建审查任务
        task = Task(
            title="代码审查",
            description="审查代码质量、安全性和最佳实践",
            assigned_agent=AgentType.REVIEWER,
            priority=TaskPriority.MEDIUM,
            input_data={
                'requirements': f"{requirements.title}\n\n{requirements.description}",
                'code_files': code_files,
                'test_files': test_files,
                'test_results': [r.output for r in test_results if r.success]
            }
        )
        
        result = await self.agent_manager.execute_task(task)
        results.append(result)
        
        return results
    
    def _convert_priority(self, priority_str: str) -> TaskPriority:
        """转换优先级字符串"""
        priority_map = {
            'critical': TaskPriority.CRITICAL,
            'high': TaskPriority.HIGH,
            'medium': TaskPriority.MEDIUM,
            'low': TaskPriority.LOW
        }
        return priority_map.get(priority_str.lower(), TaskPriority.MEDIUM)
    
    async def get_workflow_status(self) -> Dict[str, Any]:
        """获取工作流状态"""
        status = {
            'is_running': self.is_running,
            'current_project': None,
            'queue_status': self.task_queue.get_queue_status(),
            'agent_stats': self.agent_manager.get_all_stats()
        }
        
        if self.current_project:
            status['current_project'] = {
                'project_id': self.current_project.project_id,
                'title': self.current_project.requirements.title,
                'status': self.current_project.status.value,
                'created_at': self.current_project.created_at.isoformat(),
                'total_tasks': len(self.current_project.tasks),
                'completed_results': len([r for r in self.current_project.agent_results if r.success])
            }
        
        return status
    
    async def stop_workflow(self):
        """停止当前工作流"""
        if self.is_running:
            logger.info("正在停止工作流...")
            self.is_running = False
            
            if self.current_project:
                self.current_project.status = TaskStatus.CANCELLED
                await self.result_store.save_project_result(self.current_project)
