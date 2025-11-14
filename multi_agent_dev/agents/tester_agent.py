"""
测试员Agent实现
"""

import json
from typing import Dict, Any

from .base_agent import BaseAgent
from ..models.task import Task, AgentType
from ..api.claude_client import ClaudeAPIClient


class TesterAgent(BaseAgent):
    """测试员Agent"""
    
    def __init__(self, name: str, api_client: ClaudeAPIClient):
        super().__init__(
            name=name,
            agent_type=AgentType.TESTER,
            api_client=api_client
        )
    
    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示"""
        return """你是一个专业的软件测试工程师，专门负责编写和执行各种类型的测试。

你的职责包括：
1. 编写单元测试、集成测试和端到端测试
2. 设计测试用例和测试数据
3. 执行测试并生成测试报告
4. 识别和报告缺陷
5. 验证功能和性能要求

测试要求：
- 覆盖所有主要功能和边界情况
- 包含正常和异常场景
- 使用合适的测试框架和工具
- 提供清晰的测试文档
- 确保测试的可维护性和可重复性

请始终以JSON格式返回结果，包含以下字段：
- test_files: 测试文件，格式为 {文件路径: 文件内容}
- test_cases: 测试用例描述
- test_data: 测试数据
- coverage_report: 测试覆盖率分析
- test_results: 测试执行结果
- recommendations: 测试建议和改进点

保持测试的全面性和专业性。"""
    
    def build_prompt(self, task: Task) -> str:
        """构建测试员任务提示"""
        code_files = task.input_data.get('code_files', {})
        requirements = task.input_data.get('requirements', '')
        architecture = task.input_data.get('architecture', {})
        
        context = self.get_context_summary()
        
        # 提取主要代码文件信息
        code_summary = ""
        if code_files:
            code_summary = "主要代码文件：\n"
            for file_path, content in list(code_files.items())[:5]:  # 只显示前5个文件
                code_summary += f"- {file_path}: {len(content)} 字符\n"
                # 提取函数和类名
                import re
                functions = re.findall(r'def\s+(\w+)', content)
                classes = re.findall(r'class\s+(\w+)', content)
                if functions:
                    code_summary += f"  函数: {', '.join(functions[:5])}\n"
                if classes:
                    code_summary += f"  类: {', '.join(classes[:3])}\n"
        
        prompt = f"""
作为专业测试工程师，请为以下代码编写全面的测试：

## 项目需求
{requirements}

## 架构信息
{json.dumps(architecture, indent=2, ensure_ascii=False) if architecture else '暂无架构信息'}

## 代码概览
{code_summary if code_summary else '暂无代码文件'}

## 历史上下文
{context}

请提供以下测试内容：

1. **单元测试**：为每个函数和类编写测试
   - 测试正常功能
   - 测试边界条件
   - 测试异常情况
   - 使用合适的测试框架（如pytest、unittest等）

2. **集成测试**：测试模块间的交互
   - API接口测试
   - 数据库交互测试
   - 外部服务集成测试
   - 端到端流程测试

3. **测试用例设计**：详细的测试场景
   - 功能测试用例
   - 性能测试用例
   - 安全测试用例
   - 兼容性测试用例

4. **测试数据**：准备测试所需数据
   - 正常数据集
   - 边界数据集
   - 异常数据集
   - Mock数据

5. **测试配置**：测试环境和配置
   - 测试配置文件
   - 测试数据库设置
   - 测试环境变量
   - CI/CD测试流程

6. **性能测试**：性能和负载测试
   - 响应时间测试
   - 并发测试
   - 内存使用测试
   - 压力测试

7. **测试报告**：测试结果分析
   - 测试覆盖率
   - 缺陷报告
   - 性能指标
   - 改进建议

请确保测试全面、可执行、易维护。以JSON格式返回测试实现。
        """
        
        return prompt.strip()
    
    def parse_response(self, response: str, task: Task) -> Dict[str, Any]:
        """解析测试员响应"""
        try:
            result = self._extract_json_from_response(response)
            
            # 验证必要字段
            required_fields = [
                'test_files', 'test_cases', 'test_data', 
                'coverage_report', 'test_results', 'recommendations'
            ]
            for field in required_fields:
                if field not in result:
                    if field == 'test_files':
                        result[field] = {}
                    else:
                        result[field] = []
            
            # 处理测试文件
            if 'test_files' in result and isinstance(result['test_files'], dict):
                processed_files = {}
                for file_path, content in result['test_files'].items():
                    # 清理文件路径
                    clean_path = file_path.strip().lstrip('/')
                    
                    # 确保测试文件有正确的命名
                    if not clean_path.startswith('test_') and not clean_path.endswith('_test.py'):
                        if clean_path.endswith('.py'):
                            clean_path = 'test_' + clean_path
                        else:
                            clean_path = 'test_' + clean_path + '.py'
                    
                    processed_files[clean_path] = content
                
                result['test_files'] = processed_files
            
            # 标准化测试用例格式
            if 'test_cases' in result and isinstance(result['test_cases'], list):
                standardized_cases = []
                for case in result['test_cases']:
                    if isinstance(case, dict):
                        standardized_case = {
                            'name': case.get('name', '未命名测试用例'),
                            'description': case.get('description', ''),
                            'type': case.get('type', 'functional'),
                            'priority': case.get('priority', 'medium'),
                            'steps': case.get('steps', []),
                            'expected_result': case.get('expected_result', ''),
                            'test_data': case.get('test_data', {})
                        }
                        standardized_cases.append(standardized_case)
                
                result['test_cases'] = standardized_cases
            
            return result
            
        except Exception as e:
            return {
                'error': f'解析测试员响应失败: {str(e)}',
                'raw_response': response[:500] + '...' if len(response) > 500 else response
            }
    
    def validate_result(self, result: Dict[str, Any], task: Task) -> bool:
        """验证测试员结果"""
        if 'error' in result:
            return False
        
        # 检查是否有测试文件
        if 'test_files' not in result or not isinstance(result['test_files'], dict):
            return False
        
        # 检查是否至少有一个测试文件
        if len(result['test_files']) == 0:
            return False
        
        # 检查是否有测试用例
        if 'test_cases' not in result or not isinstance(result['test_cases'], list):
            return False
        
        return True
