"""
Claude API客户端封装
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any

import aiohttp

try:
    import anthropic
    from anthropic import AsyncAnthropic
except ImportError:  # pragma: no cover - optional dependency for mock mode
    anthropic = None
    AsyncAnthropic = None

from config import settings
from ..models.task import AgentResult, AgentType


logger = logging.getLogger(__name__)


class ClaudeAPIError(Exception):
    """Claude API异常类"""
    pass


if anthropic is not None:
    _AnthropicAPIError = anthropic.APIError
else:  # pragma: no cover - used when anthropic isn't installed
    class _AnthropicAPIError(Exception):
        """Fallback error used when anthropic package is unavailable."""

        pass


class ClaudeAPIClient:
    """Claude API客户端"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        初始化Claude API客户端

        Args:
            api_key: Claude API密钥，如果不提供则从配置中获取
            base_url: API基础URL，如果不提供则从配置中获取
        """
        # 检查是否使用模拟API
        configured_mock = getattr(settings, 'use_mock_api', False)
        self.use_mock = configured_mock or anthropic is None

        if anthropic is None and not configured_mock:
            logger.warning(
                "anthropic package未安装，自动切换到模拟API客户端。"
            )

        if self.use_mock:
            logger.info("使用模拟API客户端")
            from .mock_client import MockClaudeAPIClient

            self._mock_client = MockClaudeAPIClient()
            self.api_key = api_key or "mock-api-key"
            self.base_url = "mock://localhost"
        else:
            if anthropic is None:
                raise ImportError(
                    "anthropic package is required when USE_MOCK_API is false. "
                    "Install it via `pip install anthropic`."
                )

            self.api_key = api_key or settings.claude_api_key
            if not self.api_key:
                raise ValueError("Claude API key is required")

            self.base_url = base_url or getattr(settings, 'claude_base_url', None)

            # 创建客户端，支持自定义base_url
            if self.base_url and self.base_url != "mock://localhost":
                self.client = AsyncAnthropic(api_key=self.api_key, base_url=self.base_url)
            else:
                self.client = AsyncAnthropic(api_key=self.api_key)

        self.model = settings.claude_model
        self.max_tokens = settings.claude_max_tokens
        self.timeout = settings.claude_timeout
        
        # 统计信息
        self.total_requests = 0
        self.total_tokens = 0
        self.total_errors = 0

        # 检测到的有效端点
        self.detected_endpoint = None

    async def detect_api_endpoint(self) -> Optional[str]:
        """
        自动检测可用的API端点

        Returns:
            检测到的端点路径，如果没有找到则返回None
        """
        if not self.base_url:
            return None

        endpoints_to_test = [
            "/v1/chat/completions",
            "/api/v1/chat/completions",
            "/v1/messages",
            "/api/v1/messages",
            "/chat/completions",
            "/completions",
            "/v1/completions",
            "/api/v1/completions"
        ]

        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints_to_test:
                try:
                    url = f"{self.base_url.rstrip('/')}{endpoint}"
                    # 发送OPTIONS请求检查端点是否存在
                    async with session.options(url, timeout=5) as response:
                        if response.status in [200, 405, 404]:  # 404也可能表示端点存在但需要POST
                            logger.info(f"检测到可能的API端点: {endpoint}")
                            self.detected_endpoint = endpoint
                            return endpoint
                except Exception as e:
                    logger.debug(f"端点 {endpoint} 测试失败: {str(e)}")
                    continue

        logger.warning("未能检测到有效的API端点")
        return None

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
            model: 使用的模型，默认使用配置中的模型
            max_tokens: 最大token数
            temperature: 温度参数
            **kwargs: 其他参数

        Returns:
            AI生成的响应文本

        Raises:
            ClaudeAPIError: API调用失败时抛出
        """
        # 如果使用模拟API
        if self.use_mock:
            return await self._mock_client.generate_response(
                prompt=prompt,
                system_prompt=system_prompt,
                **kwargs
            )

        model = model or self.model
        max_tokens = max_tokens or self.max_tokens
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            start_time = time.time()
            
            # 构建请求参数
            request_params = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": messages,
                "temperature": temperature,
                **kwargs
            }
            
            # 添加系统提示
            if system_prompt:
                request_params["system"] = system_prompt
            
            logger.debug(f"Sending request to Claude API: {model}")
            
            response = await asyncio.wait_for(
                self.client.messages.create(**request_params),
                timeout=self.timeout
            )
            
            execution_time = time.time() - start_time
            
            # 更新统计信息
            self.total_requests += 1
            self.total_tokens += response.usage.input_tokens + response.usage.output_tokens
            
            logger.info(
                f"Claude API request completed in {execution_time:.2f}s, "
                f"tokens: {response.usage.input_tokens + response.usage.output_tokens}"
            )
            
            return response.content[0].text
            
        except asyncio.TimeoutError:
            self.total_errors += 1
            error_msg = f"Claude API request timeout after {self.timeout}s"
            logger.error(error_msg)
            raise ClaudeAPIError(error_msg)
            
        except _AnthropicAPIError as e:
            self.total_errors += 1
            error_msg = f"Claude API error: {str(e)}"
            logger.error(error_msg)
            raise ClaudeAPIError(error_msg)
            
        except Exception as e:
            self.total_errors += 1
            error_msg = f"Unexpected error in Claude API call: {str(e)}"
            logger.error(error_msg)
            raise ClaudeAPIError(error_msg)
    
    async def generate_response_with_retry(
        self,
        prompt: str,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        带重试机制的响应生成
        
        Args:
            prompt: 用户提示
            max_retries: 最大重试次数
            retry_delay: 重试延迟时间
            **kwargs: 其他参数
            
        Returns:
            AI生成的响应文本
        """
        max_retries = max_retries or settings.max_retries
        retry_delay = retry_delay or settings.retry_delay
        
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                return await self.generate_response(prompt, **kwargs)
                
            except ClaudeAPIError as e:
                last_error = e
                if attempt < max_retries:
                    wait_time = retry_delay * (2 ** attempt)  # 指数退避
                    logger.warning(
                        f"Claude API call failed (attempt {attempt + 1}/{max_retries + 1}), "
                        f"retrying in {wait_time:.1f}s: {str(e)}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Claude API call failed after {max_retries + 1} attempts")
        
        raise last_error
    
    async def batch_generate(
        self,
        prompts: List[str],
        concurrency_limit: int = 3,
        **kwargs
    ) -> List[str]:
        """
        批量生成响应
        
        Args:
            prompts: 提示列表
            concurrency_limit: 并发限制
            **kwargs: 其他参数
            
        Returns:
            响应列表
        """
        semaphore = asyncio.Semaphore(concurrency_limit)
        
        async def generate_with_semaphore(prompt: str) -> str:
            async with semaphore:
                return await self.generate_response_with_retry(prompt, **kwargs)
        
        tasks = [generate_with_semaphore(prompt) for prompt in prompts]
        return await asyncio.gather(*tasks)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取API调用统计信息
        
        Returns:
            统计信息字典
        """
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
