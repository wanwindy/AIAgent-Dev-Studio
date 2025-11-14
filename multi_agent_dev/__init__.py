"""
多Agent自动化项目开发系统。
"""

from typing import TYPE_CHECKING

__version__ = "1.0.0"
__author__ = "Multi-Agent Dev System"

__all__ = [
    "AgentManager",
    "WorkflowEngine",
    "ClaudeAPIClient",
    "MockClaudeAPIClient",
    "BaseAgent",
]


def __getattr__(name: str):
    if name == "AgentManager":
        from .core.agent_manager import AgentManager as _AgentManager

        return _AgentManager
    if name == "WorkflowEngine":
        from .core.workflow_engine import WorkflowEngine as _WorkflowEngine

        return _WorkflowEngine
    if name == "ClaudeAPIClient":
        from .api.claude_client import ClaudeAPIClient as _ClaudeAPIClient

        return _ClaudeAPIClient
    if name == "MockClaudeAPIClient":
        from .api.mock_client import MockClaudeAPIClient as _MockClaudeAPIClient

        return _MockClaudeAPIClient
    if name == "BaseAgent":
        from .agents.base_agent import BaseAgent as _BaseAgent

        return _BaseAgent
    raise AttributeError(f"module 'multi_agent_dev' has no attribute '{name}'")


if TYPE_CHECKING:  # pragma: no cover
    from .core.agent_manager import AgentManager
    from .core.workflow_engine import WorkflowEngine
    from .api.claude_client import ClaudeAPIClient
    from .api.mock_client import MockClaudeAPIClient
    from .agents.base_agent import BaseAgent
