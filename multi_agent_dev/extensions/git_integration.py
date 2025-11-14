"""
Git集成功能
"""

import os
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
import git
from git import Repo, InvalidGitRepositoryError

from config import settings


logger = logging.getLogger(__name__)


class GitIntegration:
    """Git版本控制集成"""
    
    def __init__(self, repo_path: Optional[str] = None):
        """
        初始化Git集成
        
        Args:
            repo_path: Git仓库路径，默认使用配置中的路径
        """
        self.repo_path = Path(repo_path or settings.git_repo_path or ".")
        self.repo: Optional[Repo] = None
        self.enabled = settings.git_enabled
        
        if self.enabled:
            self._initialize_repo()
    
    def _initialize_repo(self):
        """初始化Git仓库"""
        try:
            # 尝试打开现有仓库
            self.repo = Repo(self.repo_path)
            logger.info(f"Git仓库已连接: {self.repo_path}")
        except InvalidGitRepositoryError:
            try:
                # 初始化新仓库
                self.repo = Repo.init(self.repo_path)
                logger.info(f"Git仓库已初始化: {self.repo_path}")
            except Exception as e:
                logger.error(f"Git仓库初始化失败: {str(e)}")
                self.enabled = False
        except Exception as e:
            logger.error(f"Git仓库连接失败: {str(e)}")
            self.enabled = False
    
    def create_feature_branch(self, feature_name: str) -> bool:
        """
        创建功能分支
        
        Args:
            feature_name: 功能分支名称
            
        Returns:
            是否创建成功
        """
        if not self.enabled or not self.repo:
            return False
        
        try:
            # 确保在主分支上
            main_branch = self._get_main_branch()
            if main_branch:
                main_branch.checkout()
            
            # 创建并切换到新分支
            new_branch = self.repo.create_head(feature_name)
            new_branch.checkout()
            
            logger.info(f"功能分支已创建: {feature_name}")
            return True
            
        except Exception as e:
            logger.error(f"创建功能分支失败: {str(e)}")
            return False
    
    def commit_changes(self, message: str, files: Optional[List[str]] = None) -> bool:
        """
        提交更改
        
        Args:
            message: 提交信息
            files: 要提交的文件列表，None表示提交所有更改
            
        Returns:
            是否提交成功
        """
        if not self.enabled or not self.repo:
            return False
        
        try:
            # 添加文件到暂存区
            if files:
                for file_path in files:
                    self.repo.index.add([file_path])
            else:
                self.repo.git.add('--all')
            
            # 检查是否有更改
            if not self.repo.index.diff("HEAD"):
                logger.info("没有更改需要提交")
                return True
            
            # 提交更改
            commit = self.repo.index.commit(message)
            logger.info(f"更改已提交: {commit.hexsha[:8]} - {message}")
            return True
            
        except Exception as e:
            logger.error(f"提交更改失败: {str(e)}")
            return False
    
    def create_pull_request_info(self, title: str, description: str) -> Dict[str, Any]:
        """
        创建Pull Request信息
        
        Args:
            title: PR标题
            description: PR描述
            
        Returns:
            PR信息字典
        """
        if not self.enabled or not self.repo:
            return {}
        
        try:
            current_branch = self.repo.active_branch.name
            main_branch = self._get_main_branch_name()
            
            # 获取分支间的差异
            commits = list(self.repo.iter_commits(f'{main_branch}..{current_branch}'))
            
            pr_info = {
                'title': title,
                'description': description,
                'source_branch': current_branch,
                'target_branch': main_branch,
                'commits': [
                    {
                        'sha': commit.hexsha,
                        'message': commit.message.strip(),
                        'author': str(commit.author),
                        'date': commit.committed_datetime.isoformat()
                    }
                    for commit in commits
                ],
                'files_changed': self._get_changed_files(main_branch, current_branch)
            }
            
            return pr_info
            
        except Exception as e:
            logger.error(f"创建PR信息失败: {str(e)}")
            return {}
    
    def get_commit_history(self, max_count: int = 10) -> List[Dict[str, Any]]:
        """
        获取提交历史
        
        Args:
            max_count: 最大提交数量
            
        Returns:
            提交历史列表
        """
        if not self.enabled or not self.repo:
            return []
        
        try:
            commits = []
            for commit in self.repo.iter_commits(max_count=max_count):
                commits.append({
                    'sha': commit.hexsha,
                    'short_sha': commit.hexsha[:8],
                    'message': commit.message.strip(),
                    'author': str(commit.author),
                    'date': commit.committed_datetime.isoformat(),
                    'files': [item.a_path for item in commit.stats.files.keys()]
                })
            
            return commits
            
        except Exception as e:
            logger.error(f"获取提交历史失败: {str(e)}")
            return []
    
    def get_branch_info(self) -> Dict[str, Any]:
        """
        获取分支信息
        
        Returns:
            分支信息字典
        """
        if not self.enabled or not self.repo:
            return {}
        
        try:
            current_branch = self.repo.active_branch.name
            all_branches = [branch.name for branch in self.repo.branches]
            
            return {
                'current_branch': current_branch,
                'all_branches': all_branches,
                'is_dirty': self.repo.is_dirty(),
                'untracked_files': self.repo.untracked_files
            }
            
        except Exception as e:
            logger.error(f"获取分支信息失败: {str(e)}")
            return {}
    
    def save_generated_code(self, code_files: Dict[str, str], project_name: str) -> bool:
        """
        保存生成的代码到Git仓库
        
        Args:
            code_files: 代码文件字典 {文件路径: 文件内容}
            project_name: 项目名称
            
        Returns:
            是否保存成功
        """
        if not self.enabled or not self.repo:
            return False
        
        try:
            # 创建项目目录
            project_dir = self.repo_path / "generated_projects" / project_name
            project_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存代码文件
            saved_files = []
            for file_path, content in code_files.items():
                full_path = project_dir / file_path.lstrip('/')
                full_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                saved_files.append(str(full_path.relative_to(self.repo_path)))
            
            # 提交更改
            commit_message = f"Add generated project: {project_name}"
            return self.commit_changes(commit_message, saved_files)
            
        except Exception as e:
            logger.error(f"保存生成代码失败: {str(e)}")
            return False
    
    def _get_main_branch(self):
        """获取主分支对象"""
        if not self.repo:
            return None
        
        # 尝试常见的主分支名称
        main_branch_names = ['main', 'master', 'develop']
        
        for branch_name in main_branch_names:
            try:
                return self.repo.heads[branch_name]
            except IndexError:
                continue
        
        # 如果没有找到，返回第一个分支
        if self.repo.heads:
            return self.repo.heads[0]
        
        return None
    
    def _get_main_branch_name(self) -> str:
        """获取主分支名称"""
        main_branch = self._get_main_branch()
        return main_branch.name if main_branch else 'main'
    
    def _get_changed_files(self, base_branch: str, compare_branch: str) -> List[str]:
        """获取分支间的文件变更"""
        try:
            diff = self.repo.git.diff(f'{base_branch}..{compare_branch}', name_only=True)
            return diff.split('\n') if diff else []
        except Exception as e:
            logger.error(f"获取文件变更失败: {str(e)}")
            return []
    
    def is_enabled(self) -> bool:
        """检查Git集成是否启用"""
        return self.enabled and self.repo is not None
