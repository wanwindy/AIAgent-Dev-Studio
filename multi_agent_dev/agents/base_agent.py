"""
Agent基类定义
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

from ..api.claude_client import ClaudeAPIClient, ClaudeAPIError
from ..models.task import Task, AgentResult, AgentType, TaskStatus


logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Agent基类"""
    
    def __init__(
        self,
        name: str,
        agent_type: AgentType,
        api_client: ClaudeAPIClient,
        system_prompt: Optional[str] = None
    ):
        """
        初始化Agent
        
        Args:
            name: Agent名称
            agent_type: Agent类型
            api_client: Claude API客户端
            system_prompt: 系统提示
        """
        self.name = name
        self.agent_type = agent_type
        self.api_client = api_client
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        
        # 上下文记忆
        self.context_memory: List[Dict[str, Any]] = []
        self.max_memory_size = 10
        
        # 统计信息
        self.total_tasks = 0
        self.successful_tasks = 0
        self.failed_tasks = 0
        
    @abstractmethod
    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示"""
        pass
    
    @abstractmethod
    def build_prompt(self, task: Task) -> str:
        """
        构建任务提示
        
        Args:
            task: 任务对象
            
        Returns:
            构建的提示文本
        """
        pass
    
    @abstractmethod
    def parse_response(self, response: str, task: Task) -> Dict[str, Any]:
        """
        解析AI响应
        
        Args:
            response: AI响应文本
            task: 任务对象
            
        Returns:
            解析后的结果字典
        """
        pass
    
    def validate_result(self, result: Dict[str, Any], task: Task) -> bool:
        """
        验证结果是否有效
        
        Args:
            result: 结果字典
            task: 任务对象
            
        Returns:
            是否有效
        """
        # 基础验证：检查是否有错误
        if "error" in result:
            return False
        
        # 子类可以重写此方法进行更详细的验证
        return True
    
    async def process(self, task: Task) -> AgentResult:
        """
        处理任务
        
        Args:
            task: 要处理的任务
            
        Returns:
            处理结果
        """
        start_time = time.time()
        self.total_tasks += 1
        
        try:
            logger.info(f"{self.name} 开始处理任务: {task.title}")
            
            # 构建提示
            prompt = self.build_prompt(task)
            
            # 调用AI API
            response = await self.api_client.generate_response_with_retry(
                prompt=prompt,
                system_prompt=self.system_prompt,
                max_retries=task.max_retries
            )
            
            # 解析响应
            result = self.parse_response(response, task)
            
            # 验证结果
            if not self.validate_result(result, task):
                raise ValueError("Result validation failed")
            
            # 更新上下文记忆
            self.update_context(task, result)
            
            execution_time = time.time() - start_time
            self.successful_tasks += 1
            
            logger.info(
                f"{self.name} 成功完成任务: {task.title}, "
                f"耗时: {execution_time:.2f}s"
            )
            
            return AgentResult(
                agent_type=self.agent_type,
                task_id=task.id,
                success=True,
                output=result,
                execution_time=execution_time,
                tokens_used=0  # 这里可以从API客户端获取实际使用的token数
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.failed_tasks += 1
            
            error_msg = f"{self.name} 处理任务失败: {str(e)}"
            logger.error(error_msg)
            
            return AgentResult(
                agent_type=self.agent_type,
                task_id=task.id,
                success=False,
                error=error_msg,
                execution_time=execution_time
            )
    
    def update_context(self, task: Task, result: Dict[str, Any]):
        """
        更新上下文记忆
        
        Args:
            task: 任务对象
            result: 处理结果
        """
        context_entry = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task.id,
            "task_title": task.title,
            "result": result
        }
        
        self.context_memory.append(context_entry)
        
        # 限制记忆大小
        if len(self.context_memory) > self.max_memory_size:
            self.context_memory.pop(0)
    
    def get_context_summary(self) -> str:
        """
        获取上下文摘要
        
        Returns:
            上下文摘要文本
        """
        if not self.context_memory:
            return "无历史上下文"
        
        summary_parts = []
        for entry in self.context_memory[-5:]:  # 只取最近5条
            summary_parts.append(
                f"任务: {entry['task_title']}\n"
                f"结果: {str(entry['result'])[:200]}..."
            )
        
        return "\n\n".join(summary_parts)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取Agent统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "name": self.name,
            "agent_type": self.agent_type.value,
            "total_tasks": self.total_tasks,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": self.successful_tasks / max(self.total_tasks, 1),
            "context_memory_size": len(self.context_memory)
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.total_tasks = 0
        self.successful_tasks = 0
        self.failed_tasks = 0
        self.context_memory.clear()
    
    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """
        从响应中提取JSON
        
        Args:
            response: 响应文本
            
        Returns:
            提取的JSON字典
        """
        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取代码块中的JSON
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
            
            # 如果都失败了，返回错误
            raise ValueError(f"无法从响应中提取有效的JSON: {response[:200]}...")
