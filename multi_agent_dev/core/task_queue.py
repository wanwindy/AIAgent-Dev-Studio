"""
任务队列管理
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set
from collections import deque
from datetime import datetime

from ..models.task import Task, TaskStatus, TaskPriority


logger = logging.getLogger(__name__)


class TaskQueue:
    """任务队列管理器"""
    
    def __init__(self):
        """初始化任务队列"""
        self.pending_tasks: deque[Task] = deque()
        self.in_progress_tasks: Dict[str, Task] = {}
        self.completed_tasks: List[Task] = []
        self.failed_tasks: List[Task] = []
        self.cancelled_tasks: List[Task] = []
        
        # 任务依赖关系
        self.task_dependencies: Dict[str, Set[str]] = {}
        
        # 队列锁
        self._lock = asyncio.Lock()
        
    async def add_task(self, task: Task) -> bool:
        """
        添加任务到队列
        
        Args:
            task: 要添加的任务
            
        Returns:
            是否成功添加
        """
        async with self._lock:
            # 检查任务是否已存在
            if self._task_exists(task.id):
                logger.warning(f"任务 {task.id} 已存在，跳过添加")
                return False
            
            # 设置任务依赖关系
            if task.dependencies:
                self.task_dependencies[task.id] = set(task.dependencies)
            
            # 根据优先级插入任务
            self._insert_task_by_priority(task)
            
            logger.info(f"任务 {task.title} 已添加到队列，优先级: {task.priority}")
            return True
    
    async def add_tasks(self, tasks: List[Task]) -> int:
        """
        批量添加任务
        
        Args:
            tasks: 任务列表
            
        Returns:
            成功添加的任务数量
        """
        added_count = 0
        for task in tasks:
            if await self.add_task(task):
                added_count += 1
        
        logger.info(f"批量添加任务完成，成功添加 {added_count}/{len(tasks)} 个任务")
        return added_count
    
    async def get_next_task(self) -> Optional[Task]:
        """
        获取下一个可执行的任务
        
        Returns:
            下一个任务，如果没有可执行任务则返回None
        """
        async with self._lock:
            # 查找第一个满足依赖条件的任务
            for i, task in enumerate(self.pending_tasks):
                if self._can_execute_task(task):
                    # 移除任务并标记为进行中
                    task = self.pending_tasks[i]
                    del self.pending_tasks[i]
                    
                    task.status = TaskStatus.IN_PROGRESS
                    task.started_at = datetime.now()
                    self.in_progress_tasks[task.id] = task
                    
                    logger.info(f"获取到下一个任务: {task.title}")
                    return task
            
            return None
    
    async def complete_task(self, task_id: str, success: bool = True) -> bool:
        """
        标记任务完成
        
        Args:
            task_id: 任务ID
            success: 是否成功完成
            
        Returns:
            是否成功标记
        """
        async with self._lock:
            if task_id not in self.in_progress_tasks:
                logger.warning(f"任务 {task_id} 不在进行中列表")
                return False
            
            task = self.in_progress_tasks.pop(task_id)
            task.completed_at = datetime.now()
            
            if success:
                task.status = TaskStatus.COMPLETED
                self.completed_tasks.append(task)
                logger.info(f"任务 {task.title} 已完成")
            else:
                task.status = TaskStatus.FAILED
                self.failed_tasks.append(task)
                logger.error(f"任务 {task.title} 执行失败")
            
            # 清理依赖关系
            self._cleanup_dependencies(task_id)
            
            return True
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功取消
        """
        async with self._lock:
            # 从待执行队列中查找并移除
            for i, task in enumerate(self.pending_tasks):
                if task.id == task_id:
                    task = self.pending_tasks[i]
                    del self.pending_tasks[i]
                    task.status = TaskStatus.CANCELLED
                    self.cancelled_tasks.append(task)
                    logger.info(f"任务 {task.title} 已取消")
                    return True
            
            # 从进行中任务中查找并移除
            if task_id in self.in_progress_tasks:
                task = self.in_progress_tasks.pop(task_id)
                task.status = TaskStatus.CANCELLED
                self.cancelled_tasks.append(task)
                logger.info(f"正在执行的任务 {task.title} 已取消")
                return True
            
            logger.warning(f"未找到任务 {task_id}")
            return False
    
    async def retry_failed_task(self, task_id: str) -> bool:
        """
        重试失败的任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功重新加入队列
        """
        async with self._lock:
            # 在失败任务中查找
            for i, task in enumerate(self.failed_tasks):
                if task.id == task_id:
                    if task.retry_count >= task.max_retries:
                        logger.warning(f"任务 {task.title} 已达到最大重试次数")
                        return False
                    
                    # 移除失败任务并重新加入队列
                    task = self.failed_tasks.pop(i)
                    task.status = TaskStatus.PENDING
                    task.retry_count += 1
                    task.started_at = None
                    task.completed_at = None
                    task.error_message = None
                    
                    self._insert_task_by_priority(task)
                    logger.info(f"任务 {task.title} 已重新加入队列 (重试次数: {task.retry_count})")
                    return True
            
            logger.warning(f"未找到失败的任务 {task_id}")
            return False
    
    def get_queue_status(self) -> Dict[str, int]:
        """
        获取队列状态
        
        Returns:
            队列状态统计
        """
        return {
            "pending": len(self.pending_tasks),
            "in_progress": len(self.in_progress_tasks),
            "completed": len(self.completed_tasks),
            "failed": len(self.failed_tasks),
            "cancelled": len(self.cancelled_tasks),
            "total": (
                len(self.pending_tasks) + 
                len(self.in_progress_tasks) + 
                len(self.completed_tasks) + 
                len(self.failed_tasks) + 
                len(self.cancelled_tasks)
            )
        }
    
    def get_all_tasks(self) -> Dict[str, List[Task]]:
        """
        获取所有任务
        
        Returns:
            按状态分组的任务字典
        """
        return {
            "pending": list(self.pending_tasks),
            "in_progress": list(self.in_progress_tasks.values()),
            "completed": self.completed_tasks.copy(),
            "failed": self.failed_tasks.copy(),
            "cancelled": self.cancelled_tasks.copy()
        }
    
    def clear_completed_tasks(self):
        """清理已完成的任务"""
        cleared_count = len(self.completed_tasks)
        self.completed_tasks.clear()
        logger.info(f"已清理 {cleared_count} 个已完成任务")
    
    def _task_exists(self, task_id: str) -> bool:
        """检查任务是否已存在"""
        # 检查所有队列
        for task in self.pending_tasks:
            if task.id == task_id:
                return True
        
        if task_id in self.in_progress_tasks:
            return True
        
        for task_list in [self.completed_tasks, self.failed_tasks, self.cancelled_tasks]:
            for task in task_list:
                if task.id == task_id:
                    return True
        
        return False
    
    def _insert_task_by_priority(self, task: Task):
        """根据优先级插入任务"""
        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3
        }
        
        task_priority = priority_order.get(task.priority, 2)
        
        # 找到合适的插入位置
        insert_index = 0
        for i, existing_task in enumerate(self.pending_tasks):
            existing_priority = priority_order.get(existing_task.priority, 2)
            if task_priority <= existing_priority:
                insert_index = i
                break
            insert_index = i + 1
        
        self.pending_tasks.insert(insert_index, task)
    
    def _can_execute_task(self, task: Task) -> bool:
        """检查任务是否可以执行（依赖是否满足）"""
        if task.id not in self.task_dependencies:
            return True
        
        dependencies = self.task_dependencies[task.id]
        
        # 检查所有依赖任务是否已完成
        completed_task_ids = {task.id for task in self.completed_tasks}
        
        return dependencies.issubset(completed_task_ids)
    
    def _cleanup_dependencies(self, completed_task_id: str):
        """清理已完成任务的依赖关系"""
        # 从所有任务的依赖列表中移除已完成的任务
        for task_id, dependencies in self.task_dependencies.items():
            dependencies.discard(completed_task_id)
