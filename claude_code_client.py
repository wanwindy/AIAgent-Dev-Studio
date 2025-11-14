#!/usr/bin/env python3
"""
Claude Code兼容的API客户端
专门用于与只支持Claude Code客户端的API服务通信
"""

import asyncio
import aiohttp
import json
import logging
import time
from typing import Dict, List, Optional, Any
from config import settings

logger = logging.getLogger(__name__)


class ClaudeCodeAPIError(Exception):
    """Claude Code API异常类"""
    pass


class ClaudeCodeAPIClient:
    """Claude Code兼容的API客户端"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        初始化Claude Code API客户端
        
        Args:
            api_key: API密钥
            base_url: API基础URL
        """
        self.api_key = api_key or settings.claude_api_key
        self.base_url = base_url or settings.claude_base_url
        self.model = settings.claude_model
        self.max_tokens = settings.claude_max_tokens
        self.timeout = settings.claude_timeout
        
        if not self.api_key:
            raise ValueError("Claude API key is required")
        if not self.base_url:
            raise ValueError("Claude base URL is required")
        
        # 统计信息
        self.total_requests = 0
        self.total_tokens = 0
        self.total_errors = 0
    
    def _get_claude_code_headers(self) -> Dict[str, str]:
        """获取Claude Code专用的请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Claude-Code/1.0.0 Chrome/120.0.0.0 Electron/28.0.0 Safari/537.36",
            "anthropic-version": "2023-06-01",
            "anthropic-dangerous-direct-browser-access": "true",
            "x-api-key": self.api_key,
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "Origin": "vscode-webview://webview",
            "Referer": "vscode-webview://webview/",
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Claude-Code";v="1"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"'
        }
    
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
            
        Raises:
            ClaudeCodeAPIError: API调用失败时抛出
        """
        model = model or self.model
        max_tokens = max_tokens or self.max_tokens
        
        # 构建消息
        messages = [{"role": "user", "content": prompt}]
        
        # 构建请求体
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
            "temperature": temperature,
            **kwargs
        }
        
        # 添加系统提示
        if system_prompt:
            payload["system"] = system_prompt
        
        url = f"{self.base_url.rstrip('/')}/api/v1/messages"
        headers = self._get_claude_code_headers()
        
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                logger.debug(f"Sending request to Claude Code API: {url}")
                logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
                
                async with session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                ) as response:
                    
                    execution_time = time.time() - start_time
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        # 更新统计信息
                        self.total_requests += 1
                        if 'usage' in result:
                            usage = result['usage']
                            self.total_tokens += usage.get('input_tokens', 0) + usage.get('output_tokens', 0)
                        
                        logger.info(
                            f"Claude Code API request completed in {execution_time:.2f}s"
                        )
                        
                        # 提取响应文本
                        if 'content' in result and result['content']:
                            return result['content'][0]['text']
                        elif 'choices' in result and result['choices']:
                            return result['choices'][0]['message']['content']
                        else:
                            return str(result)
                    
                    else:
                        error_text = await response.text()
                        self.total_errors += 1
                        
                        logger.error(f"Claude Code API error: {response.status} - {error_text}")
                        raise ClaudeCodeAPIError(f"API request failed: {response.status} - {error_text}")
        
        except asyncio.TimeoutError:
            self.total_errors += 1
            raise ClaudeCodeAPIError(f"Request timeout after {self.timeout}s")
        except Exception as e:
            self.total_errors += 1
            if isinstance(e, ClaudeCodeAPIError):
                raise
            raise ClaudeCodeAPIError(f"Request failed: {str(e)}")
    
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
            retry_delay: 重试延迟
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
                
            except ClaudeCodeAPIError as e:
                last_error = e
                if attempt < max_retries:
                    wait_time = retry_delay * (2 ** attempt)  # 指数退避
                    logger.warning(
                        f"Claude Code API call failed (attempt {attempt + 1}/{max_retries + 1}), "
                        f"retrying in {wait_time:.1f}s: {str(e)}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Claude Code API call failed after {max_retries + 1} attempts")
        
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
        
        async def generate_single(prompt: str) -> str:
            async with semaphore:
                return await self.generate_response(prompt, **kwargs)
        
        tasks = [generate_single(prompt) for prompt in prompts]
        return await asyncio.gather(*tasks)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        error_rate = self.total_errors / max(self.total_requests + self.total_errors, 1)
        avg_tokens = self.total_tokens / max(self.total_requests, 1)
        
        return {
            'total_requests': self.total_requests,
            'total_tokens': self.total_tokens,
            'total_errors': self.total_errors,
            'error_rate': error_rate,
            'avg_tokens_per_request': avg_tokens
        }


async def test_claude_code_client():
    """测试Claude Code客户端"""
    print("🧪 测试Claude Code兼容客户端")
    print("=" * 50)
    
    try:
        # 创建客户端
        client = ClaudeCodeAPIClient()
        print(f"✅ 客户端创建成功")
        print(f"📊 Base URL: {client.base_url}")
        print(f"🔑 API Key: {client.api_key[:8]}...{client.api_key[-4:]}")
        
        # 测试简单请求
        print(f"\n🚀 测试简单请求...")
        response = await client.generate_response(
            prompt="请回复'Claude Code API测试成功'",
            max_tokens=50,
            temperature=0.1
        )
        print(f"📥 响应: {response}")
        
        # 测试重试机制
        print(f"\n🔄 测试重试机制...")
        response2 = await client.generate_response_with_retry(
            prompt="请简单介绍一下你自己",
            max_tokens=100,
            max_retries=2
        )
        print(f"📥 响应: {response2[:100]}...")
        
        # 显示统计信息
        stats = client.get_stats()
        print(f"\n📊 统计信息: {stats}")
        
        print(f"\n🎉 Claude Code客户端测试成功！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False


if __name__ == "__main__":
    asyncio.run(test_claude_code_client())
