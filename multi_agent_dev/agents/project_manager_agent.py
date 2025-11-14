"""
项目经理Agent实现
"""

import json
from typing import Dict, Any

from .base_agent import BaseAgent
from ..models.task import Task, AgentType
from ..api.claude_client import ClaudeAPIClient


class ProjectManagerAgent(BaseAgent):
    """项目经理Agent"""
    
    def __init__(self, name: str, api_client: ClaudeAPIClient):
        super().__init__(
            name=name,
            agent_type=AgentType.PROJECT_MANAGER,
            api_client=api_client
        )
    
    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示"""
        return """你是一个经验丰富的项目经理，专门负责软件项目的需求分析、任务分解和项目规划。

你的职责包括：
1. 分析项目需求，理解业务目标和技术要求
2. 将复杂项目分解为可管理的任务
3. 制定合理的开发计划和时间线
4. 识别项目风险和依赖关系
5. 提供技术栈建议和架构指导

请始终以JSON格式返回结果，包含以下字段：
- tasks: 任务列表，每个任务包含title, description, priority, estimated_hours, dependencies
- timeline: 项目时间线和里程碑
- tech_stack: 推荐的技术栈
- risks: 识别的风险和缓解措施
- resources: 所需资源和技能要求

保持专业、详细和实用的分析风格。"""
    
    def build_prompt(self, task: Task) -> str:
        """构建项目经理任务提示"""
        requirements = task.input_data.get('requirements', '')
        constraints = task.input_data.get('constraints', {})
        
        context = self.get_context_summary()
        
        prompt = f"""
作为项目经理，请分析以下项目需求并制定详细的开发计划：

## 项目需求
{requirements}

## 约束条件
{json.dumps(constraints, indent=2, ensure_ascii=False) if constraints else '无特殊约束'}

## 历史上下文
{context}

请提供以下分析：

1. **任务分解**：将项目分解为具体的开发任务
   - 每个任务应该是独立可执行的
   - 包含优先级（critical/high/medium/low）
   - 预估工作量（小时）
   - 任务间的依赖关系

2. **项目时间线**：制定合理的开发计划
   - 主要里程碑和交付物
   - 关键路径分析
   - 缓冲时间安排

3. **技术栈建议**：推荐合适的技术选型
   - 编程语言和框架
   - 数据库和存储方案
   - 部署和运维工具

4. **风险评估**：识别潜在风险
   - 技术风险
   - 进度风险
   - 资源风险
   - 缓解措施

5. **资源需求**：明确所需资源
   - 技能要求
   - 人力配置
   - 工具和环境

请以JSON格式返回分析结果。
        """
        
        return prompt.strip()
    
    def parse_response(self, response: str, task: Task) -> Dict[str, Any]:
        """解析项目经理响应"""
        try:
            result = self._extract_json_from_response(response)
            
            # 验证必要字段
            required_fields = ['tasks', 'timeline', 'tech_stack', 'risks', 'resources']
            for field in required_fields:
                if field not in result:
                    result[field] = []
            
            # 标准化任务格式
            if 'tasks' in result and isinstance(result['tasks'], list):
                standardized_tasks = []
                for i, task_item in enumerate(result['tasks']):
                    if isinstance(task_item, dict):
                        standardized_task = {
                            'id': f"task_{i+1}",
                            'title': task_item.get('title', f'任务 {i+1}'),
                            'description': task_item.get('description', ''),
                            'priority': task_item.get('priority', 'medium'),
                            'estimated_hours': task_item.get('estimated_hours', 8),
                            'dependencies': task_item.get('dependencies', []),
                            'assigned_agent': task_item.get('assigned_agent', 'developer')
                        }
                        standardized_tasks.append(standardized_task)
                
                result['tasks'] = standardized_tasks
            
            return result
            
        except Exception as e:
            return {
                'error': f'解析项目经理响应失败: {str(e)}',
                'raw_response': response[:500] + '...' if len(response) > 500 else response
            }
    
    def validate_result(self, result: Dict[str, Any], task: Task) -> bool:
        """验证项目经理结果"""
        if 'error' in result:
            return False
        
        # 检查是否有任务列表
        if 'tasks' not in result or not isinstance(result['tasks'], list):
            return False
        
        # 检查任务列表是否为空
        if len(result['tasks']) == 0:
            return False
        
        # 检查每个任务是否有必要字段
        for task_item in result['tasks']:
            if not isinstance(task_item, dict):
                return False
            
            required_task_fields = ['title', 'description']
            for field in required_task_fields:
                if field not in task_item or not task_item[field]:
                    return False
        
        return True
