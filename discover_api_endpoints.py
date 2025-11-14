#!/usr/bin/env python3
"""
API端点发现脚本
尝试发现可用的API端点和正确的请求格式
"""

import asyncio
import aiohttp
import json
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from config import settings

async def discover_endpoints():
    """发现可用的API端点"""
    print("🔍 发现API端点...")
    
    base_url = settings.claude_base_url
    api_key = settings.claude_api_key
    
    # 可能的端点路径
    possible_endpoints = [
        # 标准端点
        "/v1/messages",
        "/api/v1/messages",
        "/v1/chat/completions",
        "/api/v1/chat/completions",
        "/v1/completions",
        "/api/v1/completions",
        
        # Claude特定端点
        "/claude/v1/messages",
        "/claude/api/v1/messages",
        "/anthropic/v1/messages",
        "/anthropic/api/v1/messages",
        
        # 其他可能的端点
        "/chat/completions",
        "/completions",
        "/generate",
        "/api/generate",
        "/v1/generate",
        "/api/v1/generate",
        
        # 代理服务端点
        "/proxy/v1/messages",
        "/proxy/api/v1/messages",
        "/relay/v1/messages",
        "/relay/api/v1/messages",
        
        # 特殊端点
        "/claude-code/v1/messages",
        "/claude-code/api/v1/messages",
        "/vscode/v1/messages",
        "/vscode/api/v1/messages"
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint in possible_endpoints:
            url = f"{base_url.rstrip('/')}{endpoint}"
            print(f"  🔍 测试: {endpoint}")
            
            try:
                # 先用OPTIONS请求测试
                async with session.options(url, timeout=5) as response:
                    print(f"    OPTIONS: {response.status}")
                    
                    if response.status in [200, 204, 405]:
                        print(f"    ✅ 端点可能存在")
                        
                        # 尝试GET请求
                        try:
                            async with session.get(url, timeout=5) as get_response:
                                print(f"    GET: {get_response.status}")
                                if get_response.status != 404:
                                    text = await get_response.text()
                                    print(f"    响应: {text[:100]}...")
                        except:
                            pass
                        
                        return endpoint
                    
            except Exception as e:
                print(f"    ❌ 失败: {str(e)}")
    
    return None

async def test_different_auth_methods():
    """测试不同的认证方法"""
    print("\n🔐 测试认证方法...")
    
    base_url = settings.claude_base_url
    api_key = settings.claude_api_key
    
    # 不同的认证方法
    auth_methods = [
        {
            "name": "Standard Bearer",
            "headers": {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        },
        {
            "name": "X-API-Key",
            "headers": {
                "x-api-key": api_key,
                "Content-Type": "application/json"
            }
        },
        {
            "name": "API-Key",
            "headers": {
                "api-key": api_key,
                "Content-Type": "application/json"
            }
        },
        {
            "name": "Claude-API-Key",
            "headers": {
                "claude-api-key": api_key,
                "Content-Type": "application/json"
            }
        },
        {
            "name": "Anthropic-API-Key",
            "headers": {
                "anthropic-api-key": api_key,
                "Content-Type": "application/json"
            }
        },
        {
            "name": "Bearer + X-API-Key",
            "headers": {
                "Authorization": f"Bearer {api_key}",
                "x-api-key": api_key,
                "Content-Type": "application/json"
            }
        }
    ]
    
    test_payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 10,
        "messages": [{"role": "user", "content": "test"}]
    }
    
    endpoint = "/api/v1/messages"  # 已知存在的端点
    url = f"{base_url.rstrip('/')}{endpoint}"
    
    async with aiohttp.ClientSession() as session:
        for auth in auth_methods:
            print(f"  🔐 测试: {auth['name']}")
            
            try:
                async with session.post(
                    url,
                    headers=auth['headers'],
                    json=test_payload,
                    timeout=10
                ) as response:
                    print(f"    状态码: {response.status}")
                    
                    if response.status == 200:
                        print(f"    ✅ 认证成功!")
                        result = await response.json()
                        print(f"    响应: {str(result)[:100]}...")
                        return auth
                    else:
                        error_text = await response.text()
                        print(f"    ❌ 失败: {error_text[:100]}")
                        
            except Exception as e:
                print(f"    ❌ 异常: {str(e)}")
    
    return None

async def test_different_user_agents():
    """测试不同的User-Agent"""
    print("\n🤖 测试User-Agent...")
    
    base_url = settings.claude_base_url
    api_key = settings.claude_api_key
    
    user_agents = [
        "Claude-Code/1.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Claude-Code/1.0.0 Chrome/120.0.0.0 Electron/28.0.0 Safari/537.36",
        "VSCode/1.85.0 Claude-Code/1.0.0",
        "Anthropic-Claude-Code/1.0.0",
        "Claude-Desktop/1.0.0",
        "Claude-API-Client/1.0.0",
        "curl/7.68.0",
        "PostmanRuntime/7.32.3",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    ]
    
    base_headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "x-api-key": api_key
    }
    
    test_payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 10,
        "messages": [{"role": "user", "content": "test"}]
    }
    
    endpoint = "/api/v1/messages"
    url = f"{base_url.rstrip('/')}{endpoint}"
    
    async with aiohttp.ClientSession() as session:
        for ua in user_agents:
            print(f"  🤖 测试: {ua}")
            
            headers = {**base_headers, "User-Agent": ua}
            
            try:
                async with session.post(
                    url,
                    headers=headers,
                    json=test_payload,
                    timeout=10
                ) as response:
                    print(f"    状态码: {response.status}")
                    
                    if response.status == 200:
                        print(f"    ✅ User-Agent有效!")
                        result = await response.json()
                        print(f"    响应: {str(result)[:100]}...")
                        return ua
                    else:
                        error_text = await response.text()
                        print(f"    ❌ 失败: {error_text[:50]}")
                        
            except Exception as e:
                print(f"    ❌ 异常: {str(e)}")
    
    return None

async def check_api_documentation():
    """检查API文档"""
    print("\n📚 检查API文档...")
    
    base_url = settings.claude_base_url
    
    doc_paths = [
        "/docs",
        "/api/docs",
        "/swagger",
        "/api/swagger",
        "/openapi.json",
        "/api/openapi.json",
        "/v1/docs",
        "/api/v1/docs",
        "/.well-known/openapi",
        "/health",
        "/status",
        "/info"
    ]
    
    async with aiohttp.ClientSession() as session:
        for path in doc_paths:
            url = f"{base_url.rstrip('/')}{path}"
            print(f"  📚 检查: {path}")
            
            try:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        print(f"    ✅ 找到文档: {url}")
                        content = await response.text()
                        print(f"    内容: {content[:200]}...")
                        return url
                    else:
                        print(f"    状态码: {response.status}")
                        
            except Exception as e:
                print(f"    ❌ 失败: {str(e)}")
    
    return None

async def main():
    """主函数"""
    print("🔍 API端点发现工具")
    print("=" * 50)
    
    print(f"📋 目标服务: {settings.claude_base_url}")
    print(f"🔑 API Key: {settings.claude_api_key[:8]}...{settings.claude_api_key[-4:]}")
    
    # 1. 发现端点
    endpoint = await discover_endpoints()
    if endpoint:
        print(f"\n✅ 发现可用端点: {endpoint}")
    else:
        print(f"\n⚠️ 未发现明显可用的端点")
    
    # 2. 测试认证方法
    auth_method = await test_different_auth_methods()
    if auth_method:
        print(f"\n✅ 发现有效认证: {auth_method['name']}")
    else:
        print(f"\n⚠️ 未发现有效认证方法")
    
    # 3. 测试User-Agent
    user_agent = await test_different_user_agents()
    if user_agent:
        print(f"\n✅ 发现有效User-Agent: {user_agent}")
    else:
        print(f"\n⚠️ 未发现有效User-Agent")
    
    # 4. 检查文档
    doc_url = await check_api_documentation()
    if doc_url:
        print(f"\n✅ 发现API文档: {doc_url}")
    else:
        print(f"\n⚠️ 未发现API文档")
    
    print(f"\n🎯 总结:")
    if not any([endpoint, auth_method, user_agent]):
        print("  ❌ 该API服务可能:")
        print("    1. 只支持特定的Claude Code客户端")
        print("    2. 需要特殊的认证或配置")
        print("    3. 使用了客户端指纹识别")
        print("    4. API密钥可能无效或过期")
        print("\n  💡 建议:")
        print("    1. 联系API服务提供商获取正确的接入方式")
        print("    2. 检查API密钥是否有效")
        print("    3. 确认服务是否支持第三方客户端")
    else:
        print("  ✅ 发现了一些可用的配置，请根据上述结果调整客户端")

if __name__ == "__main__":
    asyncio.run(main())
