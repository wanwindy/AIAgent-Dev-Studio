#!/usr/bin/env python3
"""
快速运行示例脚本

这个脚本提供了一个简单的方式来测试多Agent开发系统。
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from main import MultiAgentDevSystem


async def run_simple_example():
    """运行一个简单的示例项目"""
    
    print("🚀 多Agent自动化项目开发系统 - 快速示例")
    print("=" * 60)
    
    # 检查API密钥
    if not os.getenv('CLAUDE_API_KEY'):
        print("❌ 错误: 请设置CLAUDE_API_KEY环境变量")
        print("   export CLAUDE_API_KEY='your-api-key-here'")
        return
    
    try:
        # 初始化系统
        print("🔧 正在初始化系统...")
        system = MultiAgentDevSystem()
        await system.initialize()
        print("✅ 系统初始化完成")
        
        # 开发一个简单的计算器项目
        print("\n📝 开始开发示例项目: 简单计算器")
        
        result = await system.develop_project(
            title="简单计算器",
            description="""
            开发一个简单的命令行计算器程序，支持基本的数学运算。
            
            功能要求：
            1. 支持加法、减法、乘法、除法运算
            2. 支持括号运算
            3. 错误处理（如除零错误）
            4. 用户友好的界面
            5. 输入验证
            
            技术要求：
            - 使用Python编写
            - 代码结构清晰
            - 包含单元测试
            - 有详细的文档说明
            """,
            features=[
                "基本四则运算",
                "括号支持",
                "错误处理",
                "用户界面",
                "输入验证",
                "单元测试"
            ],
            tech_stack=[
                "Python",
                "argparse",
                "unittest"
            ],
            constraints={
                "complexity": "simple",
                "target_audience": "beginner",
                "code_style": "clean_and_documented"
            }
        )
        
        print("\n🎉 项目开发完成!")
        print(f"📁 项目ID: {result.project_id}")
        print(f"📊 生成文件数: {len(result.final_code)}")
        print(f"⏱️  执行时间: {result.total_execution_time:.2f}秒")
        
        # 显示生成的文件
        print("\n📄 生成的文件:")
        for file_path in sorted(result.final_code.keys()):
            print(f"   📝 {file_path}")
        
        # 保存文件到本地
        output_dir = Path("generated_projects") / result.project_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for file_path, content in result.final_code.items():
            full_path = output_dir / file_path.lstrip('/')
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        print(f"\n💾 文件已保存到: {output_dir}")
        print("\n🔍 您可以查看生成的代码并运行测试:")
        print(f"   cd {output_dir}")
        print("   python main.py  # 运行计算器")
        print("   python -m unittest  # 运行测试")
        
        return result
        
    except Exception as e:
        print(f"\n❌ 示例运行失败: {str(e)}")
        print("\n🔧 故障排除建议:")
        print("1. 检查网络连接")
        print("2. 验证Claude API密钥是否有效")
        print("3. 确认API配额是否充足")
        print("4. 查看日志文件获取详细错误信息")
        raise


async def run_interactive_demo():
    """运行交互式演示"""
    
    print("🎮 交互式演示模式")
    print("=" * 40)
    
    # 预定义的项目示例
    examples = {
        "1": {
            "title": "待办事项应用",
            "description": "一个简单的待办事项管理Web应用，支持添加、编辑、删除和标记完成任务。",
            "features": ["任务管理", "Web界面", "数据持久化"],
            "tech_stack": ["Python", "Flask", "SQLite", "HTML/CSS"]
        },
        "2": {
            "title": "天气查询API",
            "description": "一个RESTful API服务，提供天气信息查询功能。",
            "features": ["REST API", "天气数据", "JSON响应", "错误处理"],
            "tech_stack": ["Python", "FastAPI", "requests", "JSON"]
        },
        "3": {
            "title": "文件管理工具",
            "description": "一个命令行文件管理工具，支持文件搜索、复制、移动等操作。",
            "features": ["文件操作", "搜索功能", "命令行界面"],
            "tech_stack": ["Python", "argparse", "pathlib", "shutil"]
        }
    }
    
    print("选择一个示例项目:")
    for key, example in examples.items():
        print(f"  {key}. {example['title']}")
    print("  4. 自定义项目")
    
    choice = input("\n请选择 (1-4): ").strip()
    
    if choice in examples:
        example = examples[choice]
        print(f"\n选择了: {example['title']}")
        
        # 初始化系统
        system = MultiAgentDevSystem()
        await system.initialize()
        
        # 开发项目
        await system.develop_project(**example)
        
    elif choice == "4":
        # 自定义项目
        title = input("项目标题: ").strip()
        description = input("项目描述: ").strip()
        
        features_input = input("功能列表 (用逗号分隔): ").strip()
        features = [f.strip() for f in features_input.split(',')] if features_input else []
        
        tech_stack_input = input("技术栈 (用逗号分隔): ").strip()
        tech_stack = [t.strip() for t in tech_stack_input.split(',')] if tech_stack_input else []
        
        # 初始化系统
        system = MultiAgentDevSystem()
        await system.initialize()
        
        # 开发项目
        await system.develop_project(
            title=title,
            description=description,
            features=features,
            tech_stack=tech_stack
        )
    else:
        print("无效选择")


async def main():
    """主函数"""
    print("🤖 多Agent自动化项目开发系统")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        await run_interactive_demo()
    else:
        await run_simple_example()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，程序退出")
    except Exception as e:
        print(f"\n❌ 程序执行失败: {str(e)}")
        sys.exit(1)
