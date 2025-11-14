"""
全局上下文管理器
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)


class ContextEntry:
    """上下文条目"""
    
    def __init__(self, key: str, value: Any, timestamp: datetime = None, metadata: Dict = None):
        self.key = key
        self.value = value
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
        self.access_count = 0
        self.last_accessed = self.timestamp
    
    def access(self):
        """记录访问"""
        self.access_count += 1
        self.last_accessed = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'key': self.key,
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed.isoformat()
        }


class GlobalContextManager:
    """全局上下文管理器"""
    
    def __init__(self, storage_dir: str = "context_storage"):
        """
        初始化全局上下文管理器
        
        Args:
            storage_dir: 上下文存储目录
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # 内存中的上下文缓存
        self.project_contexts: Dict[str, Dict[str, ContextEntry]] = {}
        self.agent_contexts: Dict[str, Dict[str, ContextEntry]] = {}
        self.task_contexts: Dict[str, Dict[str, ContextEntry]] = {}
        self.shared_artifacts: Dict[str, ContextEntry] = {}
        
        # 上下文访问锁
        self._lock = asyncio.Lock()
        
        # 配置
        self.max_context_size = 1000  # 每个上下文的最大条目数
        self.auto_save_interval = 300  # 自动保存间隔（秒）
        
        # 启动自动保存任务
        asyncio.create_task(self._auto_save_loop())
    
    async def update_project_context(self, project_id: str, context_data: Dict[str, Any]):
        """
        更新项目级上下文
        
        Args:
            project_id: 项目ID
            context_data: 上下文数据
        """
        async with self._lock:
            if project_id not in self.project_contexts:
                self.project_contexts[project_id] = {}
            
            for key, value in context_data.items():
                entry = ContextEntry(
                    key=key,
                    value=value,
                    metadata={'level': 'project', 'project_id': project_id}
                )
                self.project_contexts[project_id][key] = entry
            
            # 限制上下文大小
            await self._trim_context(self.project_contexts[project_id])
            
            logger.debug(f"更新项目上下文: {project_id}, 键: {list(context_data.keys())}")
    
    async def update_agent_context(self, agent_id: str, context_data: Dict[str, Any]):
        """
        更新Agent级上下文
        
        Args:
            agent_id: Agent ID
            context_data: 上下文数据
        """
        async with self._lock:
            if agent_id not in self.agent_contexts:
                self.agent_contexts[agent_id] = {}
            
            for key, value in context_data.items():
                entry = ContextEntry(
                    key=key,
                    value=value,
                    metadata={'level': 'agent', 'agent_id': agent_id}
                )
                self.agent_contexts[agent_id][key] = entry
            
            await self._trim_context(self.agent_contexts[agent_id])
            
            logger.debug(f"更新Agent上下文: {agent_id}, 键: {list(context_data.keys())}")
    
    async def update_task_context(self, task_id: str, context_data: Dict[str, Any]):
        """
        更新任务级上下文
        
        Args:
            task_id: 任务ID
            context_data: 上下文数据
        """
        async with self._lock:
            if task_id not in self.task_contexts:
                self.task_contexts[task_id] = {}
            
            for key, value in context_data.items():
                entry = ContextEntry(
                    key=key,
                    value=value,
                    metadata={'level': 'task', 'task_id': task_id}
                )
                self.task_contexts[task_id][key] = entry
            
            await self._trim_context(self.task_contexts[task_id])
            
            logger.debug(f"更新任务上下文: {task_id}, 键: {list(context_data.keys())}")
    
    async def update_stage_context(self, project_id: str, stage_name: str, stage_result: Dict[str, Any]):
        """
        更新阶段上下文
        
        Args:
            project_id: 项目ID
            stage_name: 阶段名称
            stage_result: 阶段结果
        """
        stage_context = {
            f"stage_{stage_name}_result": stage_result,
            f"stage_{stage_name}_completed_at": datetime.now().isoformat(),
            f"stage_{stage_name}_deliverables": stage_result.get('deliverables', {}),
            f"stage_{stage_name}_status": stage_result.get('status', 'unknown')
        }
        
        await self.update_project_context(project_id, stage_context)
    
    async def add_shared_artifact(self, artifact_id: str, artifact_data: Any, metadata: Dict = None):
        """
        添加共享工件
        
        Args:
            artifact_id: 工件ID
            artifact_data: 工件数据
            metadata: 元数据
        """
        async with self._lock:
            entry = ContextEntry(
                key=artifact_id,
                value=artifact_data,
                metadata=metadata or {'level': 'shared'}
            )
            self.shared_artifacts[artifact_id] = entry
            
            logger.debug(f"添加共享工件: {artifact_id}")
    
    async def get_context_for_agent(self, project_id: str, agent_id: str) -> Dict[str, Any]:
        """
        获取Agent所需的上下文信息
        
        Args:
            project_id: 项目ID
            agent_id: Agent ID
            
        Returns:
            上下文信息字典
        """
        async with self._lock:
            context = {}
            
            # 项目级上下文
            if project_id in self.project_contexts:
                for key, entry in self.project_contexts[project_id].items():
                    entry.access()
                    context[f"project_{key}"] = entry.value
            
            # Agent级上下文
            if agent_id in self.agent_contexts:
                for key, entry in self.agent_contexts[agent_id].items():
                    entry.access()
                    context[f"agent_{key}"] = entry.value
            
            # 相关的共享工件
            for artifact_id, entry in self.shared_artifacts.items():
                if self._is_relevant_artifact(artifact_id, agent_id, project_id):
                    entry.access()
                    context[f"artifact_{artifact_id}"] = entry.value
            
            logger.debug(f"为Agent {agent_id} 获取上下文，包含 {len(context)} 个条目")
            return context
    
    async def get_global_context(self, project_id: str) -> Dict[str, Any]:
        """
        获取全局上下文
        
        Args:
            project_id: 项目ID
            
        Returns:
            全局上下文字典
        """
        async with self._lock:
            context = {}
            
            # 项目级上下文
            if project_id in self.project_contexts:
                for key, entry in self.project_contexts[project_id].items():
                    entry.access()
                    context[key] = entry.value
            
            # 所有共享工件
            for artifact_id, entry in self.shared_artifacts.items():
                entry.access()
                context[f"artifact_{artifact_id}"] = entry.value
            
            return context
    
    async def get_context_summary(self, project_id: str, max_items: int = 20) -> str:
        """
        获取上下文摘要
        
        Args:
            project_id: 项目ID
            max_items: 最大条目数
            
        Returns:
            上下文摘要文本
        """
        context = await self.get_global_context(project_id)
        
        summary_parts = []
        item_count = 0
        
        for key, value in context.items():
            if item_count >= max_items:
                break
            
            # 格式化值
            if isinstance(value, dict):
                value_str = json.dumps(value, ensure_ascii=False)[:200]
            elif isinstance(value, list):
                value_str = f"列表({len(value)}项)"
            else:
                value_str = str(value)[:200]
            
            summary_parts.append(f"- {key}: {value_str}")
            item_count += 1
        
        if len(context) > max_items:
            summary_parts.append(f"... 还有 {len(context) - max_items} 个条目")
        
        return "\n".join(summary_parts)
    
    async def search_context(self, project_id: str, query: str) -> List[Dict[str, Any]]:
        """
        搜索上下文
        
        Args:
            project_id: 项目ID
            query: 搜索查询
            
        Returns:
            匹配的上下文条目列表
        """
        async with self._lock:
            results = []
            query_lower = query.lower()
            
            # 搜索项目上下文
            if project_id in self.project_contexts:
                for key, entry in self.project_contexts[project_id].items():
                    if (query_lower in key.lower() or 
                        query_lower in str(entry.value).lower()):
                        results.append({
                            'level': 'project',
                            'key': key,
                            'value': entry.value,
                            'timestamp': entry.timestamp.isoformat(),
                            'relevance_score': self._calculate_relevance(query, key, entry.value)
                        })
            
            # 搜索共享工件
            for artifact_id, entry in self.shared_artifacts.items():
                if (query_lower in artifact_id.lower() or 
                    query_lower in str(entry.value).lower()):
                    results.append({
                        'level': 'shared',
                        'key': artifact_id,
                        'value': entry.value,
                        'timestamp': entry.timestamp.isoformat(),
                        'relevance_score': self._calculate_relevance(query, artifact_id, entry.value)
                    })
            
            # 按相关性排序
            results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            return results
    
    async def clear_context(self, project_id: str = None, agent_id: str = None):
        """
        清理上下文
        
        Args:
            project_id: 项目ID（可选）
            agent_id: Agent ID（可选）
        """
        async with self._lock:
            if project_id:
                if project_id in self.project_contexts:
                    del self.project_contexts[project_id]
                    logger.info(f"清理项目上下文: {project_id}")
            
            if agent_id:
                if agent_id in self.agent_contexts:
                    del self.agent_contexts[agent_id]
                    logger.info(f"清理Agent上下文: {agent_id}")
            
            if not project_id and not agent_id:
                # 清理所有上下文
                self.project_contexts.clear()
                self.agent_contexts.clear()
                self.task_contexts.clear()
                self.shared_artifacts.clear()
                logger.info("清理所有上下文")
    
    async def save_context_to_disk(self, project_id: str = None):
        """
        保存上下文到磁盘
        
        Args:
            project_id: 项目ID（可选，如果不指定则保存所有）
        """
        try:
            if project_id:
                # 保存特定项目的上下文
                if project_id in self.project_contexts:
                    context_file = self.storage_dir / f"project_{project_id}.json"
                    context_data = {
                        key: entry.to_dict() 
                        for key, entry in self.project_contexts[project_id].items()
                    }
                    
                    with open(context_file, 'w', encoding='utf-8') as f:
                        json.dump(context_data, f, ensure_ascii=False, indent=2)
                    
                    logger.debug(f"保存项目上下文到磁盘: {project_id}")
            else:
                # 保存所有上下文
                all_contexts = {
                    'project_contexts': {
                        pid: {key: entry.to_dict() for key, entry in contexts.items()}
                        for pid, contexts in self.project_contexts.items()
                    },
                    'agent_contexts': {
                        aid: {key: entry.to_dict() for key, entry in contexts.items()}
                        for aid, contexts in self.agent_contexts.items()
                    },
                    'shared_artifacts': {
                        key: entry.to_dict() for key, entry in self.shared_artifacts.items()
                    }
                }
                
                context_file = self.storage_dir / "global_context.json"
                with open(context_file, 'w', encoding='utf-8') as f:
                    json.dump(all_contexts, f, ensure_ascii=False, indent=2)
                
                logger.debug("保存全局上下文到磁盘")
                
        except Exception as e:
            logger.error(f"保存上下文到磁盘失败: {str(e)}")
    
    async def load_context_from_disk(self, project_id: str = None):
        """
        从磁盘加载上下文
        
        Args:
            project_id: 项目ID（可选）
        """
        try:
            if project_id:
                # 加载特定项目的上下文
                context_file = self.storage_dir / f"project_{project_id}.json"
                if context_file.exists():
                    with open(context_file, 'r', encoding='utf-8') as f:
                        context_data = json.load(f)
                    
                    self.project_contexts[project_id] = {}
                    for key, entry_data in context_data.items():
                        entry = ContextEntry(
                            key=entry_data['key'],
                            value=entry_data['value'],
                            timestamp=datetime.fromisoformat(entry_data['timestamp']),
                            metadata=entry_data['metadata']
                        )
                        entry.access_count = entry_data['access_count']
                        entry.last_accessed = datetime.fromisoformat(entry_data['last_accessed'])
                        self.project_contexts[project_id][key] = entry
                    
                    logger.debug(f"从磁盘加载项目上下文: {project_id}")
            else:
                # 加载全局上下文
                context_file = self.storage_dir / "global_context.json"
                if context_file.exists():
                    with open(context_file, 'r', encoding='utf-8') as f:
                        all_contexts = json.load(f)
                    
                    # 恢复项目上下文
                    for pid, contexts in all_contexts.get('project_contexts', {}).items():
                        self.project_contexts[pid] = {}
                        for key, entry_data in contexts.items():
                            entry = ContextEntry(
                                key=entry_data['key'],
                                value=entry_data['value'],
                                timestamp=datetime.fromisoformat(entry_data['timestamp']),
                                metadata=entry_data['metadata']
                            )
                            entry.access_count = entry_data['access_count']
                            entry.last_accessed = datetime.fromisoformat(entry_data['last_accessed'])
                            self.project_contexts[pid][key] = entry
                    
                    # 恢复Agent上下文
                    for aid, contexts in all_contexts.get('agent_contexts', {}).items():
                        self.agent_contexts[aid] = {}
                        for key, entry_data in contexts.items():
                            entry = ContextEntry(
                                key=entry_data['key'],
                                value=entry_data['value'],
                                timestamp=datetime.fromisoformat(entry_data['timestamp']),
                                metadata=entry_data['metadata']
                            )
                            entry.access_count = entry_data['access_count']
                            entry.last_accessed = datetime.fromisoformat(entry_data['last_accessed'])
                            self.agent_contexts[aid][key] = entry
                    
                    # 恢复共享工件
                    for key, entry_data in all_contexts.get('shared_artifacts', {}).items():
                        entry = ContextEntry(
                            key=entry_data['key'],
                            value=entry_data['value'],
                            timestamp=datetime.fromisoformat(entry_data['timestamp']),
                            metadata=entry_data['metadata']
                        )
                        entry.access_count = entry_data['access_count']
                        entry.last_accessed = datetime.fromisoformat(entry_data['last_accessed'])
                        self.shared_artifacts[key] = entry
                    
                    logger.debug("从磁盘加载全局上下文")
                    
        except Exception as e:
            logger.error(f"从磁盘加载上下文失败: {str(e)}")
    
    async def _trim_context(self, context_dict: Dict[str, ContextEntry]):
        """修剪上下文大小"""
        if len(context_dict) > self.max_context_size:
            # 按最后访问时间排序，删除最旧的条目
            sorted_entries = sorted(
                context_dict.items(),
                key=lambda x: x[1].last_accessed
            )
            
            # 保留最新的条目
            to_keep = sorted_entries[-self.max_context_size:]
            context_dict.clear()
            context_dict.update(to_keep)
    
    def _is_relevant_artifact(self, artifact_id: str, agent_id: str, project_id: str) -> bool:
        """判断工件是否与Agent相关"""
        # 简单的相关性判断逻辑，可以根据需要扩展
        return (artifact_id.startswith(project_id) or 
                artifact_id.startswith(agent_id) or
                'global' in artifact_id)
    
    def _calculate_relevance(self, query: str, key: str, value: Any) -> float:
        """计算相关性分数"""
        score = 0.0
        query_lower = query.lower()
        
        # 键匹配
        if query_lower in key.lower():
            score += 1.0
        
        # 值匹配
        value_str = str(value).lower()
        if query_lower in value_str:
            score += 0.5
        
        # 精确匹配加分
        if query_lower == key.lower():
            score += 2.0
        
        return score
    
    async def _auto_save_loop(self):
        """自动保存循环"""
        while True:
            try:
                await asyncio.sleep(self.auto_save_interval)
                await self.save_context_to_disk()
            except Exception as e:
                logger.error(f"自动保存上下文失败: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'project_contexts_count': len(self.project_contexts),
            'agent_contexts_count': len(self.agent_contexts),
            'task_contexts_count': len(self.task_contexts),
            'shared_artifacts_count': len(self.shared_artifacts),
            'total_entries': (
                sum(len(ctx) for ctx in self.project_contexts.values()) +
                sum(len(ctx) for ctx in self.agent_contexts.values()) +
                sum(len(ctx) for ctx in self.task_contexts.values()) +
                len(self.shared_artifacts)
            )
        }
