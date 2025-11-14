"""
动态工作流引擎
"""

import os
import yaml
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class WorkflowConfig:
    """工作流配置"""
    
    def __init__(self, config_data: Dict):
        self.name = config_data.get('name', '')
        self.description = config_data.get('description', '')
        self.project_types = config_data.get('project_types', [])
        self.complexity_levels = config_data.get('complexity_levels', ['medium'])
        self.stages = config_data.get('stages', [])
        self.global_settings = config_data.get('global_settings', {})
        
    def matches_project(self, project_type: str, complexity: str) -> bool:
        """检查工作流是否匹配项目"""
        type_match = not self.project_types or project_type in self.project_types
        complexity_match = not self.complexity_levels or complexity in self.complexity_levels
        return type_match and complexity_match


class DynamicWorkflowEngine:
    """动态工作流引擎"""
    
    def __init__(self, workflows_dir: str = "workflows"):
        """
        初始化动态工作流引擎
        
        Args:
            workflows_dir: 工作流配置文件目录
        """
        self.workflows_dir = Path(workflows_dir)
        self.workflows: Dict[str, WorkflowConfig] = {}
        self.default_workflow: Optional[WorkflowConfig] = None
        
        # 确保工作流目录存在
        self.workflows_dir.mkdir(exist_ok=True)
        
        # 加载工作流配置
        self._load_workflows()
        
        # 如果没有工作流配置，创建默认配置
        if not self.workflows:
            self._create_default_workflows()
    
    def _load_workflows(self):
        """加载所有工作流配置"""
        logger.info(f"从 {self.workflows_dir} 加载工作流配置")
        
        for config_file in self.workflows_dir.glob("*.yml"):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                
                workflow = WorkflowConfig(config_data)
                self.workflows[config_file.stem] = workflow
                
                # 设置默认工作流
                if config_data.get('is_default', False):
                    self.default_workflow = workflow
                
                logger.info(f"加载工作流配置: {workflow.name}")
                
            except Exception as e:
                logger.error(f"加载工作流配置失败 {config_file}: {str(e)}")
        
        # 如果没有设置默认工作流，使用第一个
        if not self.default_workflow and self.workflows:
            self.default_workflow = list(self.workflows.values())[0]
    
    def _create_default_workflows(self):
        """创建默认工作流配置"""
        logger.info("创建默认工作流配置")
        
        # Web应用开发工作流
        web_workflow = {
            'name': 'Web应用开发流程',
            'description': '标准Web应用开发工作流',
            'project_types': ['web', 'fullstack', 'webapp'],
            'complexity_levels': ['simple', 'medium', 'complex'],
            'is_default': True,
            'global_settings': {
                'max_parallel_agents': 3,
                'quality_threshold': 0.8,
                'auto_retry': True,
                'max_retries': 2
            },
            'stages': [
                {
                    'name': '需求分析',
                    'description': '分析项目需求，制定开发计划',
                    'agents': ['master'],
                    'parallel': False,
                    'quality_gates': ['requirements_analysis'],
                    'timeout_minutes': 30
                },
                {
                    'name': '设计阶段',
                    'description': 'UI设计和数据库设计',
                    'agents': ['ui_design', 'database_design', 'documentation'],
                    'parallel': True,
                    'dependencies': ['需求分析'],
                    'quality_gates': ['design_review'],
                    'timeout_minutes': 60
                },
                {
                    'name': '开发阶段',
                    'description': '前端和后端开发',
                    'agents': ['frontend', 'backend'],
                    'parallel': True,
                    'dependencies': ['设计阶段'],
                    'quality_gates': ['code_quality'],
                    'timeout_minutes': 120
                },
                {
                    'name': '测试阶段',
                    'description': '代码测试和质量保证',
                    'agents': ['testing'],
                    'parallel': False,
                    'dependencies': ['开发阶段'],
                    'quality_gates': ['testing_coverage'],
                    'timeout_minutes': 45
                },
                {
                    'name': '部署阶段',
                    'description': '代码审查和部署准备',
                    'agents': ['review', 'deployment'],
                    'parallel': False,
                    'dependencies': ['测试阶段'],
                    'quality_gates': ['deployment_readiness'],
                    'timeout_minutes': 30
                }
            ]
        }
        
        # API服务开发工作流
        api_workflow = {
            'name': 'API服务开发流程',
            'description': 'RESTful API服务开发工作流',
            'project_types': ['api', 'microservice', 'backend'],
            'complexity_levels': ['simple', 'medium', 'complex'],
            'global_settings': {
                'max_parallel_agents': 2,
                'quality_threshold': 0.85,
                'auto_retry': True,
                'max_retries': 3
            },
            'stages': [
                {
                    'name': '需求分析',
                    'description': '分析API需求和接口设计',
                    'agents': ['master'],
                    'parallel': False,
                    'quality_gates': ['requirements_analysis'],
                    'timeout_minutes': 20
                },
                {
                    'name': '设计阶段',
                    'description': 'API设计和数据库设计',
                    'agents': ['database_design', 'documentation'],
                    'parallel': True,
                    'dependencies': ['需求分析'],
                    'quality_gates': ['design_review'],
                    'timeout_minutes': 40
                },
                {
                    'name': '开发阶段',
                    'description': 'API实现和文档生成',
                    'agents': ['backend', 'documentation'],
                    'parallel': True,
                    'dependencies': ['设计阶段'],
                    'quality_gates': ['code_quality'],
                    'timeout_minutes': 90
                },
                {
                    'name': '测试阶段',
                    'description': 'API测试和集成测试',
                    'agents': ['testing'],
                    'parallel': False,
                    'dependencies': ['开发阶段'],
                    'quality_gates': ['testing_coverage'],
                    'timeout_minutes': 30
                },
                {
                    'name': '部署阶段',
                    'description': '代码审查和部署',
                    'agents': ['review', 'deployment'],
                    'parallel': False,
                    'dependencies': ['测试阶段'],
                    'quality_gates': ['deployment_readiness'],
                    'timeout_minutes': 20
                }
            ]
        }
        
        # 移动应用开发工作流
        mobile_workflow = {
            'name': '移动应用开发流程',
            'description': '移动应用开发工作流',
            'project_types': ['mobile', 'ios', 'android', 'react-native', 'flutter'],
            'complexity_levels': ['simple', 'medium', 'complex'],
            'global_settings': {
                'max_parallel_agents': 4,
                'quality_threshold': 0.8,
                'auto_retry': True,
                'max_retries': 2
            },
            'stages': [
                {
                    'name': '需求分析',
                    'description': '分析移动应用需求',
                    'agents': ['master'],
                    'parallel': False,
                    'quality_gates': ['requirements_analysis'],
                    'timeout_minutes': 30
                },
                {
                    'name': '设计阶段',
                    'description': 'UI/UX设计和数据设计',
                    'agents': ['ui_design', 'database_design'],
                    'parallel': True,
                    'dependencies': ['需求分析'],
                    'quality_gates': ['design_review'],
                    'timeout_minutes': 80
                },
                {
                    'name': '开发阶段',
                    'description': '移动端和后端开发',
                    'agents': ['frontend', 'backend'],
                    'parallel': True,
                    'dependencies': ['设计阶段'],
                    'quality_gates': ['code_quality'],
                    'timeout_minutes': 150
                },
                {
                    'name': '测试阶段',
                    'description': '功能测试和设备兼容性测试',
                    'agents': ['testing'],
                    'parallel': False,
                    'dependencies': ['开发阶段'],
                    'quality_gates': ['testing_coverage'],
                    'timeout_minutes': 60
                },
                {
                    'name': '部署阶段',
                    'description': '应用打包和发布准备',
                    'agents': ['review', 'deployment'],
                    'parallel': False,
                    'dependencies': ['测试阶段'],
                    'quality_gates': ['deployment_readiness'],
                    'timeout_minutes': 40
                }
            ]
        }
        
        # 保存默认工作流配置
        workflows = {
            'web_application': web_workflow,
            'api_service': api_workflow,
            'mobile_application': mobile_workflow
        }
        
        for name, config in workflows.items():
            config_file = self.workflows_dir / f"{name}.yml"
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            workflow = WorkflowConfig(config)
            self.workflows[name] = workflow
            
            if config.get('is_default'):
                self.default_workflow = workflow
        
        logger.info(f"创建了 {len(workflows)} 个默认工作流配置")
    
    async def load_workflow_config(self, project_type: str, complexity: str) -> Dict[str, Any]:
        """
        根据项目类型和复杂度加载工作流配置
        
        Args:
            project_type: 项目类型
            complexity: 复杂度级别
            
        Returns:
            工作流配置字典
        """
        logger.info(f"为项目类型 {project_type}({complexity}) 选择工作流")
        
        # 查找匹配的工作流
        best_match = None
        best_score = 0
        
        for workflow in self.workflows.values():
            if workflow.matches_project(project_type, complexity):
                # 计算匹配分数
                score = 0
                if project_type in workflow.project_types:
                    score += 2
                if complexity in workflow.complexity_levels:
                    score += 1
                
                if score > best_score:
                    best_match = workflow
                    best_score = score
        
        # 如果没有找到匹配的工作流，使用默认工作流
        if not best_match:
            best_match = self.default_workflow
            logger.warning(f"未找到匹配的工作流，使用默认工作流: {best_match.name}")
        else:
            logger.info(f"选择工作流: {best_match.name}")
        
        return {
            'name': best_match.name,
            'description': best_match.description,
            'stages': best_match.stages,
            'global_settings': best_match.global_settings
        }
    
    def get_available_workflows(self) -> List[Dict[str, Any]]:
        """获取所有可用的工作流"""
        return [
            {
                'name': workflow.name,
                'description': workflow.description,
                'project_types': workflow.project_types,
                'complexity_levels': workflow.complexity_levels,
                'stages_count': len(workflow.stages)
            }
            for workflow in self.workflows.values()
        ]
    
    async def validate_workflow_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证工作流配置的有效性
        
        Args:
            config: 工作流配置
            
        Returns:
            验证结果
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # 检查必需字段
        required_fields = ['name', 'stages']
        for field in required_fields:
            if field not in config:
                validation_result['errors'].append(f"缺少必需字段: {field}")
                validation_result['valid'] = False
        
        # 检查阶段配置
        if 'stages' in config:
            stages = config['stages']
            if not isinstance(stages, list) or len(stages) == 0:
                validation_result['errors'].append("stages必须是非空列表")
                validation_result['valid'] = False
            else:
                stage_names = set()
                for i, stage in enumerate(stages):
                    if not isinstance(stage, dict):
                        validation_result['errors'].append(f"阶段 {i} 必须是字典")
                        continue
                    
                    # 检查阶段名称
                    if 'name' not in stage:
                        validation_result['errors'].append(f"阶段 {i} 缺少name字段")
                    else:
                        stage_name = stage['name']
                        if stage_name in stage_names:
                            validation_result['errors'].append(f"重复的阶段名称: {stage_name}")
                        stage_names.add(stage_name)
                    
                    # 检查Agent配置
                    if 'agents' not in stage:
                        validation_result['errors'].append(f"阶段 {stage.get('name', i)} 缺少agents字段")
                    elif not isinstance(stage['agents'], list):
                        validation_result['errors'].append(f"阶段 {stage.get('name', i)} 的agents必须是列表")
                    
                    # 检查依赖关系
                    if 'dependencies' in stage:
                        dependencies = stage['dependencies']
                        if isinstance(dependencies, list):
                            for dep in dependencies:
                                if dep not in stage_names and dep != stage.get('name'):
                                    validation_result['warnings'].append(
                                        f"阶段 {stage.get('name', i)} 依赖未定义的阶段: {dep}"
                                    )
        
        return validation_result
    
    async def create_custom_workflow(self, config: Dict[str, Any]) -> bool:
        """
        创建自定义工作流
        
        Args:
            config: 工作流配置
            
        Returns:
            是否创建成功
        """
        # 验证配置
        validation_result = await self.validate_workflow_config(config)
        if not validation_result['valid']:
            logger.error(f"工作流配置无效: {validation_result['errors']}")
            return False
        
        # 生成文件名
        workflow_name = config['name'].lower().replace(' ', '_').replace('-', '_')
        config_file = self.workflows_dir / f"{workflow_name}.yml"
        
        try:
            # 保存配置文件
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            # 加载到内存
            workflow = WorkflowConfig(config)
            self.workflows[workflow_name] = workflow
            
            logger.info(f"创建自定义工作流: {config['name']}")
            return True
            
        except Exception as e:
            logger.error(f"创建自定义工作流失败: {str(e)}")
            return False
