"""
任务和数据模型定义
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """任务优先级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentType(str, Enum):
    """Agent类型枚举"""
    MASTER = "master"                    # 主Agent
    PROJECT_MANAGER = "project_manager"  # 项目经理
    ARCHITECT = "architect"              # 架构师
    DEVELOPER = "developer"              # 开发者
    TESTER = "tester"                   # 测试员
    REVIEWER = "reviewer"               # 审查员

    # 新增专业子Agent
    FRONTEND = "frontend"               # 前端开发Agent
    BACKEND = "backend"                 # 后端开发Agent
    UI_DESIGN = "ui_design"            # UI设计Agent
    DATABASE_DESIGN = "database_design" # 数据库设计Agent
    DOCUMENTATION = "documentation"     # 文档生成Agent
    DEPLOYMENT = "deployment"          # 部署Agent


class Task(BaseModel):
    """任务模型"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    assigned_agent: Optional[AgentType] = None
    dependencies: List[str] = Field(default_factory=list)
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


class ProjectRequirements(BaseModel):
    """项目需求模型"""
    title: str
    description: str
    features: List[str] = Field(default_factory=list)
    tech_stack: Optional[List[str]] = None
    constraints: Dict[str, Any] = Field(default_factory=dict)
    timeline: Optional[str] = None
    budget: Optional[float] = None


class AgentResult(BaseModel):
    """Agent执行结果模型"""
    agent_type: AgentType
    task_id: str
    success: bool
    output: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    execution_time: float = 0.0
    tokens_used: int = 0
    timestamp: datetime = Field(default_factory=datetime.now)


class ProjectResult(BaseModel):
    """项目开发结果模型"""
    project_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    requirements: ProjectRequirements
    tasks: List[Task] = Field(default_factory=list)
    agent_results: List[AgentResult] = Field(default_factory=list)
    final_code: Dict[str, str] = Field(default_factory=dict)
    test_reports: List[Dict[str, Any]] = Field(default_factory=list)
    review_feedback: List[Dict[str, Any]] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    total_execution_time: float = 0.0
    total_tokens_used: int = 0
