"""
重试处理机制
"""

import asyncio
import logging
import time
from typing import Callable, Any, Optional, Dict, List
from functools import wraps
from enum import Enum

from config import settings


logger = logging.getLogger(__name__)


class RetryStrategy(str, Enum):
    """重试策略枚举"""
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"


class RetryHandler:
    """重试处理器"""
    
    def __init__(
        self,
        max_retries: int = None,
        base_delay: float = None,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0
    ):
        """
        初始化重试处理器
        
        Args:
            max_retries: 最大重试次数
            base_delay: 基础延迟时间（秒）
            strategy: 重试策略
            max_delay: 最大延迟时间（秒）
            backoff_factor: 退避因子
        """
        self.max_retries = max_retries or settings.max_retries
        self.base_delay = base_delay or settings.retry_delay
        self.strategy = strategy
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        
        # 统计信息
        self.total_attempts = 0
        self.total_retries = 0
        self.success_count = 0
        self.failure_count = 0
        self.retry_history: List[Dict[str, Any]] = []
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        exception_types: tuple = (Exception,),
        retry_condition: Optional[Callable[[Exception], bool]] = None,
        **kwargs
    ) -> Any:
        """
        执行函数并在失败时重试
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            exception_types: 需要重试的异常类型
            retry_condition: 重试条件函数
            **kwargs: 函数关键字参数
            
        Returns:
            函数执行结果
            
        Raises:
            最后一次执行的异常
        """
        last_exception = None
        attempt_start_time = time.time()
        
        for attempt in range(self.max_retries + 1):
            self.total_attempts += 1
            
            try:
                # 执行函数
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # 成功执行
                self.success_count += 1
                
                if attempt > 0:
                    logger.info(f"函数在第{attempt + 1}次尝试后成功执行")
                
                # 记录成功的重试历史
                self._record_retry_history(
                    func.__name__,
                    attempt,
                    True,
                    None,
                    time.time() - attempt_start_time
                )
                
                return result
                
            except exception_types as e:
                last_exception = e
                
                # 检查是否应该重试
                if retry_condition and not retry_condition(e):
                    logger.info(f"重试条件不满足，停止重试: {str(e)}")
                    break
                
                if attempt < self.max_retries:
                    self.total_retries += 1
                    delay = self._calculate_delay(attempt)
                    
                    logger.warning(
                        f"函数执行失败 (尝试 {attempt + 1}/{self.max_retries + 1}): {str(e)}, "
                        f"{delay:.1f}秒后重试"
                    )
                    
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"函数在{self.max_retries + 1}次尝试后仍然失败")
        
        # 记录失败的重试历史
        self.failure_count += 1
        self._record_retry_history(
            func.__name__,
            self.max_retries,
            False,
            str(last_exception),
            time.time() - attempt_start_time
        )
        
        # 抛出最后一次的异常
        raise last_exception
    
    def retry_decorator(
        self,
        exception_types: tuple = (Exception,),
        retry_condition: Optional[Callable[[Exception], bool]] = None
    ):
        """
        重试装饰器
        
        Args:
            exception_types: 需要重试的异常类型
            retry_condition: 重试条件函数
            
        Returns:
            装饰器函数
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await self.execute_with_retry(
                    func,
                    *args,
                    exception_types=exception_types,
                    retry_condition=retry_condition,
                    **kwargs
                )
            return wrapper
        return decorator
    
    def _calculate_delay(self, attempt: int) -> float:
        """
        计算延迟时间
        
        Args:
            attempt: 当前尝试次数（从0开始）
            
        Returns:
            延迟时间（秒）
        """
        if self.strategy == RetryStrategy.FIXED:
            delay = self.base_delay
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.base_delay * (attempt + 1)
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.base_delay * (self.backoff_factor ** attempt)
        else:
            delay = self.base_delay
        
        # 限制最大延迟时间
        return min(delay, self.max_delay)
    
    def _record_retry_history(
        self,
        function_name: str,
        attempts: int,
        success: bool,
        error: Optional[str],
        duration: float
    ):
        """记录重试历史"""
        record = {
            'timestamp': time.time(),
            'function_name': function_name,
            'attempts': attempts + 1,
            'success': success,
            'error': error,
            'duration': duration,
            'strategy': self.strategy.value
        }
        
        self.retry_history.append(record)
        
        # 限制历史记录数量
        if len(self.retry_history) > 1000:
            self.retry_history = self.retry_history[-500:]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取重试统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'total_attempts': self.total_attempts,
            'total_retries': self.total_retries,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': self.success_count / max(self.total_attempts, 1),
            'retry_rate': self.total_retries / max(self.total_attempts, 1),
            'config': {
                'max_retries': self.max_retries,
                'base_delay': self.base_delay,
                'strategy': self.strategy.value,
                'max_delay': self.max_delay,
                'backoff_factor': self.backoff_factor
            },
            'recent_history': self.retry_history[-10:]  # 最近10条记录
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.total_attempts = 0
        self.total_retries = 0
        self.success_count = 0
        self.failure_count = 0
        self.retry_history.clear()
    
    def get_failure_analysis(self) -> Dict[str, Any]:
        """
        获取失败分析
        
        Returns:
            失败分析结果
        """
        if not self.retry_history:
            return {'message': '暂无重试历史数据'}
        
        # 分析失败模式
        failed_records = [r for r in self.retry_history if not r['success']]
        
        if not failed_records:
            return {'message': '暂无失败记录'}
        
        # 统计失败原因
        error_counts = {}
        function_failures = {}
        
        for record in failed_records:
            error = record.get('error', 'Unknown')
            function_name = record.get('function_name', 'Unknown')
            
            error_counts[error] = error_counts.get(error, 0) + 1
            function_failures[function_name] = function_failures.get(function_name, 0) + 1
        
        return {
            'total_failures': len(failed_records),
            'most_common_errors': sorted(
                error_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            'functions_with_most_failures': sorted(
                function_failures.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            'average_attempts_before_failure': sum(
                r['attempts'] for r in failed_records
            ) / len(failed_records)
        }


# 全局重试处理器实例
default_retry_handler = RetryHandler()


def retry_on_failure(
    max_retries: int = None,
    base_delay: float = None,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    exception_types: tuple = (Exception,),
    retry_condition: Optional[Callable[[Exception], bool]] = None
):
    """
    重试装饰器的便捷函数
    
    Args:
        max_retries: 最大重试次数
        base_delay: 基础延迟时间
        strategy: 重试策略
        exception_types: 需要重试的异常类型
        retry_condition: 重试条件函数
        
    Returns:
        装饰器函数
    """
    retry_handler = RetryHandler(
        max_retries=max_retries,
        base_delay=base_delay,
        strategy=strategy
    )
    
    return retry_handler.retry_decorator(
        exception_types=exception_types,
        retry_condition=retry_condition
    )
