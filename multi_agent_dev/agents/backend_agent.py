"""
后端开发Agent实现
"""

import json
import logging
from typing import Dict, Any, List

from .base_agent import BaseAgent
from ..models.task import Task, AgentType
from ..api.claude_client import ClaudeAPIClient

logger = logging.getLogger(__name__)


class BackendAgent(BaseAgent):
    """后端开发Agent"""
    
    def __init__(self, name: str, api_client: ClaudeAPIClient):
        super().__init__(
            name=name,
            agent_type=AgentType.BACKEND,
            api_client=api_client
        )
    
    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示"""
        return """你是一个资深的后端开发工程师，专门负责服务端应用开发。

你的专业技能包括：
1. 后端框架：Django、Flask、FastAPI、Express.js、Spring Boot
2. 数据库：MySQL、PostgreSQL、MongoDB、Redis
3. API设计：RESTful API、GraphQL、gRPC
4. 认证授权：JWT、OAuth2、Session
5. 缓存策略：Redis、Memcached
6. 消息队列：RabbitMQ、Kafka、Celery
7. 微服务架构和容器化
8. 性能优化和监控

请根据项目需求和数据库设计，生成高质量的后端代码，包括：
- API接口实现
- 数据模型定义
- 业务逻辑处理
- 数据库操作
- 认证和权限控制
- 错误处理和日志
- 配置文件和部署脚本

返回格式为JSON，包含以下字段：
- models: 数据模型文件
- views: 视图/控制器文件
- services: 业务逻辑文件
- utils: 工具函数文件
- config: 配置文件
- requirements: 依赖文件
- documentation: API文档

确保代码遵循最佳实践，具有良好的安全性和可扩展性。"""

    def build_prompt(self, task: Task) -> str:
        """构建后端开发任务提示"""
        project_plan = task.input_data.get('project_plan', {})
        agent_context = task.input_data.get('agent_context', {})
        global_context = task.input_data.get('global_context', {})
        
        # 提取相关信息
        requirements = global_context.get('requirements', '')
        db_design = global_context.get('artifact_database_design', {})
        api_design = global_context.get('artifact_api_design', {})
        tech_stack = project_plan.get('project_analysis', {}).get('tech_stack', {})
        
        context = self.get_context_summary()
        
        prompt = f"""
作为后端开发工程师，请根据以下信息开发后端服务：

## 项目需求
{requirements}

## 数据库设计
{json.dumps(db_design, indent=2, ensure_ascii=False) if db_design else '暂无数据库设计，请根据需求设计数据模型'}

## API接口设计
{json.dumps(api_design, indent=2, ensure_ascii=False) if api_design else '暂无API设计，请根据需求设计RESTful API'}

## 技术栈要求
{json.dumps(tech_stack, indent=2, ensure_ascii=False) if tech_stack else '请选择合适的后端技术栈'}

## 开发上下文
{context}

请完成以下后端开发任务：

### 1. 技术选型和架构设计
- 选择合适的后端框架
- 确定数据库方案
- 设计API架构
- 选择认证方案

### 2. 数据模型开发
- 定义数据模型/实体类
- 设置数据库关系
- 添加数据验证
- 实现数据迁移

### 3. API接口实现
- RESTful API端点
- 请求参数验证
- 响应数据格式化
- 错误处理

### 4. 业务逻辑实现
- 核心业务功能
- 数据处理逻辑
- 业务规则验证
- 事务管理

### 5. 认证和权限
- 用户认证系统
- 权限控制
- JWT令牌管理
- 安全中间件

### 6. 数据库操作
- CRUD操作
- 复杂查询
- 数据库连接池
- 查询优化

### 7. 配置和部署
- 环境配置
- 日志配置
- 部署脚本
- 健康检查

### 8. 测试和文档
- 单元测试
- API测试
- 接口文档
- 部署文档

请以JSON格式返回完整的后端代码：

```json
{{
  "models": {{
    "user.py": "用户模型代码",
    "product.py": "产品模型代码",
    "...": "其他模型文件"
  }},
  "views": {{
    "user_views.py": "用户API视图",
    "product_views.py": "产品API视图",
    "...": "其他视图文件"
  }},
  "services": {{
    "user_service.py": "用户业务逻辑",
    "auth_service.py": "认证服务",
    "...": "其他服务文件"
  }},
  "utils": {{
    "helpers.py": "工具函数",
    "validators.py": "验证器",
    "...": "其他工具文件"
  }},
  "config": {{
    "settings.py": "应用配置",
    "database.py": "数据库配置",
    "...": "其他配置文件"
  }},
  "requirements": {{
    "requirements.txt": "Python依赖",
    "package.json": "Node.js依赖（如果适用）"
  }},
  "documentation": {{
    "API.md": "API接口文档",
    "SETUP.md": "环境搭建文档",
    "DEPLOYMENT.md": "部署文档"
  }}
}}
```

确保代码安全、高效、可维护。
        """
        
        return prompt.strip()

    def parse_response(self, response: str, task: Task) -> Dict[str, Any]:
        """解析后端开发响应"""
        try:
            result = self._extract_json_from_response(response)
            
            # 验证必需字段
            required_fields = ['models', 'views', 'services', 'config']
            for field in required_fields:
                if field not in result:
                    logger.warning(f"后端开发响应中缺少字段: {field}")
                    result[field] = {}
            
            # 确保有基本的模型文件
            if not result['models']:
                result['models'] = {
                    'base.py': '# 基础模型\nfrom sqlalchemy.ext.declarative import declarative_base\n\nBase = declarative_base()'
                }
            
            # 确保有基本的视图文件
            if not result['views']:
                result['views'] = {
                    'health.py': '# 健康检查\ndef health_check():\n    return {"status": "ok"}'
                }
            
            # 确保有requirements文件
            if 'requirements' not in result:
                result['requirements'] = {}
            
            if not result['requirements']:
                result['requirements'] = {
                    'requirements.txt': 'fastapi==0.104.1\nuvicorn==0.24.0\nsqlalchemy==2.0.23\npydantic==2.5.0'
                }
            
            # 添加统计信息
            result['statistics'] = {
                'model_count': len(result['models']),
                'view_count': len(result['views']),
                'service_count': len(result['services']),
                'config_count': len(result['config']),
                'total_files': sum(len(section) for section in [
                    result['models'], result['views'], result['services'], 
                    result['utils'], result['config']
                ])
            }
            
            return result
            
        except Exception as e:
            logger.error(f"解析后端开发响应失败: {str(e)}")
            return {
                'error': f'响应解析失败: {str(e)}',
                'raw_response': response[:500],
                'models': {},
                'views': {},
                'services': {},
                'config': {},
                'requirements': {}
            }

    def validate_result(self, result: Dict[str, Any], task: Task) -> bool:
        """验证后端开发结果"""
        if "error" in result:
            return False
        
        # 检查是否有基本的模型和视图文件
        models = result.get('models', {})
        views = result.get('views', {})
        
        if not models and not views:
            logger.error("后端开发结果缺少模型和视图文件")
            return False
        
        # 检查是否有配置文件
        config = result.get('config', {})
        if not config:
            logger.warning("后端开发结果缺少配置文件")
        
        # 检查是否有依赖文件
        requirements = result.get('requirements', {})
        if not requirements:
            logger.warning("后端开发结果缺少依赖文件")
        
        return True

    def get_capabilities(self) -> List[str]:
        """获取Agent能力列表"""
        return [
            "RESTful API开发",
            "GraphQL API开发",
            "数据库设计和操作",
            "用户认证和授权",
            "业务逻辑实现",
            "数据验证和处理",
            "缓存策略",
            "性能优化",
            "安全防护",
            "微服务架构",
            "API文档生成",
            "单元测试"
        ]

    def estimate_effort(self, task_description: str) -> Dict[str, Any]:
        """估算开发工作量"""
        base_hours = 12
        
        # 根据关键词调整工作量
        complexity_keywords = {
            'microservice': 2.5,
            'complex': 2.0,
            'advanced': 1.8,
            'simple': 0.6,
            'basic': 0.7,
            'crud': 0.8,
            'api': 1.0,
            'authentication': 1.3,
            'payment': 1.8,
            'real-time': 1.6,
            'machine learning': 2.2,
            'data processing': 1.5
        }
        
        multiplier = 1.0
        for keyword, factor in complexity_keywords.items():
            if keyword in task_description.lower():
                multiplier = max(multiplier, factor)
        
        estimated_hours = base_hours * multiplier
        
        return {
            'estimated_hours': estimated_hours,
            'complexity_level': 'high' if multiplier > 1.5 else 'medium' if multiplier > 1.0 else 'low',
            'key_features': self._extract_features_from_description(task_description),
            'recommended_tech_stack': self._recommend_tech_stack(task_description)
        }
    
    def _extract_features_from_description(self, description: str) -> List[str]:
        """从描述中提取功能需求"""
        features = []
        
        feature_keywords = {
            'user': '用户管理',
            'auth': '认证授权',
            'login': '登录功能',
            'register': '注册功能',
            'crud': 'CRUD操作',
            'api': 'API接口',
            'database': '数据库操作',
            'search': '搜索功能',
            'filter': '筛选功能',
            'pagination': '分页功能',
            'upload': '文件上传',
            'email': '邮件发送',
            'notification': '通知系统',
            'payment': '支付功能',
            'report': '报表生成',
            'export': '数据导出',
            'import': '数据导入',
            'cache': '缓存机制',
            'queue': '队列处理'
        }
        
        description_lower = description.lower()
        for keyword, feature in feature_keywords.items():
            if keyword in description_lower:
                features.append(feature)
        
        return features
    
    def _recommend_tech_stack(self, description: str) -> Dict[str, str]:
        """推荐技术栈"""
        description_lower = description.lower()
        
        # 框架推荐
        if 'django' in description_lower:
            framework = 'Django'
            orm = 'Django ORM'
        elif 'flask' in description_lower:
            framework = 'Flask'
            orm = 'SQLAlchemy'
        elif 'node' in description_lower or 'express' in description_lower:
            framework = 'Express.js'
            orm = 'Sequelize'
        elif 'spring' in description_lower or 'java' in description_lower:
            framework = 'Spring Boot'
            orm = 'JPA/Hibernate'
        else:
            framework = 'FastAPI'  # 默认推荐FastAPI
            orm = 'SQLAlchemy'
        
        # 数据库推荐
        if 'mongo' in description_lower or 'nosql' in description_lower:
            database = 'MongoDB'
        elif 'postgres' in description_lower:
            database = 'PostgreSQL'
        else:
            database = 'MySQL'
        
        # 缓存推荐
        cache = 'Redis'
        
        # 消息队列推荐
        if 'real-time' in description_lower or 'websocket' in description_lower:
            message_queue = 'Redis Pub/Sub'
        elif 'complex' in description_lower or 'microservice' in description_lower:
            message_queue = 'RabbitMQ'
        else:
            message_queue = 'Celery'
        
        return {
            'framework': framework,
            'orm': orm,
            'database': database,
            'cache': cache,
            'message_queue': message_queue,
            'auth': 'JWT',
            'api_docs': 'OpenAPI/Swagger'
        }

    def generate_api_documentation(self, api_endpoints: Dict[str, Any]) -> str:
        """生成API文档"""
        doc_lines = [
            "# API 接口文档\n",
            "## 概述",
            "本文档描述了后端API的所有接口。\n",
            "## 认证",
            "所有API请求需要在Header中包含JWT令牌：",
            "```",
            "Authorization: Bearer <token>",
            "```\n",
            "## 接口列表\n"
        ]
        
        for endpoint, details in api_endpoints.items():
            doc_lines.extend([
                f"### {endpoint}",
                f"**方法**: {details.get('method', 'GET')}",
                f"**描述**: {details.get('description', '暂无描述')}",
                f"**路径**: `{details.get('path', endpoint)}`\n"
            ])
            
            if 'parameters' in details:
                doc_lines.append("**参数**:")
                for param in details['parameters']:
                    doc_lines.append(f"- `{param['name']}` ({param['type']}): {param['description']}")
                doc_lines.append("")
            
            if 'response' in details:
                doc_lines.extend([
                    "**响应示例**:",
                    "```json",
                    json.dumps(details['response'], indent=2, ensure_ascii=False),
                    "```\n"
                ])
        
        return "\n".join(doc_lines)
