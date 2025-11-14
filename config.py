"""
系统配置管理
"""

import os
from typing import Optional

try:
    from pydantic_settings import BaseSettings
    from pydantic import Field
except ImportError:
    from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """系统配置类"""
    
    # Claude API配置
    claude_api_key: str = Field(
        "", env="CLAUDE_API_KEY"
    )
    claude_base_url: str = Field(
        "https://cc.zwchat.cn", env="CLAUDE_BASE_URL"
    )
    # 模型名称，如果不指定则让API服务自动选择
    claude_model: str = Field(
        "claude-3-5-sonnet-20241022", env="CLAUDE_MODEL"
    )
    claude_max_tokens: int = Field(4000, env="CLAUDE_MAX_TOKENS")
    claude_timeout: int = Field(60, env="CLAUDE_TIMEOUT")
    
    # 系统配置
    log_level: str = Field("INFO", env="LOG_LEVEL")
    max_concurrent_tasks: int = Field(5, env="MAX_CONCURRENT_TASKS")
    task_timeout: int = Field(300, env="TASK_TIMEOUT")
    
    # 重试配置
    max_retries: int = Field(3, env="MAX_RETRIES")
    retry_delay: float = Field(1.0, env="RETRY_DELAY")
    
    # 存储配置
    results_dir: str = Field("./results", env="RESULTS_DIR")
    logs_dir: str = Field("./logs", env="LOGS_DIR")
    
    # Git配置
    git_enabled: bool = Field(False, env="GIT_ENABLED")
    git_repo_path: Optional[str] = Field(None, env="GIT_REPO_PATH")
    
    # 监控配置
    metrics_enabled: bool = Field(True, env="METRICS_ENABLED")
    metrics_port: int = Field(8000, env="METRICS_PORT")

    # API模式配置
    use_mock_api: bool = Field(False, env="USE_MOCK_API")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
