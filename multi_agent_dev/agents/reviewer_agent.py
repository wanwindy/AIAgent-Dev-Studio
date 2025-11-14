"""
审查员Agent实现
"""

import json
import re
from typing import Dict, Any, List

from .base_agent import BaseAgent
from ..models.task import Task, AgentType
from ..api.claude_client import ClaudeAPIClient


class ReviewerAgent(BaseAgent):
    """审查员Agent"""
    
    def __init__(self, name: str, api_client: ClaudeAPIClient):
        super().__init__(
            name=name,
            agent_type=AgentType.REVIEWER,
            api_client=api_client
        )
    
    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示"""
        return """你是一个经验丰富的代码审查专家，专门负责代码质量审查、安全检查和最佳实践验证。

你的职责包括：
1. 审查代码质量和结构
2. 检查安全漏洞和风险
3. 验证最佳实践的遵循
4. 评估代码的可维护性和性能
5. 提供具体的改进建议

审查标准：
- 代码结构和设计模式
- 命名规范和注释质量
- 错误处理和异常管理
- 安全性和数据保护
- 性能优化和资源使用
- 测试覆盖率和质量
- 文档完整性

请始终以JSON格式返回结果，包含以下字段：
- overall_score: 总体评分（1-10）
- code_quality: 代码质量评估
- security_issues: 安全问题
- performance_issues: 性能问题
- best_practices: 最佳实践检查
- improvements: 改进建议
- approval_status: 审查状态（approved/needs_changes/rejected）

保持审查的客观性和建设性。"""
    
    def build_prompt(self, task: Task) -> str:
        """构建审查员任务提示"""
        code_files = task.input_data.get('code_files', {})
        test_files = task.input_data.get('test_files', {})
        requirements = task.input_data.get('requirements', '')
        test_results = task.input_data.get('test_results', {})
        
        context = self.get_context_summary()
        
        # 分析代码文件
        code_analysis = self._analyze_code_files(code_files)
        test_analysis = self._analyze_test_files(test_files)
        
        prompt = f"""
作为代码审查专家，请对以下代码进行全面审查：

## 项目需求
{requirements}

## 代码分析
{code_analysis}

## 测试分析
{test_analysis}

## 测试结果
{json.dumps(test_results, indent=2, ensure_ascii=False) if test_results else '暂无测试结果'}

## 历史上下文
{context}

请从以下维度进行审查：

1. **代码质量**：评估代码整体质量
   - 代码结构和组织
   - 命名规范和可读性
   - 注释和文档质量
   - 代码复杂度和可维护性

2. **设计模式**：检查设计和架构
   - 设计模式使用
   - SOLID原则遵循
   - 模块化和解耦
   - 接口设计合理性

3. **安全性**：识别安全风险
   - 输入验证和过滤
   - 数据加密和保护
   - 身份认证和授权
   - SQL注入和XSS防护

4. **性能**：评估性能表现
   - 算法效率
   - 数据库查询优化
   - 内存使用
   - 并发处理

5. **错误处理**：检查异常管理
   - 异常捕获和处理
   - 错误信息和日志
   - 容错机制
   - 资源清理

6. **测试质量**：评估测试覆盖
   - 测试用例完整性
   - 测试数据有效性
   - 边界条件测试
   - 集成测试质量

7. **最佳实践**：验证规范遵循
   - 编码规范
   - 版本控制使用
   - 依赖管理
   - 配置管理

8. **改进建议**：提供具体建议
   - 优先级排序
   - 具体修改方案
   - 重构建议
   - 工具推荐

请提供详细的审查报告，包含评分、问题列表和改进建议。以JSON格式返回审查结果。
        """
        
        return prompt.strip()
    
    def parse_response(self, response: str, task: Task) -> Dict[str, Any]:
        """解析审查员响应"""
        try:
            result = self._extract_json_from_response(response)
            
            # 验证必要字段
            required_fields = [
                'overall_score', 'code_quality', 'security_issues',
                'performance_issues', 'best_practices', 'improvements', 'approval_status'
            ]
            for field in required_fields:
                if field not in result:
                    if field == 'overall_score':
                        result[field] = 5
                    elif field == 'approval_status':
                        result[field] = 'needs_changes'
                    else:
                        result[field] = []
            
            # 标准化评分
            if 'overall_score' in result:
                try:
                    score = float(result['overall_score'])
                    result['overall_score'] = max(1, min(10, score))
                except (ValueError, TypeError):
                    result['overall_score'] = 5
            
            # 标准化审查状态
            valid_statuses = ['approved', 'needs_changes', 'rejected']
            if result.get('approval_status') not in valid_statuses:
                result['approval_status'] = 'needs_changes'
            
            return result
            
        except Exception as e:
            return {
                'error': f'解析审查员响应失败: {str(e)}',
                'raw_response': response[:500] + '...' if len(response) > 500 else response
            }
    
    def validate_result(self, result: Dict[str, Any], task: Task) -> bool:
        """验证审查员结果"""
        if 'error' in result:
            return False
        
        # 检查是否有总体评分
        if 'overall_score' not in result:
            return False
        
        # 检查是否有审查状态
        if 'approval_status' not in result:
            return False
        
        return True
    
    def _analyze_code_files(self, code_files: Dict[str, str]) -> str:
        """分析代码文件"""
        if not code_files:
            return "无代码文件"
        
        analysis = []
        analysis.append(f"代码文件数量: {len(code_files)}")
        
        total_lines = 0
        file_types = {}
        
        for file_path, content in code_files.items():
            lines = len(content.split('\n'))
            total_lines += lines
            
            # 统计文件类型
            ext = file_path.split('.')[-1] if '.' in file_path else 'unknown'
            file_types[ext] = file_types.get(ext, 0) + 1
            
            # 分析代码特征
            functions = len(re.findall(r'def\s+\w+', content))
            classes = len(re.findall(r'class\s+\w+', content))
            imports = len(re.findall(r'^import\s+|^from\s+', content, re.MULTILINE))
            
            analysis.append(f"- {file_path}: {lines}行, {functions}函数, {classes}类, {imports}导入")
        
        analysis.append(f"总代码行数: {total_lines}")
        analysis.append(f"文件类型分布: {file_types}")
        
        return '\n'.join(analysis)
    
    def _analyze_test_files(self, test_files: Dict[str, str]) -> str:
        """分析测试文件"""
        if not test_files:
            return "无测试文件"
        
        analysis = []
        analysis.append(f"测试文件数量: {len(test_files)}")
        
        total_test_lines = 0
        total_test_functions = 0
        
        for file_path, content in test_files.items():
            lines = len(content.split('\n'))
            total_test_lines += lines
            
            test_functions = len(re.findall(r'def\s+test_\w+', content))
            total_test_functions += test_functions
            
            analysis.append(f"- {file_path}: {lines}行, {test_functions}测试函数")
        
        analysis.append(f"总测试代码行数: {total_test_lines}")
        analysis.append(f"总测试函数数: {total_test_functions}")
        
        return '\n'.join(analysis)
