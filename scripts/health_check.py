#!/usr/bin/env python3
"""
健康检查脚本
"""

import asyncio
import logging
import sys
from pathlib import Path
import aiohttp
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from multi_agent_dev.extensions.monitoring import metrics_collector
from config import settings


async def check_api_health():
    """检查API健康状态"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://localhost:{settings.metrics_port}/health', timeout=5) as response:
                if response.status == 200:
                    return True, "API健康检查通过"
                else:
                    return False, f"API返回状态码: {response.status}"
    except Exception as e:
        return False, f"API健康检查失败: {str(e)}"


async def check_metrics_collection():
    """检查指标收集"""
    try:
        stats = metrics_collector.get_summary_stats()
        if 'message' in stats and '暂无指标数据' in stats['message']:
            return True, "指标收集正常（暂无数据）"
        else:
            return True, f"指标收集正常，最近1小时有 {stats.get('time_range', {}).get('last_hour', 0)} 条记录"
    except Exception as e:
        return False, f"指标收集检查失败: {str(e)}"


async def check_file_permissions():
    """检查文件权限"""
    try:
        # 检查结果目录
        results_dir = Path(settings.results_dir)
        if not results_dir.exists():
            results_dir.mkdir(parents=True, exist_ok=True)
        
        # 测试写入权限
        test_file = results_dir / "health_check_test.txt"
        test_file.write_text("health check test")
        test_file.unlink()
        
        # 检查日志目录
        logs_dir = Path(settings.logs_dir)
        if not logs_dir.exists():
            logs_dir.mkdir(parents=True, exist_ok=True)
        
        return True, "文件权限检查通过"
    except Exception as e:
        return False, f"文件权限检查失败: {str(e)}"


async def check_claude_api_key():
    """检查Claude API密钥配置"""
    try:
        if not settings.claude_api_key:
            return False, "Claude API密钥未配置"
        
        if settings.claude_api_key == "your_claude_api_key_here":
            return False, "Claude API密钥未设置为有效值"
        
        # 这里不实际调用API，只检查配置
        return True, "Claude API密钥配置正常"
    except Exception as e:
        return False, f"Claude API密钥检查失败: {str(e)}"


async def main():
    """主健康检查函数"""
    print(f"开始健康检查 - {datetime.now().isoformat()}")
    print("=" * 50)
    
    checks = [
        ("API健康状态", check_api_health),
        ("指标收集", check_metrics_collection),
        ("文件权限", check_file_permissions),
        ("Claude API配置", check_claude_api_key),
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            passed, message = await check_func()
            status = "✓ 通过" if passed else "✗ 失败"
            print(f"{check_name}: {status} - {message}")
            
            if not passed:
                all_passed = False
                
        except Exception as e:
            print(f"{check_name}: ✗ 异常 - {str(e)}")
            all_passed = False
    
    print("=" * 50)
    
    if all_passed:
        print("✓ 所有健康检查通过")
        sys.exit(0)
    else:
        print("✗ 部分健康检查失败")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
