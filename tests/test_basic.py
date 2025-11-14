"""
基础功能测试
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from multi_agent_dev.models.task import ProjectRequirements, Task, AgentType, TaskPriority
from multi_agent_dev.utils.validation import validate_project_requirements, validate_code_files
from multi_agent_dev.api.claude_client import ClaudeAPIClient


class TestProjectRequirements:
    """项目需求测试"""
    
    def test_create_project_requirements(self):
        """测试创建项目需求"""
        requirements = ProjectRequirements(
            title="测试项目",
            description="这是一个测试项目",
            features=["功能1", "功能2"],
            tech_stack=["Python", "Flask"]
        )
        
        assert requirements.title == "测试项目"
        assert requirements.description == "这是一个测试项目"
        assert len(requirements.features) == 2
        assert len(requirements.tech_stack) == 2
    
    def test_validate_project_requirements_valid(self):
        """测试有效的项目需求验证"""
        requirements = {
            "title": "测试项目",
            "description": "这是一个测试项目的详细描述",
            "features": ["功能1", "功能2"],
            "tech_stack": ["Python", "Flask"]
        }
        
        is_valid, errors = validate_project_requirements(requirements)
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_project_requirements_invalid(self):
        """测试无效的项目需求验证"""
        requirements = {
            "title": "",  # 空标题
            "description": "短描述",  # 描述太短
            "features": [],
            "tech_stack": None
        }
        
        is_valid, errors = validate_project_requirements(requirements)
        assert not is_valid
        assert len(errors) > 0


class TestTask:
    """任务测试"""
    
    def test_create_task(self):
        """测试创建任务"""
        task = Task(
            title="测试任务",
            description="这是一个测试任务",
            assigned_agent=AgentType.DEVELOPER,
            priority=TaskPriority.HIGH
        )
        
        assert task.title == "测试任务"
        assert task.assigned_agent == AgentType.DEVELOPER
        assert task.priority == TaskPriority.HIGH
        assert task.id is not None


class TestValidation:
    """验证工具测试"""
    
    def test_validate_code_files_valid(self):
        """测试有效的代码文件验证"""
        code_files = {
            "main.py": "print('Hello, World!')",
            "utils.py": "def helper_function():\n    pass",
            "requirements.txt": "flask==2.0.1"
        }
        
        is_valid, errors = validate_code_files(code_files)
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_code_files_invalid(self):
        """测试无效的代码文件验证"""
        code_files = {
            "": "content",  # 空文件名
            "main.py": "",  # 空内容
            "../unsafe.py": "content",  # 不安全路径
        }
        
        is_valid, errors = validate_code_files(code_files)
        assert not is_valid
        assert len(errors) > 0


class TestClaudeAPIClient:
    """Claude API客户端测试"""
    
    @pytest.mark.asyncio
    async def test_api_client_initialization(self):
        """测试API客户端初始化"""
        # 使用模拟的API密钥
        client = ClaudeAPIClient(api_key="test-api-key")
        assert client.api_key == "test-api-key"
        assert client.model is not None
        assert client.max_tokens > 0
    
    @pytest.mark.asyncio
    async def test_api_client_stats(self):
        """测试API客户端统计"""
        client = ClaudeAPIClient(api_key="test-api-key")
        
        # 初始统计应该为0
        stats = client.get_stats()
        assert stats['total_requests'] == 0
        assert stats['total_tokens'] == 0
        assert stats['total_errors'] == 0
        
        # 重置统计
        client.reset_stats()
        stats = client.get_stats()
        assert stats['total_requests'] == 0


if __name__ == "__main__":
    pytest.main([__file__])
