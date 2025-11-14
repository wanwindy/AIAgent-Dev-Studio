"""
开发者Agent实现
"""

import json
import re
from typing import Dict, Any

from .base_agent import BaseAgent
from ..models.task import Task, AgentType
from ..api.claude_client import ClaudeAPIClient


class DeveloperAgent(BaseAgent):
    """开发者Agent"""
    
    def __init__(self, name: str, api_client: ClaudeAPIClient):
        super().__init__(
            name=name,
            agent_type=AgentType.DEVELOPER,
            api_client=api_client
        )
    
    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示"""
        return """你是一个资深的软件开发工程师，专门负责高质量代码的编写和实现。

你的职责包括：
1. 根据需求和架构设计编写代码
2. 遵循最佳实践和编码规范
3. 实现完整的功能模块
4. 处理错误和异常情况
5. 编写清晰的注释和文档

编码要求：
- 代码结构清晰，逻辑合理
- 遵循SOLID原则和设计模式
- 包含完整的错误处理
- 添加必要的注释和文档字符串
- 考虑代码的可维护性和可扩展性

请始终以JSON格式返回结果，包含以下字段：
- files: 生成的代码文件，格式为 {文件路径: 文件内容}
- dependencies: 所需的依赖包
- setup_instructions: 安装和配置说明
- usage_examples: 使用示例
- notes: 实现说明和注意事项

保持代码的专业性和实用性。"""
    
    def build_prompt(self, task: Task) -> str:
        """构建开发者任务提示"""
        task_description = task.description
        requirements = task.input_data.get('requirements', '')
        architecture = task.input_data.get('architecture', {})
        pm_analysis = task.input_data.get('pm_analysis', {})
        
        context = self.get_context_summary()
        
        prompt = f"""
作为资深开发工程师，请根据以下信息实现代码：

## 任务描述
{task_description}

## 项目需求
{requirements}

## 架构设计
{json.dumps(architecture, indent=2, ensure_ascii=False) if architecture else '暂无架构设计'}

## 项目分析
{json.dumps(pm_analysis, indent=2, ensure_ascii=False) if pm_analysis else '暂无项目分析'}

## 历史上下文
{context}

请实现以下内容：

1. **代码实现**：编写完整的功能代码
   - 遵循架构设计和技术规范
   - 实现所有必要的功能
   - 包含完整的错误处理
   - 添加详细的注释

2. **文件结构**：组织合理的代码文件
   - 按模块划分文件
   - 遵循命名约定
   - 包含配置文件
   - 添加必要的初始化文件

3. **依赖管理**：列出所需依赖
   - 第三方库和框架
   - 版本要求
   - 安装说明

4. **配置说明**：提供配置指导
   - 环境变量设置
   - 配置文件说明
   - 数据库初始化
   - 服务启动方式

5. **使用示例**：提供使用演示
   - API调用示例
   - 功能演示代码
   - 测试用例
   - 常见问题解决

请确保代码质量高、结构清晰、功能完整。以JSON格式返回实现结果。
        """
        
        return prompt.strip()
    
    def parse_response(self, response: str, task: Task) -> Dict[str, Any]:
        """解析开发者响应"""
        try:
            result = self._extract_json_from_response(response)
            
            # 验证必要字段
            required_fields = ['files', 'dependencies', 'setup_instructions', 'usage_examples', 'notes']
            for field in required_fields:
                if field not in result:
                    if field == 'files':
                        result[field] = {}
                    else:
                        result[field] = []
            
            # 处理代码文件
            if 'files' in result and isinstance(result['files'], dict):
                processed_files = {}
                for file_path, content in result['files'].items():
                    # 清理文件路径
                    clean_path = file_path.strip().lstrip('/')
                    
                    # 如果内容包含代码块标记，提取代码
                    if isinstance(content, str):
                        # 移除markdown代码块标记
                        content = re.sub(r'^```\w*\n', '', content, flags=re.MULTILINE)
                        content = re.sub(r'\n```$', '', content, flags=re.MULTILINE)
                        content = content.strip()
                    
                    processed_files[clean_path] = content
                
                result['files'] = processed_files
            
            return result
            
        except Exception as e:
            return {
                'error': f'解析开发者响应失败: {str(e)}',
                'raw_response': response[:500] + '...' if len(response) > 500 else response
            }
    
    def validate_result(self, result: Dict[str, Any], task: Task) -> bool:
        """验证开发者结果"""
        if 'error' in result:
            return False
        
        # 检查是否有代码文件
        if 'files' not in result or not isinstance(result['files'], dict):
            return False
        
        # 检查是否至少有一个代码文件
        if len(result['files']) == 0:
            return False
        
        # 检查代码文件内容是否为空
        for file_path, content in result['files'].items():
            if not content or not content.strip():
                return False
        
        return True
