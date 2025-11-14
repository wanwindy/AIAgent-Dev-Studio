"""
交互式脚本：帮助用户选择并配置多 Agent 系统的 API 服务。
"""

from __future__ import annotations

import asyncio
import os


def show_api_options():
    """展示可选的 API 服务模式。"""
    print("🤖 AI API 服务选择")
    print("=" * 48)
    print("1) 模拟 API（推荐开发调试）")
    print("   - 无需密钥，响应迅速，覆盖全部流程")
    print("2) OpenAI API")
    print("   - 官方服务稳定，需要 API Key，可自定义 Base URL")
    print("3) Claude API (Anthropic)")
    print("   - 官方模型能力强，需要 API Key，可能受地区限制")
    print("4) 其他代理服务")
    print("   - 需要手动填写 .env，脚本仅提供提示\n")


def configure_mock_api():
    """写入模拟 API 配置。"""
    print("🔧 正在生成模拟 API 配置 ...")
    env_content = """# AI API 配置 - Mock 模式
USE_MOCK_API=true
CLAUDE_API_KEY=mock-api-key
CLAUDE_BASE_URL=mock://localhost
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CLAUDE_MAX_TOKENS=4000
CLAUDE_TIMEOUT=60

LOG_LEVEL=INFO
MAX_CONCURRENT_TASKS=5
TASK_TIMEOUT=300
MAX_RETRIES=3
RETRY_DELAY=1.0

RESULTS_DIR=./results
LOGS_DIR=./logs
GIT_ENABLED=false
METRICS_ENABLED=true
METRICS_PORT=8000
"""
    with open(".env", "w", encoding="utf-8") as fp:
        fp.write(env_content)
    print("✅ 模拟 API 配置完成，可直接运行 pytest 或 run_example.py\n")


def configure_openai_api() -> bool:
    """根据输入生成 OpenAI 配置。"""
    print("🔧 设置 OpenAI API")
    api_key = input("请输入 OpenAI API Key: ").strip()
    if not api_key:
        print("⚠️ API Key 不能为空\n")
        return False

    base_url = input("API Base URL (默认 https://api.openai.com): ").strip() or "https://api.openai.com"
    model = input("模型名称 (默认 gpt-3.5-turbo): ").strip() or "gpt-3.5-turbo"

    env_content = f"""# AI API 配置 - OpenAI 模式
USE_MOCK_API=false
OPENAI_API_KEY={api_key}
OPENAI_BASE_URL={base_url}
OPENAI_MODEL={model}
OPENAI_MAX_TOKENS=4000
OPENAI_TIMEOUT=60

LOG_LEVEL=INFO
MAX_CONCURRENT_TASKS=5
TASK_TIMEOUT=300
MAX_RETRIES=3
RETRY_DELAY=1.0

RESULTS_DIR=./results
LOGS_DIR=./logs
GIT_ENABLED=false
METRICS_ENABLED=true
METRICS_PORT=8000
"""
    with open(".env", "w", encoding="utf-8") as fp:
        fp.write(env_content)
    print("✅ OpenAI 配置已写入 .env\n")
    return True


def configure_claude_api() -> bool:
    """根据输入生成 Claude 配置。"""
    print("🔧 设置 Claude API")
    api_key = input("请输入 Claude API Key: ").strip()
    if not api_key:
        print("⚠️ API Key 不能为空\n")
        return False

    base_url = input("API Base URL (默认 https://api.anthropic.com): ").strip() or "https://api.anthropic.com"
    model = input("模型名称 (默认 claude-3-5-sonnet-20241022): ").strip() or "claude-3-5-sonnet-20241022"

    env_content = f"""# AI API 配置 - Claude 模式
USE_MOCK_API=false
CLAUDE_API_KEY={api_key}
CLAUDE_BASE_URL={base_url}
CLAUDE_MODEL={model}
CLAUDE_MAX_TOKENS=4000
CLAUDE_TIMEOUT=60

LOG_LEVEL=INFO
MAX_CONCURRENT_TASKS=5
TASK_TIMEOUT=300
MAX_RETRIES=3
RETRY_DELAY=1.0

RESULTS_DIR=./results
LOGS_DIR=./logs
GIT_ENABLED=false
METRICS_ENABLED=true
METRICS_PORT=8000
"""
    with open(".env", "w", encoding="utf-8") as fp:
        fp.write(env_content)
    print("✅ Claude 配置已写入 .env\n")
    return True


async def test_api_connection() -> bool:
    """简单检测当前配置是否可用。"""
    print("\n🧪 校验当前配置 ...")
    try:
        import importlib
        import config

        importlib.reload(config)
        if getattr(config.settings, "use_mock_api", False):
            print("✅ 模拟 API 配置就绪")
        else:
            print("ℹ️ 已启用真实 API，建议继续运行 `python scripts/health_check.py` 验证连接")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"❌ 检测失败：{exc}")
        return False


def main():
    """脚本入口。"""
    print("🚀 多 Agent 系统 · API 服务配置\n")

    if os.path.exists(".env"):
        choice = input("检测到现有 .env，是否覆盖? (y/N): ").strip().lower()
        if choice not in {"y", "yes"}:
            print("保持原配置，退出。")
            return

    show_api_options()

    while True:
        selection = input("请选择服务 (1-4): ").strip()
        if selection == "1":
            configure_mock_api()
            break
        if selection == "2" and configure_openai_api():
            break
        if selection == "3" and configure_claude_api():
            break
        if selection == "4":
            print("请手动编辑 .env，填入代理服务的地址与密钥。")
            break
        print("⚠️ 无效输入，请重新选择。")

    print("\n🎯 下一步建议")
    print("1. 运行 `pytest tests -q` 做快速验证")
    print("2. 运行 `python run_example.py` 体验完整流程")
    print("3. 阅读 docs/PROJECT_SUMMARY.md 了解系统能力\n")

    should_test = input("是否立即检测配置? (Y/n): ").strip().lower()
    if should_test not in {"n", "no"}:
        asyncio.run(test_api_connection())


if __name__ == "__main__":
    main()
