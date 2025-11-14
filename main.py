"""
多Agent自动化项目开发系统主程序
"""

import asyncio
import logging
import sys
import argparse
from pathlib import Path
from typing import Optional
import threading
import json
from aiohttp import web

from multi_agent_dev import AgentManager, WorkflowEngine, ClaudeAPIClient
from multi_agent_dev.core.task_queue import TaskQueue
from multi_agent_dev.core.result_store import ResultStore
from multi_agent_dev.models.task import ProjectRequirements
from multi_agent_dev.extensions.git_integration import GitIntegration
from multi_agent_dev.extensions.ci_integration import CIIntegration
from multi_agent_dev.extensions.monitoring import metrics_collector
from config import settings


# 配置日志
def setup_logging():
    """配置日志系统"""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # 创建日志目录
    log_dir = Path(settings.logs_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 配置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 文件处理器
    file_handler = logging.FileHandler(
        log_dir / 'multi_agent_dev.log',
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # 设置第三方库日志级别
    logging.getLogger('anthropic').setLevel(logging.WARNING)
    logging.getLogger('git').setLevel(logging.WARNING)


class MultiAgentDevSystem:
    """多Agent开发系统主类"""
    
    def __init__(self):
        """初始化系统"""
        self.api_client = None
        self.agent_manager = None
        self.workflow_engine = None
        self.task_queue = None
        self.result_store = None
        self.git_integration = None
        self.ci_integration = None
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self):
        """初始化系统组件"""
        try:
            self.logger.info("正在初始化多Agent开发系统...")
            
            # 初始化API客户端
            self.api_client = ClaudeAPIClient()
            self.logger.info("Claude API客户端已初始化")
            
            # 初始化核心组件
            self.task_queue = TaskQueue()
            self.result_store = ResultStore()
            self.agent_manager = AgentManager(self.api_client)
            self.workflow_engine = WorkflowEngine(
                self.agent_manager,
                self.task_queue,
                self.result_store
            )
            
            # 初始化扩展功能
            if settings.git_enabled:
                self.git_integration = GitIntegration()
                self.logger.info("Git集成已启用")
            
            self.ci_integration = CIIntegration()
            
            self.logger.info("系统初始化完成")
            
        except Exception as e:
            self.logger.error(f"系统初始化失败: {str(e)}")
            raise
    
    async def develop_project(
        self,
        title: str,
        description: str,
        features: Optional[list] = None,
        tech_stack: Optional[list] = None,
        constraints: Optional[dict] = None
    ):
        """
        开发项目
        
        Args:
            title: 项目标题
            description: 项目描述
            features: 功能列表
            tech_stack: 技术栈
            constraints: 约束条件
        """
        try:
            self.logger.info(f"开始开发项目: {title}")
            
            # 创建项目需求
            requirements = ProjectRequirements(
                title=title,
                description=description,
                features=features or [],
                tech_stack=tech_stack,
                constraints=constraints or {}
            )
            
            # 执行开发工作流
            result = await self.workflow_engine.execute_development_workflow(requirements)
            
            # Git集成：保存代码到仓库
            if self.git_integration and self.git_integration.is_enabled():
                self.logger.info("保存代码到Git仓库...")
                
                # 创建功能分支
                branch_name = f"feature/{title.lower().replace(' ', '-')}"
                self.git_integration.create_feature_branch(branch_name)
                
                # 保存生成的代码
                if result.final_code:
                    self.git_integration.save_generated_code(
                        result.final_code,
                        result.project_id
                    )
                
                # 提交更改
                commit_message = f"Add generated project: {title}"
                self.git_integration.commit_changes(commit_message)
                
                # 创建PR信息
                pr_info = self.git_integration.create_pull_request_info(
                    f"Add {title}",
                    f"Auto-generated project: {description}"
                )
                
                self.logger.info(f"代码已保存到分支: {branch_name}")
                if pr_info:
                    self.logger.info(f"PR信息已生成，包含 {len(pr_info.get('commits', []))} 个提交")
            
            # CI/CD集成：运行测试和构建
            if result.final_code:
                self.logger.info("运行CI/CD流水线...")
                
                # 将代码保存到临时目录进行测试
                temp_dir = Path("temp_projects") / result.project_id
                temp_dir.mkdir(parents=True, exist_ok=True)
                
                for file_path, content in result.final_code.items():
                    full_path = temp_dir / file_path.lstrip('/')
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                
                # 运行CI/CD流水线
                ci_integration = CIIntegration(str(temp_dir))
                pipeline_result = await ci_integration.run_full_pipeline()
                
                self.logger.info(f"CI/CD流水线完成，状态: {'成功' if pipeline_result['success'] else '失败'}")
                
                # 清理临时目录
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            
            # 输出结果摘要
            self._print_project_summary(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"项目开发失败: {str(e)}")
            raise
    
    def _print_project_summary(self, result):
        """打印项目摘要"""
        print("\n" + "="*60)
        print(f"项目开发完成: {result.requirements.title}")
        print("="*60)
        
        print(f"项目ID: {result.project_id}")
        print(f"状态: {result.status.value}")
        print(f"执行时间: {result.total_execution_time:.2f}秒")
        print(f"使用Token: {result.total_tokens_used}")
        
        print(f"\n生成的文件数量: {len(result.final_code)}")
        for file_path in result.final_code.keys():
            print(f"  - {file_path}")
        
        print(f"\n测试报告数量: {len(result.test_reports)}")
        print(f"审查反馈数量: {len(result.review_feedback)}")
        
        # Agent执行统计
        agent_stats = {}
        for agent_result in result.agent_results:
            agent_type = agent_result.agent_type.value
            if agent_type not in agent_stats:
                agent_stats[agent_type] = {'success': 0, 'failure': 0}
            
            if agent_result.success:
                agent_stats[agent_type]['success'] += 1
            else:
                agent_stats[agent_type]['failure'] += 1
        
        print("\nAgent执行统计:")
        for agent_type, stats in agent_stats.items():
            total = stats['success'] + stats['failure']
            success_rate = stats['success'] / total if total > 0 else 0
            print(f"  {agent_type}: {stats['success']}/{total} 成功 ({success_rate:.1%})")
        
        print("="*60)
    
    async def get_system_status(self):
        """获取系统状态"""
        status = {
            'system': 'Multi-Agent Development System',
            'version': '1.0.0',
            'status': 'running' if self.workflow_engine else 'not_initialized'
        }
        
        if self.workflow_engine:
            workflow_status = await self.workflow_engine.get_workflow_status()
            status.update(workflow_status)
        
        if self.git_integration:
            status['git'] = self.git_integration.get_branch_info()
        
        # 添加指标统计
        status['metrics'] = metrics_collector.get_summary_stats()
        
        return status


async def health_check_handler(request):
    """健康检查处理器"""
    try:
        # 简单的健康检查
        status = {
            'status': 'healthy',
            'timestamp': asyncio.get_event_loop().time(),
            'version': '1.0.0'
        }

        # 检查系统组件
        system = request.app.get('system')
        if system and system.workflow_engine:
            status['components'] = {
                'workflow_engine': 'running',
                'api_client': 'connected' if system.api_client else 'disconnected'
            }

        return web.json_response(status)
    except Exception as e:
        return web.json_response(
            {'status': 'unhealthy', 'error': str(e)},
            status=500
        )


async def metrics_handler(request):
    """指标处理器"""
    try:
        stats = metrics_collector.get_summary_stats()
        return web.json_response(stats)
    except Exception as e:
        return web.json_response(
            {'error': str(e)},
            status=500
        )


async def start_http_server(system: MultiAgentDevSystem):
    """启动HTTP服务器"""
    app = web.Application()
    app['system'] = system

    # 添加路由
    app.router.add_get('/health', health_check_handler)
    app.router.add_get('/metrics', metrics_handler)

    # 启动服务器
    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, '0.0.0.0', settings.metrics_port)
    await site.start()

    logging.getLogger(__name__).info(f"HTTP服务器已启动，端口: {settings.metrics_port}")
    return runner


async def main():
    """主函数"""
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='多Agent自动化项目开发系统')
    parser.add_argument('--title', required=True, help='项目标题')
    parser.add_argument('--description', required=True, help='项目描述')
    parser.add_argument('--features', nargs='*', help='功能列表')
    parser.add_argument('--tech-stack', nargs='*', help='技术栈')
    parser.add_argument('--interactive', action='store_true', help='交互式模式')
    
    args = parser.parse_args()
    
    try:
        # 初始化系统
        system = MultiAgentDevSystem()
        await system.initialize()

        # 启动HTTP服务器（用于健康检查和指标）
        http_runner = None
        if settings.metrics_enabled:
            http_runner = await start_http_server(system)

        try:
            if args.interactive:
                # 交互式模式
                await interactive_mode(system)
            else:
                # 命令行模式
                await system.develop_project(
                    title=args.title,
                    description=args.description,
                    features=args.features,
                    tech_stack=args.tech_stack
                )
        finally:
            # 清理HTTP服务器
            if http_runner:
                await http_runner.cleanup()
        
    except KeyboardInterrupt:
        logger.info("用户中断程序")
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")
        sys.exit(1)


async def interactive_mode(system: MultiAgentDevSystem):
    """交互式模式"""
    print("欢迎使用多Agent自动化项目开发系统!")
    print("输入 'help' 查看可用命令，输入 'quit' 退出")
    
    while True:
        try:
            command = input("\n> ").strip()
            
            if command.lower() in ['quit', 'exit']:
                break
            elif command.lower() == 'help':
                print_help()
            elif command.lower() == 'status':
                status = await system.get_system_status()
                print(f"系统状态: {status}")
            elif command.lower().startswith('develop'):
                await handle_develop_command(system, command)
            else:
                print("未知命令，输入 'help' 查看可用命令")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"命令执行失败: {str(e)}")


def print_help():
    """打印帮助信息"""
    print("""
可用命令:
  help                    - 显示此帮助信息
  status                  - 显示系统状态
  develop <title>         - 开发项目（会提示输入详细信息）
  quit/exit              - 退出程序
    """)


async def handle_develop_command(system: MultiAgentDevSystem, command: str):
    """处理开发命令"""
    parts = command.split(maxsplit=1)
    if len(parts) < 2:
        print("请提供项目标题")
        return
    
    title = parts[1]
    
    # 交互式收集项目信息
    description = input("项目描述: ").strip()
    
    features_input = input("功能列表 (用逗号分隔): ").strip()
    features = [f.strip() for f in features_input.split(',')] if features_input else []
    
    tech_stack_input = input("技术栈 (用逗号分隔): ").strip()
    tech_stack = [t.strip() for t in tech_stack_input.split(',')] if tech_stack_input else None
    
    print(f"\n开始开发项目: {title}")
    await system.develop_project(
        title=title,
        description=description,
        features=features,
        tech_stack=tech_stack
    )


if __name__ == "__main__":
    asyncio.run(main())
