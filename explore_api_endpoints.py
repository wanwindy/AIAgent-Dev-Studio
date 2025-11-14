#!/usr/bin/env python3
"""
探索API服务的正确端点
"""

import asyncio
import aiohttp
import json
from config import settings

async def explore_api_structure():
    """探索API结构"""
    print("🔍 探索API服务结构...")
    
    base_url = settings.claude_base_url.rstrip('/')
    api_key = settings.claude_api_key
    
    # 可能的端点路径
    potential_endpoints = [
        # 标准路径
        "/v1/messages",
        "/api/v1/messages", 
        "/v1/chat/completions",
        "/api/v1/chat/completions",
        
        # Claude相关路径
        "/claude/v1/messages",
        "/claude/messages",
        "/anthropic/v1/messages",
        "/anthropic/messages",
        
        # 通用AI路径
        "/ai/v1/messages",
        "/ai/messages",
        "/llm/v1/messages",
        "/llm/messages",
        
        # 其他可能的路径
        "/chat",
        "/message",
        "/generate",
        "/completion",
        "/api/chat",
        "/api/message",
        "/api/generate",
        "/api/completion",
        
        # 版本化路径
        "/v2/messages",
        "/v3/messages",
        "/latest/messages",
        
        # 服务特定路径
        "/relay/v1/messages",
        "/proxy/v1/messages",
        "/gateway/v1/messages"
    ]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    
    # 简单的测试负载
    test_payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 10,
        "messages": [{"role": "user", "content": "test"}]
    }
    
    working_endpoints = []
    
    async with aiohttp.ClientSession() as session:
        for endpoint in potential_endpoints:
            url = f"{base_url}{endpoint}"
            print(f"  🔗 测试: {endpoint}")
            
            try:
                # 先用OPTIONS请求测试
                async with session.options(url, headers=headers, timeout=10) as response:
                    if response.status in [200, 405]:  # 405表示方法不允许但端点存在
                        print(f"    OPTIONS: {response.status} - 端点可能存在")
                        
                        # 尝试POST请求
                        try:
                            async with session.post(url, headers=headers, json=test_payload, timeout=15) as post_response:
                                print(f"    POST: {post_response.status}")
                                
                                if post_response.status == 200:
                                    result = await post_response.json()
                                    print(f"    ✅ 成功! 响应: {json.dumps(result, indent=2, ensure_ascii=False)[:200]}...")
                                    working_endpoints.append((endpoint, "success", result))
                                elif post_response.status in [400, 401, 403]:
                                    # 这些状态码表示端点存在但请求有问题
                                    error_text = await post_response.text()
                                    print(f"    ⚠️ 端点存在但请求有问题: {error_text[:100]}")
                                    working_endpoints.append((endpoint, "exists_but_error", error_text))
                                else:
                                    error_text = await post_response.text()
                                    print(f"    ❌ 失败: {error_text[:100]}")
                        except Exception as e:
                            print(f"    ❌ POST异常: {e}")
                    else:
                        print(f"    OPTIONS: {response.status} - 端点不存在")
                        
            except Exception as e:
                print(f"    ❌ 异常: {e}")
    
    return working_endpoints

async def check_api_documentation():
    """检查API文档或帮助信息"""
    print("\n📚 查找API文档...")
    
    base_url = settings.claude_base_url.rstrip('/')
    
    # 可能包含文档的路径
    doc_paths = [
        "/docs",
        "/api/docs", 
        "/swagger",
        "/openapi",
        "/help",
        "/info",
        "/status",
        "/health",
        "/version",
        "/api",
        "/api/v1",
        "/.well-known/openapi"
    ]
    
    async with aiohttp.ClientSession() as session:
        for path in doc_paths:
            url = f"{base_url}{path}"
            print(f"  🔗 检查: {path}")
            
            try:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        text = await response.text()
                        
                        print(f"    ✅ 找到内容 ({content_type})")
                        
                        if 'json' in content_type:
                            try:
                                data = json.loads(text)
                                print(f"    JSON: {json.dumps(data, indent=2, ensure_ascii=False)[:300]}...")
                            except:
                                print(f"    文本: {text[:200]}...")
                        else:
                            print(f"    文本: {text[:200]}...")
                            
                        # 查找可能的端点信息
                        if any(keyword in text.lower() for keyword in ['endpoint', 'api', 'route', 'path']):
                            print(f"    💡 可能包含端点信息!")
                            
            except Exception as e:
                print(f"    ❌ 异常: {e}")

async def test_different_auth_methods():
    """测试不同的认证方法"""
    print("\n🔐 测试不同的认证方法...")
    
    base_url = settings.claude_base_url.rstrip('/')
    api_key = settings.claude_api_key
    
    # 尝试一个可能存在的端点
    test_url = f"{base_url}/api/v1/messages"
    
    auth_methods = [
        {
            "name": "Bearer Token",
            "headers": {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        },
        {
            "name": "X-API-Key",
            "headers": {"X-API-Key": api_key, "Content-Type": "application/json"}
        },
        {
            "name": "API-Key",
            "headers": {"API-Key": api_key, "Content-Type": "application/json"}
        },
        {
            "name": "Authorization Key",
            "headers": {"Authorization": f"Key {api_key}", "Content-Type": "application/json"}
        },
        {
            "name": "Custom Header",
            "headers": {"x-api-key": api_key, "Content-Type": "application/json"}
        }
    ]
    
    test_payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 10,
        "messages": [{"role": "user", "content": "test"}]
    }
    
    async with aiohttp.ClientSession() as session:
        for auth in auth_methods:
            print(f"  🔑 测试: {auth['name']}")
            
            try:
                async with session.post(test_url, headers=auth['headers'], json=test_payload, timeout=15) as response:
                    print(f"    状态码: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print(f"    ✅ 认证成功! 响应: {json.dumps(result, indent=2, ensure_ascii=False)[:200]}...")
                        return auth
                    else:
                        error_text = await response.text()
                        print(f"    ❌ 失败: {error_text[:100]}")
                        
            except Exception as e:
                print(f"    ❌ 异常: {e}")
    
    return None

async def main():
    """主探索函数"""
    print("🕵️ API端点探索开始")
    print("=" * 50)
    
    # 1. 探索API结构
    working_endpoints = await explore_api_structure()
    
    if working_endpoints:
        print(f"\n✅ 找到可用端点:")
        for endpoint, status, info in working_endpoints:
            print(f"  - {endpoint}: {status}")
    else:
        print(f"\n⚠️ 未找到标准端点，继续探索...")
    
    # 2. 查找文档
    await check_api_documentation()
    
    # 3. 测试认证方法
    working_auth = await test_different_auth_methods()
    
    if working_auth:
        print(f"\n✅ 找到工作的认证方法: {working_auth['name']}")
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 探索结果总结:")
    print(f"  可用端点数量: {len(working_endpoints)}")
    print(f"  认证方法: {'找到' if working_auth else '未找到'}")
    
    if working_endpoints or working_auth:
        print("\n💡 建议:")
        if working_endpoints:
            for endpoint, status, _ in working_endpoints:
                if status == "success":
                    print(f"  - 使用端点: {endpoint}")
        if working_auth:
            print(f"  - 使用认证: {working_auth['name']}")

if __name__ == "__main__":
    asyncio.run(main())
