"""
架构师Agent实现
"""

import json
from typing import Dict, Any

from .base_agent import BaseAgent
from ..models.task import Task, AgentType
from ..api.claude_client import ClaudeAPIClient


class ArchitectAgent(BaseAgent):
    """架构师Agent"""
    
    def __init__(self, name: str, api_client: ClaudeAPIClient):
        super().__init__(
            name=name,
            agent_type=AgentType.ARCHITECT,
            api_client=api_client
        )
    
    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示"""
        return """你是一个资深的软件架构师，专门负责系统架构设计、技术选型和模块划分。

你的职责包括：
1. 设计系统整体架构和模块结构
2. 制定技术规范和编码标准
3. 定义接口和数据模型
4. 考虑系统的可扩展性、性能和安全性
5. 提供详细的技术实现指导

请始终以JSON格式返回结果，包含以下字段：
- architecture: 系统架构描述
- modules: 模块划分和职责
- interfaces: API接口定义
- data_models: 数据模型设计
- tech_specs: 技术规范
- patterns: 设计模式建议
- security: 安全考虑
- performance: 性能优化建议

保持技术专业性和实用性。"""
    
    def build_prompt(self, task: Task) -> str:
        """构建架构师任务提示"""
        requirements = task.input_data.get('requirements', '')
        pm_analysis = task.input_data.get('pm_analysis', {})
        tech_stack = pm_analysis.get('tech_stack', []) if isinstance(pm_analysis, dict) else []
        
        context = self.get_context_summary()
        
        prompt = f"""
作为系统架构师，请基于以下信息设计详细的系统架构：

## 项目需求
{requirements}

## 项目经理分析
{json.dumps(pm_analysis, indent=2, ensure_ascii=False) if pm_analysis else '暂无项目经理分析'}

## 推荐技术栈
{json.dumps(tech_stack, indent=2, ensure_ascii=False) if tech_stack else '暂无技术栈建议'}

## 历史上下文
{context}

请提供以下架构设计：

1. **系统架构**：整体架构设计
   - 架构模式（如MVC、微服务、分层架构等）
   - 系统组件和层次结构
   - 数据流和控制流
   - 部署架构

2. **模块划分**：详细的模块设计
   - 核心模块和功能模块
   - 模块间的依赖关系
   - 模块职责和边界
   - 代码组织结构

3. **接口设计**：API和接口规范
   - RESTful API设计
   - 数据传输格式
   - 错误处理机制
   - 版本控制策略

4. **数据模型**：数据库和数据结构设计
   - 实体关系图
   - 数据表结构
   - 索引策略
   - 数据迁移方案

5. **技术规范**：开发标准和规范
   - 编码规范
   - 命名约定
   - 文档标准
   - 测试策略

6. **设计模式**：推荐的设计模式
   - 创建型模式
   - 结构型模式
   - 行为型模式
   - 架构模式

7. **安全设计**：安全考虑和措施
   - 身份认证和授权
   - 数据加密
   - 输入验证
   - 安全漏洞防护

8. **性能优化**：性能设计考虑
   - 缓存策略
   - 数据库优化
   - 并发处理
   - 负载均衡

请以JSON格式返回架构设计。
        """
        
        return prompt.strip()
    
    def parse_response(self, response: str, task: Task) -> Dict[str, Any]:
        """解析架构师响应"""
        try:
            result = self._extract_json_from_response(response)
            
            # 验证必要字段
            required_fields = [
                'architecture', 'modules', 'interfaces', 'data_models',
                'tech_specs', 'patterns', 'security', 'performance'
            ]
            for field in required_fields:
                if field not in result:
                    result[field] = {}
            
            # 标准化模块格式
            if 'modules' in result and isinstance(result['modules'], list):
                standardized_modules = {}
                for module in result['modules']:
                    if isinstance(module, dict) and 'name' in module:
                        module_name = module['name']
                        standardized_modules[module_name] = {
                            'description': module.get('description', ''),
                            'responsibilities': module.get('responsibilities', []),
                            'dependencies': module.get('dependencies', []),
                            'interfaces': module.get('interfaces', [])
                        }
                result['modules'] = standardized_modules
            
            return result
            
        except Exception as e:
            return {
                'error': f'解析架构师响应失败: {str(e)}',
                'raw_response': response[:500] + '...' if len(response) > 500 else response
            }
    
    def validate_result(self, result: Dict[str, Any], task: Task) -> bool:
        """验证架构师结果"""
        if 'error' in result:
            return False
        
        # 检查是否有架构描述
        if 'architecture' not in result or not result['architecture']:
            return False
        
        # 检查是否有模块设计
        if 'modules' not in result or not result['modules']:
            return False
        
        return True
