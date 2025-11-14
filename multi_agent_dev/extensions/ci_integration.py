"""
CI/CD集成功能
"""

import asyncio
import logging
import subprocess
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

from config import settings


logger = logging.getLogger(__name__)


class CIIntegration:
    """CI/CD集成"""
    
    def __init__(self, project_path: Optional[str] = None):
        """
        初始化CI/CD集成
        
        Args:
            project_path: 项目路径
        """
        self.project_path = Path(project_path or ".")
        self.enabled = True
        
    async def run_tests(self, test_command: Optional[str] = None) -> Dict[str, Any]:
        """
        运行测试
        
        Args:
            test_command: 测试命令，默认自动检测
            
        Returns:
            测试结果
        """
        if not test_command:
            test_command = self._detect_test_command()
        
        if not test_command:
            return {
                'success': False,
                'error': '无法检测到测试命令',
                'output': ''
            }
        
        try:
            logger.info(f"运行测试命令: {test_command}")
            
            process = await asyncio.create_subprocess_shell(
                test_command,
                cwd=self.project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            stdout, _ = await process.communicate()
            output = stdout.decode('utf-8') if stdout else ''
            
            success = process.returncode == 0
            
            result = {
                'success': success,
                'return_code': process.returncode,
                'output': output,
                'command': test_command
            }
            
            if success:
                logger.info("测试执行成功")
            else:
                logger.error(f"测试执行失败，返回码: {process.returncode}")
            
            return result
            
        except Exception as e:
            logger.error(f"运行测试失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'output': '',
                'command': test_command
            }
    
    async def run_linting(self, lint_command: Optional[str] = None) -> Dict[str, Any]:
        """
        运行代码检查
        
        Args:
            lint_command: 检查命令，默认自动检测
            
        Returns:
            检查结果
        """
        if not lint_command:
            lint_command = self._detect_lint_command()
        
        if not lint_command:
            return {
                'success': False,
                'error': '无法检测到代码检查命令',
                'output': ''
            }
        
        try:
            logger.info(f"运行代码检查: {lint_command}")
            
            process = await asyncio.create_subprocess_shell(
                lint_command,
                cwd=self.project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            stdout, _ = await process.communicate()
            output = stdout.decode('utf-8') if stdout else ''
            
            # 对于linting，返回码非0不一定是错误，可能只是有警告
            success = True
            
            result = {
                'success': success,
                'return_code': process.returncode,
                'output': output,
                'command': lint_command,
                'issues_found': process.returncode != 0
            }
            
            logger.info(f"代码检查完成，发现问题: {result['issues_found']}")
            return result
            
        except Exception as e:
            logger.error(f"运行代码检查失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'output': '',
                'command': lint_command
            }
    
    async def build_project(self, build_command: Optional[str] = None) -> Dict[str, Any]:
        """
        构建项目
        
        Args:
            build_command: 构建命令，默认自动检测
            
        Returns:
            构建结果
        """
        if not build_command:
            build_command = self._detect_build_command()
        
        if not build_command:
            return {
                'success': False,
                'error': '无法检测到构建命令',
                'output': ''
            }
        
        try:
            logger.info(f"构建项目: {build_command}")
            
            process = await asyncio.create_subprocess_shell(
                build_command,
                cwd=self.project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            stdout, _ = await process.communicate()
            output = stdout.decode('utf-8') if stdout else ''
            
            success = process.returncode == 0
            
            result = {
                'success': success,
                'return_code': process.returncode,
                'output': output,
                'command': build_command
            }
            
            if success:
                logger.info("项目构建成功")
            else:
                logger.error(f"项目构建失败，返回码: {process.returncode}")
            
            return result
            
        except Exception as e:
            logger.error(f"构建项目失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'output': '',
                'command': build_command
            }
    
    async def run_full_pipeline(self) -> Dict[str, Any]:
        """
        运行完整的CI/CD流水线
        
        Returns:
            流水线执行结果
        """
        pipeline_result = {
            'success': True,
            'stages': {},
            'total_duration': 0
        }
        
        import time
        start_time = time.time()
        
        # 阶段1: 代码检查
        logger.info("CI/CD流水线 - 阶段1: 代码检查")
        lint_result = await self.run_linting()
        pipeline_result['stages']['linting'] = lint_result
        
        if not lint_result['success']:
            pipeline_result['success'] = False
            logger.error("代码检查阶段失败，停止流水线")
            return pipeline_result
        
        # 阶段2: 运行测试
        logger.info("CI/CD流水线 - 阶段2: 运行测试")
        test_result = await self.run_tests()
        pipeline_result['stages']['testing'] = test_result
        
        if not test_result['success']:
            pipeline_result['success'] = False
            logger.error("测试阶段失败，停止流水线")
            return pipeline_result
        
        # 阶段3: 构建项目
        logger.info("CI/CD流水线 - 阶段3: 构建项目")
        build_result = await self.build_project()
        pipeline_result['stages']['building'] = build_result
        
        if not build_result['success']:
            pipeline_result['success'] = False
            logger.error("构建阶段失败")
            return pipeline_result
        
        pipeline_result['total_duration'] = time.time() - start_time
        logger.info(f"CI/CD流水线完成，耗时: {pipeline_result['total_duration']:.2f}s")
        
        return pipeline_result
    
    def generate_ci_config(self, platform: str = 'github') -> str:
        """
        生成CI配置文件
        
        Args:
            platform: CI平台 (github, gitlab, jenkins)
            
        Returns:
            CI配置文件内容
        """
        if platform.lower() == 'github':
            return self._generate_github_actions_config()
        elif platform.lower() == 'gitlab':
            return self._generate_gitlab_ci_config()
        else:
            return "# 不支持的CI平台"
    
    def _detect_test_command(self) -> Optional[str]:
        """自动检测测试命令"""
        # 检查常见的测试配置文件
        if (self.project_path / "pytest.ini").exists() or \
           (self.project_path / "pyproject.toml").exists():
            return "pytest"
        
        if (self.project_path / "package.json").exists():
            return "npm test"
        
        if (self.project_path / "Cargo.toml").exists():
            return "cargo test"
        
        if (self.project_path / "go.mod").exists():
            return "go test ./..."
        
        # 默认Python测试
        return "python -m pytest"
    
    def _detect_lint_command(self) -> Optional[str]:
        """自动检测代码检查命令"""
        # Python项目
        if any((self.project_path / f).exists() for f in ["setup.py", "pyproject.toml", "requirements.txt"]):
            return "flake8 . && black --check ."
        
        # Node.js项目
        if (self.project_path / "package.json").exists():
            return "npm run lint"
        
        # Rust项目
        if (self.project_path / "Cargo.toml").exists():
            return "cargo clippy"
        
        # Go项目
        if (self.project_path / "go.mod").exists():
            return "go vet ./... && gofmt -l ."
        
        return None
    
    def _detect_build_command(self) -> Optional[str]:
        """自动检测构建命令"""
        # Python项目
        if (self.project_path / "setup.py").exists():
            return "python setup.py build"
        
        # Node.js项目
        if (self.project_path / "package.json").exists():
            return "npm run build"
        
        # Rust项目
        if (self.project_path / "Cargo.toml").exists():
            return "cargo build --release"
        
        # Go项目
        if (self.project_path / "go.mod").exists():
            return "go build ./..."
        
        return None
    
    def _generate_github_actions_config(self) -> str:
        """生成GitHub Actions配置"""
        return """name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run linting
      run: |
        flake8 .
        black --check .
    
    - name: Run tests
      run: |
        pytest --cov=./ --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
"""
    
    def _generate_gitlab_ci_config(self) -> str:
        """生成GitLab CI配置"""
        return """stages:
  - lint
  - test
  - build

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip/
    - venv/

before_script:
  - python -m venv venv
  - source venv/bin/activate
  - pip install -r requirements.txt

lint:
  stage: lint
  script:
    - flake8 .
    - black --check .

test:
  stage: test
  script:
    - pytest --cov=./ --cov-report=xml
  coverage: '/TOTAL.+?(\d+\%)$/'

build:
  stage: build
  script:
    - python setup.py build
  artifacts:
    paths:
      - dist/
"""
