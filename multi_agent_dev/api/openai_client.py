"""
OpenAI API客户端封装
支持OpenAI官方API和兼容的代理服务
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
import aiohttp
import json
import time

from config import settings

logger = logging.getLogger(__name__)


class OpenAIAPIError(Exception):
    """OpenAI API相关异常"""
    pass


class OpenAIAPIClient:
    """OpenAI API客户端"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        初始化OpenAI API客户端
        
        Args:
            api_key: OpenAI API密钥
            base_url: API基础URL
        """
        self.api_key = api_key or getattr(settings, 'openai_api_key', '')
        self.base_url = base_url or getattr(settings, 'openai_base_url', 'https://api.openai.com')
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.model = getattr(settings, 'openai_model', 'gpt-3.5-turbo')
        self.max_tokens = getattr(settings, 'openai_max_tokens', 4000)
        self.timeout = getattr(settings, 'openai_timeout', 60)
        
        # 统计信息
        self.total_requests = 0
        self.total_tokens = 0
        self.total_errors = 0
    
    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        生成AI响应
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            model: 使用的模型
            max_tokens: 最大token数
            temperature: 温度参数
            **kwargs: 其他参数
            
        Returns:
            AI生成的响应文本
        """
        model = model or self.model
        max_tokens = max_tokens or self.max_tokens
        
        # 构建消息
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # 构建请求数据
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url.rstrip('/')}/v1/chat/completions"
        
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        # 更新统计信息
                        self.total_requests += 1
                        if 'usage' in result:
                            self.total_tokens += result['usage'].get('total_tokens', 0)
                        
                        execution_time = time.time() - start_time
                        logger.info(f"OpenAI API请求成功，耗时: {execution_time:.2f}s")
                        
                        return result['choices'][0]['message']['content']
                    else:
                        error_text = await response.text()
                        self.total_errors += 1
                        raise OpenAIAPIError(f"API请求失败: {response.status} - {error_text}")
                        
        except asyncio.TimeoutError:
            self.total_errors += 1
            raise OpenAIAPIError(f"API请求超时: {self.timeout}s")
        except Exception as e:
            self.total_errors += 1
            raise OpenAIAPIError(f"API请求异常: {str(e)}")
    
    async def generate_response_with_retry(
        self,
        prompt: str,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        带重试机制的响应生成
        """
        max_retries = max_retries or getattr(settings, 'max_retries', 3)
        retry_delay = retry_delay or getattr(settings, 'retry_delay', 1.0)
        
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                return await self.generate_response(prompt, **kwargs)
                
            except OpenAIAPIError as e:
                last_error = e
                if attempt < max_retries:
                    wait_time = retry_delay * (2 ** attempt)
                    logger.warning(f"OpenAI API调用失败，{wait_time:.1f}s后重试: {str(e)}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"OpenAI API调用失败，已达最大重试次数")
        
        raise last_error
    
    def get_stats(self) -> Dict[str, Any]:
        """获取API调用统计信息"""
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "total_errors": self.total_errors,
            "error_rate": self.total_errors / max(self.total_requests, 1),
            "avg_tokens_per_request": self.total_tokens / max(self.total_requests, 1)
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.total_requests = 0
        self.total_tokens = 0
        self.total_errors = 0


class UnifiedAPIClient:
    """统一API客户端，支持多种AI服务"""
    
    def __init__(self, provider: str = "claude"):
        """
        初始化统一API客户端
        
        Args:
            provider: AI服务提供商 ("claude", "openai", "mock")
        """
        self.provider = provider.lower()
        
        if self.provider == "claude":
            from .claude_client import ClaudeAPIClient
            self.client = ClaudeAPIClient()
        elif self.provider == "openai":
            self.client = OpenAIAPIClient()
        elif self.provider == "mock":
            from .mock_client import MockClaudeAPIClient

            self.client = MockClaudeAPIClient()
        else:
            raise ValueError(f"不支持的AI服务提供商: {provider}")
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """生成AI响应"""
        return await self.client.generate_response(prompt, **kwargs)
    
    async def generate_response_with_retry(self, prompt: str, **kwargs) -> str:
        """带重试的响应生成"""
        if hasattr(self.client, 'generate_response_with_retry'):
            return await self.client.generate_response_with_retry(prompt, **kwargs)
        else:
            return await self.client.generate_response(prompt, **kwargs)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.client.get_stats()
    
    def reset_stats(self):
        """重置统计信息"""
        self.client.reset_stats()
