#!/usr/bin/env python3
"""
API问题诊断脚本
专门用于诊断API连接问题，包括请求格式、请求头、端点路径等
"""

import asyncio
import aiohttp
import json
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from config import settings

async def test_basic_connectivity():
    """测试基本网络连接"""
    print("🌐 测试基本网络连接...")
    
    base_url = settings.claude_base_url
    print(f"  目标URL: {base_url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            # 测试基本连接
            async with session.get(base_url, timeout=10) as response:
                print(f"  ✅ 基本连接成功，状态码: {response.status}")
                print(f"  📋 响应头: {dict(response.headers)}")
                
                # 尝试读取响应内容
                try:
                    text = await response.text()
                    print(f"  📄 响应内容前200字符: {text[:200]}")
                except Exception as e:
                    print(f"  ⚠️ 无法读取响应内容: {e}")
                
                return True
                
    except Exception as e:
        print(f"  ❌ 基本连接失败: {e}")
        return False

async def test_api_endpoints():
    """测试不同的API端点"""
    print("\n🔍 测试API端点...")
    
    base_url = settings.claude_base_url
    api_key = settings.claude_api_key
    
    # 常见的API端点
    endpoints = [
        "/v1/messages",
        "/api/v1/messages", 
        "/v1/chat/completions",
        "/api/v1/chat/completions",
        "/claude/v1/messages",
        "/anthropic/v1/messages"
    ]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "Claude-API-Client/1.0",
        "anthropic-version": "2023-06-01"
    }
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints:
            url = f"{base_url.rstrip('/')}{endpoint}"
            print(f"  🔍 测试端点: {endpoint}")
            
            try:
                # 先用OPTIONS请求测试
                async with session.options(url, headers=headers, timeout=10) as response:
                    print(f"    OPTIONS状态码: {response.status}")
                    if response.status in [200, 405, 404]:
                        print(f"    ✅ 端点可能存在")
                        
                        # 尝试POST请求
                        test_payload = {
                            "model": "claude-3-5-sonnet-20241022",
                            "max_tokens": 10,
                            "messages": [{"role": "user", "content": "test"}]
                        }
                        
                        async with session.post(url, headers=headers, json=test_payload, timeout=10) as post_response:
                            print(f"    POST状态码: {post_response.status}")
                            
                            if post_response.status == 200:
                                print(f"    ✅ 端点工作正常: {endpoint}")
                                return endpoint
                            else:
                                error_text = await post_response.text()
                                print(f"    ❌ POST失败: {error_text[:200]}")
                    
            except Exception as e:
                print(f"    ❌ 端点测试失败: {e}")
    
    return None

async def test_request_formats():
    """测试不同的请求格式"""
    print("\n📝 测试请求格式...")
    
    base_url = settings.claude_base_url
    api_key = settings.claude_api_key
    
    # 测试不同的请求格式
    formats = [
        {
            "name": "Anthropic Messages API",
            "endpoint": "/v1/messages",
            "headers": {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            },
            "payload": {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "test"}]
            }
        },
        {
            "name": "OpenAI Compatible API",
            "endpoint": "/v1/chat/completions",
            "headers": {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            "payload": {
                "model": "claude-3-5-sonnet-20241022",
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 10
            }
        },
        {
            "name": "Alternative Messages API",
            "endpoint": "/api/v1/messages",
            "headers": {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "x-api-key": api_key
            },
            "payload": {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "test"}]
            }
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for format_info in formats:
            print(f"  📝 测试格式: {format_info['name']}")
            url = f"{base_url.rstrip('/')}{format_info['endpoint']}"
            
            try:
                async with session.post(
                    url,
                    headers=format_info['headers'],
                    json=format_info['payload'],
                    timeout=15
                ) as response:
                    print(f"    状态码: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print(f"    ✅ 格式正确，响应: {str(result)[:100]}...")
                        return format_info
                    else:
                        error_text = await response.text()
                        print(f"    ❌ 请求失败: {error_text[:200]}")
                        
            except Exception as e:
                print(f"    ❌ 请求异常: {e}")
    
    return None

async def test_authentication():
    """测试认证方式"""
    print("\n🔐 测试认证方式...")
    
    base_url = settings.claude_base_url
    api_key = settings.claude_api_key
    
    auth_methods = [
        {
            "name": "Bearer Token",
            "headers": {"Authorization": f"Bearer {api_key}"}
        },
        {
            "name": "X-API-Key",
            "headers": {"x-api-key": api_key}
        },
        {
            "name": "API-Key",
            "headers": {"api-key": api_key}
        },
        {
            "name": "Both Bearer and X-API-Key",
            "headers": {
                "Authorization": f"Bearer {api_key}",
                "x-api-key": api_key
            }
        }
    ]
    
    test_payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 10,
        "messages": [{"role": "user", "content": "test"}]
    }
    
    async with aiohttp.ClientSession() as session:
        for auth in auth_methods:
            print(f"  🔐 测试认证: {auth['name']}")
            
            headers = {
                "Content-Type": "application/json",
                **auth['headers']
            }
            
            url = f"{base_url.rstrip('/')}/v1/messages"
            
            try:
                async with session.post(url, headers=headers, json=test_payload, timeout=10) as response:
                    print(f"    状态码: {response.status}")
                    
                    if response.status == 200:
                        print(f"    ✅ 认证成功")
                        return auth
                    elif response.status == 401:
                        print(f"    ❌ 认证失败")
                    else:
                        error_text = await response.text()
                        print(f"    ⚠️ 其他错误: {error_text[:100]}")
                        
            except Exception as e:
                print(f"    ❌ 请求异常: {e}")
    
    return None

async def main():
    """主诊断函数"""
    print("🔧 API问题诊断开始")
    print("=" * 50)
    
    # 显示当前配置
    print(f"📋 当前配置:")
    print(f"  Base URL: {settings.claude_base_url}")
    print(f"  API Key: {settings.claude_api_key[:8]}...{settings.claude_api_key[-4:]}")
    print(f"  Model: {settings.claude_model}")
    print(f"  Use Mock: {settings.use_mock_api}")
    
    # 测试1: 基本连接
    connectivity_ok = await test_basic_connectivity()
    if not connectivity_ok:
        print("\n❌ 基本网络连接失败，请检查URL和网络")
        return
    
    # 测试2: API端点
    working_endpoint = await test_api_endpoints()
    if working_endpoint:
        print(f"\n✅ 找到工作的端点: {working_endpoint}")
    else:
        print(f"\n⚠️ 未找到工作的端点，继续测试其他方面")
    
    # 测试3: 请求格式
    working_format = await test_request_formats()
    if working_format:
        print(f"\n✅ 找到工作的请求格式: {working_format['name']}")
    else:
        print(f"\n⚠️ 未找到工作的请求格式")
    
    # 测试4: 认证方式
    working_auth = await test_authentication()
    if working_auth:
        print(f"\n✅ 找到工作的认证方式: {working_auth['name']}")
    else:
        print(f"\n❌ 未找到工作的认证方式")
    
    print("\n🎯 诊断总结:")
    if working_endpoint and working_format and working_auth:
        print("  ✅ API配置正确，应该可以正常工作")
        print(f"  📝 建议配置:")
        print(f"    端点: {working_endpoint}")
        print(f"    格式: {working_format['name']}")
        print(f"    认证: {working_auth['name']}")
    else:
        print("  ❌ 发现配置问题:")
        if not working_endpoint:
            print("    - API端点不正确")
        if not working_format:
            print("    - 请求格式不正确")
        if not working_auth:
            print("    - 认证方式不正确")

if __name__ == "__main__":
    asyncio.run(main())
