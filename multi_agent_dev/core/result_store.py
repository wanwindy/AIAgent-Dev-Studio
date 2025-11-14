"""
结果存储管理
"""

import json
import logging
import os
import aiofiles
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from ..models.task import Task, AgentResult, ProjectResult, TaskStatus
from config import settings


logger = logging.getLogger(__name__)


class ResultStore:
    """结果存储管理器"""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        初始化结果存储
        
        Args:
            storage_dir: 存储目录，默认使用配置中的目录
        """
        self.storage_dir = Path(storage_dir or settings.results_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存
        self.project_results: Dict[str, ProjectResult] = {}
        self.agent_results: Dict[str, List[AgentResult]] = {}
        
        logger.info(f"结果存储初始化完成，存储目录: {self.storage_dir}")
    
    async def save_project_result(self, project_result: ProjectResult) -> bool:
        """
        保存项目结果
        
        Args:
            project_result: 项目结果
            
        Returns:
            是否保存成功
        """
        try:
            # 更新内存缓存
            self.project_results[project_result.project_id] = project_result
            
            # 保存到文件
            file_path = self.storage_dir / f"project_{project_result.project_id}.json"
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(project_result.json(indent=2, ensure_ascii=False))
            
            logger.info(f"项目结果已保存: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存项目结果失败: {str(e)}")
            return False
    
    async def load_project_result(self, project_id: str) -> Optional[ProjectResult]:
        """
        加载项目结果
        
        Args:
            project_id: 项目ID
            
        Returns:
            项目结果，如果不存在则返回None
        """
        # 先检查内存缓存
        if project_id in self.project_results:
            return self.project_results[project_id]
        
        # 从文件加载
        file_path = self.storage_dir / f"project_{project_id}.json"
        
        if not file_path.exists():
            logger.warning(f"项目结果文件不存在: {file_path}")
            return None
        
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                project_result = ProjectResult.parse_raw(content)
                
            # 更新内存缓存
            self.project_results[project_id] = project_result
            
            logger.info(f"项目结果已加载: {file_path}")
            return project_result
            
        except Exception as e:
            logger.error(f"加载项目结果失败: {str(e)}")
            return None
    
    async def save_agent_result(self, agent_result: AgentResult) -> bool:
        """
        保存Agent结果
        
        Args:
            agent_result: Agent结果
            
        Returns:
            是否保存成功
        """
        try:
            # 更新内存缓存
            if agent_result.task_id not in self.agent_results:
                self.agent_results[agent_result.task_id] = []
            self.agent_results[agent_result.task_id].append(agent_result)
            
            # 保存到文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"agent_{agent_result.agent_type.value}_{agent_result.task_id}_{timestamp}.json"
            file_path = self.storage_dir / "agent_results" / file_name
            
            # 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(agent_result.json(indent=2, ensure_ascii=False))
            
            logger.debug(f"Agent结果已保存: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存Agent结果失败: {str(e)}")
            return False
    
    async def get_agent_results(self, task_id: str) -> List[AgentResult]:
        """
        获取任务的所有Agent结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            Agent结果列表
        """
        # 先检查内存缓存
        if task_id in self.agent_results:
            return self.agent_results[task_id].copy()
        
        # 从文件加载
        results = []
        agent_results_dir = self.storage_dir / "agent_results"
        
        if not agent_results_dir.exists():
            return results
        
        try:
            for file_path in agent_results_dir.glob(f"*_{task_id}_*.json"):
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    agent_result = AgentResult.parse_raw(content)
                    results.append(agent_result)
            
            # 按时间戳排序
            results.sort(key=lambda x: x.timestamp)
            
            # 更新内存缓存
            self.agent_results[task_id] = results.copy()
            
            logger.debug(f"加载了 {len(results)} 个Agent结果，任务ID: {task_id}")
            return results
            
        except Exception as e:
            logger.error(f"加载Agent结果失败: {str(e)}")
            return []
    
    async def save_code_files(self, project_id: str, code_files: Dict[str, str]) -> bool:
        """
        保存生成的代码文件
        
        Args:
            project_id: 项目ID
            code_files: 代码文件字典 {文件路径: 文件内容}
            
        Returns:
            是否保存成功
        """
        try:
            code_dir = self.storage_dir / "generated_code" / project_id
            code_dir.mkdir(parents=True, exist_ok=True)
            
            for file_path, content in code_files.items():
                # 确保文件路径安全
                safe_path = code_dir / file_path.lstrip('/')
                safe_path.parent.mkdir(parents=True, exist_ok=True)
                
                async with aiofiles.open(safe_path, 'w', encoding='utf-8') as f:
                    await f.write(content)
            
            logger.info(f"代码文件已保存到: {code_dir}")
            return True
            
        except Exception as e:
            logger.error(f"保存代码文件失败: {str(e)}")
            return False
    
    async def export_project_summary(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        导出项目摘要
        
        Args:
            project_id: 项目ID
            
        Returns:
            项目摘要字典
        """
        project_result = await self.load_project_result(project_id)
        if not project_result:
            return None
        
        summary = {
            "project_id": project_id,
            "title": project_result.requirements.title,
            "description": project_result.requirements.description,
            "status": project_result.status.value,
            "created_at": project_result.created_at.isoformat(),
            "completed_at": project_result.completed_at.isoformat() if project_result.completed_at else None,
            "total_execution_time": project_result.total_execution_time,
            "total_tokens_used": project_result.total_tokens_used,
            "tasks_summary": {
                "total": len(project_result.tasks),
                "completed": len([t for t in project_result.tasks if t.status == TaskStatus.COMPLETED]),
                "failed": len([t for t in project_result.tasks if t.status == TaskStatus.FAILED]),
                "cancelled": len([t for t in project_result.tasks if t.status == TaskStatus.CANCELLED])
            },
            "agents_summary": {
                "total_results": len(project_result.agent_results),
                "successful_results": len([r for r in project_result.agent_results if r.success]),
                "failed_results": len([r for r in project_result.agent_results if not r.success])
            },
            "generated_files": len(project_result.final_code),
            "test_reports": len(project_result.test_reports),
            "review_feedback": len(project_result.review_feedback)
        }
        
        return summary
    
    async def list_projects(self) -> List[Dict[str, Any]]:
        """
        列出所有项目
        
        Returns:
            项目列表
        """
        projects = []
        
        try:
            for file_path in self.storage_dir.glob("project_*.json"):
                project_id = file_path.stem.replace("project_", "")
                summary = await self.export_project_summary(project_id)
                if summary:
                    projects.append(summary)
            
            # 按创建时间排序
            projects.sort(key=lambda x: x["created_at"], reverse=True)
            
            return projects
            
        except Exception as e:
            logger.error(f"列出项目失败: {str(e)}")
            return []
    
    async def cleanup_old_results(self, days: int = 30) -> int:
        """
        清理旧的结果文件
        
        Args:
            days: 保留天数
            
        Returns:
            清理的文件数量
        """
        cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)
        cleaned_count = 0
        
        try:
            for file_path in self.storage_dir.rglob("*.json"):
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    cleaned_count += 1
            
            logger.info(f"清理了 {cleaned_count} 个旧结果文件")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理旧结果文件失败: {str(e)}")
            return 0
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        获取存储统计信息
        
        Returns:
            存储统计信息
        """
        try:
            total_size = 0
            file_count = 0
            
            for file_path in self.storage_dir.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
            
            return {
                "storage_dir": str(self.storage_dir),
                "total_files": file_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "cached_projects": len(self.project_results),
                "cached_agent_results": len(self.agent_results)
            }
            
        except Exception as e:
            logger.error(f"获取存储统计失败: {str(e)}")
            return {}
