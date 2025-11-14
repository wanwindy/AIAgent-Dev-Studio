"""
监控和指标收集
"""

import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
import threading

from config import settings


logger = logging.getLogger(__name__)


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self, enabled: bool = None):
        """
        初始化指标收集器
        
        Args:
            enabled: 是否启用指标收集
        """
        self.enabled = enabled if enabled is not None else settings.metrics_enabled
        
        if self.enabled:
            self.registry = CollectorRegistry()
            self._initialize_metrics()
        
        # 内存中的指标存储
        self.metrics_history: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        
    def _initialize_metrics(self):
        """初始化Prometheus指标"""
        # API调用指标
        self.api_calls_total = Counter(
            'claude_api_calls_total',
            'Total number of Claude API calls',
            ['agent_type', 'status'],
            registry=self.registry
        )
        
        self.api_call_duration = Histogram(
            'claude_api_call_duration_seconds',
            'Duration of Claude API calls',
            ['agent_type'],
            registry=self.registry
        )
        
        self.api_tokens_used = Counter(
            'claude_api_tokens_used_total',
            'Total number of tokens used',
            ['agent_type'],
            registry=self.registry
        )
        
        # 任务执行指标
        self.tasks_total = Counter(
            'tasks_total',
            'Total number of tasks',
            ['agent_type', 'status'],
            registry=self.registry
        )
        
        self.task_duration = Histogram(
            'task_duration_seconds',
            'Duration of task execution',
            ['agent_type'],
            registry=self.registry
        )
        
        # 系统指标
        self.active_projects = Gauge(
            'active_projects',
            'Number of active projects',
            registry=self.registry
        )
        
        self.queue_size = Gauge(
            'task_queue_size',
            'Size of task queue',
            ['status'],
            registry=self.registry
        )
        
        # 错误指标
        self.errors_total = Counter(
            'errors_total',
            'Total number of errors',
            ['error_type', 'component'],
            registry=self.registry
        )
    
    def record_api_call(
        self,
        agent_type: str,
        duration: float,
        tokens_used: int,
        success: bool
    ):
        """
        记录API调用指标
        
        Args:
            agent_type: Agent类型
            duration: 调用持续时间
            tokens_used: 使用的token数
            success: 是否成功
        """
        if not self.enabled:
            return
        
        status = 'success' if success else 'failure'
        
        self.api_calls_total.labels(agent_type=agent_type, status=status).inc()
        self.api_call_duration.labels(agent_type=agent_type).observe(duration)
        self.api_tokens_used.labels(agent_type=agent_type).inc(tokens_used)
        
        # 记录到内存历史
        self._record_to_history('api_call', {
            'agent_type': agent_type,
            'duration': duration,
            'tokens_used': tokens_used,
            'success': success
        })
    
    def record_task_execution(
        self,
        agent_type: str,
        duration: float,
        success: bool
    ):
        """
        记录任务执行指标
        
        Args:
            agent_type: Agent类型
            duration: 执行持续时间
            success: 是否成功
        """
        if not self.enabled:
            return
        
        status = 'success' if success else 'failure'
        
        self.tasks_total.labels(agent_type=agent_type, status=status).inc()
        self.task_duration.labels(agent_type=agent_type).observe(duration)
        
        # 记录到内存历史
        self._record_to_history('task_execution', {
            'agent_type': agent_type,
            'duration': duration,
            'success': success
        })
    
    def update_queue_metrics(self, queue_status: Dict[str, int]):
        """
        更新队列指标
        
        Args:
            queue_status: 队列状态字典
        """
        if not self.enabled:
            return
        
        for status, count in queue_status.items():
            self.queue_size.labels(status=status).set(count)
    
    def update_active_projects(self, count: int):
        """
        更新活跃项目数量
        
        Args:
            count: 活跃项目数量
        """
        if not self.enabled:
            return
        
        self.active_projects.set(count)
    
    def record_error(self, error_type: str, component: str):
        """
        记录错误
        
        Args:
            error_type: 错误类型
            component: 组件名称
        """
        if not self.enabled:
            return
        
        self.errors_total.labels(error_type=error_type, component=component).inc()
        
        # 记录到内存历史
        self._record_to_history('error', {
            'error_type': error_type,
            'component': component
        })
    
    def get_metrics_text(self) -> str:
        """
        获取Prometheus格式的指标文本
        
        Returns:
            指标文本
        """
        if not self.enabled:
            return "# Metrics collection is disabled"
        
        return generate_latest(self.registry).decode('utf-8')
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        获取汇总统计信息
        
        Returns:
            统计信息字典
        """
        with self.lock:
            if not self.metrics_history:
                return {'message': '暂无指标数据'}
            
            # 计算时间范围
            now = datetime.now()
            last_hour = now - timedelta(hours=1)
            last_day = now - timedelta(days=1)
            
            # 过滤最近的指标
            recent_metrics = [
                m for m in self.metrics_history
                if datetime.fromisoformat(m['timestamp']) > last_hour
            ]
            
            daily_metrics = [
                m for m in self.metrics_history
                if datetime.fromisoformat(m['timestamp']) > last_day
            ]
            
            # API调用统计
            api_calls = [m for m in recent_metrics if m['type'] == 'api_call']
            successful_api_calls = [m for m in api_calls if m['data']['success']]
            
            # 任务执行统计
            task_executions = [m for m in recent_metrics if m['type'] == 'task_execution']
            successful_tasks = [m for m in task_executions if m['data']['success']]
            
            # 错误统计
            errors = [m for m in daily_metrics if m['type'] == 'error']
            
            return {
                'time_range': {
                    'last_hour': len(recent_metrics),
                    'last_day': len(daily_metrics)
                },
                'api_calls': {
                    'total_last_hour': len(api_calls),
                    'successful_last_hour': len(successful_api_calls),
                    'success_rate': len(successful_api_calls) / max(len(api_calls), 1),
                    'avg_duration': sum(m['data']['duration'] for m in api_calls) / max(len(api_calls), 1),
                    'total_tokens': sum(m['data']['tokens_used'] for m in api_calls)
                },
                'task_executions': {
                    'total_last_hour': len(task_executions),
                    'successful_last_hour': len(successful_tasks),
                    'success_rate': len(successful_tasks) / max(len(task_executions), 1),
                    'avg_duration': sum(m['data']['duration'] for m in task_executions) / max(len(task_executions), 1)
                },
                'errors': {
                    'total_last_day': len(errors),
                    'error_types': self._count_by_field(errors, 'error_type'),
                    'components': self._count_by_field(errors, 'component')
                }
            }
    
    def get_agent_performance(self) -> Dict[str, Any]:
        """
        获取Agent性能统计
        
        Returns:
            Agent性能字典
        """
        with self.lock:
            # 按Agent类型分组统计
            agent_stats = {}
            
            for metric in self.metrics_history:
                if metric['type'] in ['api_call', 'task_execution']:
                    agent_type = metric['data']['agent_type']
                    
                    if agent_type not in agent_stats:
                        agent_stats[agent_type] = {
                            'api_calls': [],
                            'task_executions': [],
                            'total_tokens': 0,
                            'total_duration': 0
                        }
                    
                    if metric['type'] == 'api_call':
                        agent_stats[agent_type]['api_calls'].append(metric)
                        agent_stats[agent_type]['total_tokens'] += metric['data']['tokens_used']
                    else:
                        agent_stats[agent_type]['task_executions'].append(metric)
                    
                    agent_stats[agent_type]['total_duration'] += metric['data']['duration']
            
            # 计算每个Agent的统计信息
            performance = {}
            for agent_type, stats in agent_stats.items():
                api_calls = stats['api_calls']
                task_executions = stats['task_executions']
                
                performance[agent_type] = {
                    'api_calls_count': len(api_calls),
                    'api_success_rate': len([c for c in api_calls if c['data']['success']]) / max(len(api_calls), 1),
                    'task_executions_count': len(task_executions),
                    'task_success_rate': len([t for t in task_executions if t['data']['success']]) / max(len(task_executions), 1),
                    'total_tokens_used': stats['total_tokens'],
                    'total_duration': stats['total_duration'],
                    'avg_api_duration': sum(c['data']['duration'] for c in api_calls) / max(len(api_calls), 1),
                    'avg_task_duration': sum(t['data']['duration'] for t in task_executions) / max(len(task_executions), 1)
                }
            
            return performance
    
    def _record_to_history(self, metric_type: str, data: Dict[str, Any]):
        """记录指标到内存历史"""
        with self.lock:
            record = {
                'timestamp': datetime.now().isoformat(),
                'type': metric_type,
                'data': data
            }
            
            self.metrics_history.append(record)
            
            # 限制历史记录数量（保留最近24小时的数据）
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.metrics_history = [
                m for m in self.metrics_history
                if datetime.fromisoformat(m['timestamp']) > cutoff_time
            ]
    
    def _count_by_field(self, metrics: List[Dict], field: str) -> Dict[str, int]:
        """按字段统计指标"""
        counts = {}
        for metric in metrics:
            value = metric['data'].get(field, 'unknown')
            counts[value] = counts.get(value, 0) + 1
        return counts
    
    def export_metrics_to_file(self, file_path: str) -> bool:
        """
        导出指标到文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否导出成功
        """
        try:
            import json
            
            export_data = {
                'export_time': datetime.now().isoformat(),
                'summary_stats': self.get_summary_stats(),
                'agent_performance': self.get_agent_performance(),
                'raw_metrics': self.metrics_history[-1000:]  # 最近1000条记录
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"指标已导出到: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出指标失败: {str(e)}")
            return False


# 全局指标收集器实例
metrics_collector = MetricsCollector()
