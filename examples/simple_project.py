#!/usr/bin/env python3
"""
简单项目开发示例

这个示例展示如何使用多Agent系统开发一个简单的Web应用项目。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import MultiAgentDevSystem


async def develop_todo_app():
    """开发一个简单的待办事项应用"""
    
    # 初始化系统
    system = MultiAgentDevSystem()
    await system.initialize()
    
    print("开始开发待办事项应用...")
    
    # 开发项目
    result = await system.develop_project(
        title="待办事项管理应用",
        description="""
        一个简单的待办事项管理Web应用，用户可以：
        1. 添加新的待办事项
        2. 标记事项为完成
        3. 删除不需要的事项
        4. 查看所有事项列表
        
        应用应该有简洁的用户界面，支持基本的CRUD操作。
        """,
        features=[
            "用户界面设计",
            "添加待办事项",
            "编辑待办事项", 
            "删除待办事项",
            "标记完成状态",
            "事项列表显示",
            "数据持久化"
        ],
        tech_stack=[
            "Python",
            "Flask",
            "SQLite",
            "HTML/CSS",
            "JavaScript"
        ],
        constraints={
            "complexity": "simple",
            "deployment": "single_file_if_possible",
            "database": "sqlite_file_based"
        }
    )
    
    print(f"\n项目开发完成！")
    print(f"项目ID: {result.project_id}")
    print(f"生成的文件数量: {len(result.final_code)}")
    
    # 显示生成的文件
    print("\n生成的文件:")
    for file_path in sorted(result.final_code.keys()):
        print(f"  - {file_path}")
    
    # 显示测试报告摘要
    if result.test_reports:
        print(f"\n测试报告数量: {len(result.test_reports)}")
        for i, report in enumerate(result.test_reports):
            test_files = report.get('test_files', {})
            print(f"  报告 {i+1}: {len(test_files)} 个测试文件")
    
    # 显示审查反馈摘要
    if result.review_feedback:
        print(f"\n代码审查反馈数量: {len(result.review_feedback)}")
        for i, feedback in enumerate(result.review_feedback):
            score = feedback.get('overall_score', 'N/A')
            status = feedback.get('approval_status', 'unknown')
            print(f"  审查 {i+1}: 评分 {score}/10, 状态: {status}")
    
    return result


async def develop_api_service():
    """开发一个简单的REST API服务"""
    
    # 初始化系统
    system = MultiAgentDevSystem()
    await system.initialize()
    
    print("开始开发REST API服务...")
    
    # 开发项目
    result = await system.develop_project(
        title="用户管理API服务",
        description="""
        一个简单的用户管理REST API服务，提供以下功能：
        1. 用户注册和登录
        2. 用户信息的CRUD操作
        3. JWT身份验证
        4. 输入验证和错误处理
        
        API应该遵循RESTful设计原则，返回JSON格式数据。
        """,
        features=[
            "用户注册接口",
            "用户登录接口",
            "获取用户信息",
            "更新用户信息",
            "删除用户",
            "JWT身份验证",
            "输入验证",
            "错误处理",
            "API文档"
        ],
        tech_stack=[
            "Python",
            "FastAPI",
            "SQLAlchemy",
            "PostgreSQL",
            "JWT",
            "Pydantic"
        ],
        constraints={
            "api_style": "RESTful",
            "authentication": "JWT",
            "documentation": "OpenAPI/Swagger",
            "validation": "strict"
        }
    )
    
    print(f"\nAPI服务开发完成！")
    print(f"项目ID: {result.project_id}")
    
    return result


async def main():
    """主函数"""
    print("多Agent项目开发示例")
    print("=" * 50)
    
    # 选择要运行的示例
    examples = {
        "1": ("待办事项应用", develop_todo_app),
        "2": ("REST API服务", develop_api_service)
    }
    
    print("可用示例:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")
    
    choice = input("\n请选择要运行的示例 (1-2): ").strip()
    
    if choice in examples:
        name, func = examples[choice]
        print(f"\n开始运行示例: {name}")
        print("-" * 30)
        
        try:
            result = await func()
            print(f"\n示例 '{name}' 运行完成！")
            
        except Exception as e:
            print(f"\n示例运行失败: {str(e)}")
            
    else:
        print("无效选择")


if __name__ == "__main__":
    asyncio.run(main())
