"""
质量控制器
"""

import json
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class QualityResult:
    """质量检查结果"""
    
    def __init__(self):
        self.passed: bool = False
        self.score: float = 0.0
        self.max_score: float = 100.0
        self.issues: List[Dict[str, Any]] = []
        self.recommendations: List[str] = []
        self.metrics: Dict[str, Any] = {}
        self.timestamp: datetime = datetime.now()
    
    def add_issue(self, severity: str, category: str, description: str, location: str = None):
        """添加质量问题"""
        self.issues.append({
            'severity': severity,  # critical, high, medium, low
            'category': category,
            'description': description,
            'location': location,
            'timestamp': datetime.now().isoformat()
        })
    
    def add_recommendation(self, recommendation: str):
        """添加改进建议"""
        self.recommendations.append(recommendation)
    
    def calculate_final_score(self) -> float:
        """计算最终质量分数"""
        if not self.issues:
            self.score = self.max_score
        else:
            # 根据问题严重程度扣分
            deduction = 0
            for issue in self.issues:
                severity = issue['severity']
                if severity == 'critical':
                    deduction += 25
                elif severity == 'high':
                    deduction += 15
                elif severity == 'medium':
                    deduction += 8
                elif severity == 'low':
                    deduction += 3
            
            self.score = max(0, self.max_score - deduction)
        
        # 设置通过标准（通常是70分以上）
        self.passed = self.score >= 70.0
        return self.score
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'passed': self.passed,
            'score': self.score,
            'max_score': self.max_score,
            'issues': self.issues,
            'recommendations': self.recommendations,
            'metrics': self.metrics,
            'timestamp': self.timestamp.isoformat()
        }


class BaseQualityGate(ABC):
    """质量门控基类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def check(self, artifacts: Dict[str, Any]) -> QualityResult:
        """执行质量检查"""
        pass


class RequirementsQualityGate(BaseQualityGate):
    """需求分析质量门控"""
    
    def __init__(self):
        super().__init__(
            name="需求分析质量检查",
            description="检查需求分析的完整性、可测试性和一致性"
        )
    
    async def check(self, artifacts: Dict[str, Any]) -> QualityResult:
        """检查需求分析质量"""
        result = QualityResult()
        
        # 获取需求分析结果
        analysis = artifacts.get('project_analysis', {})
        task_breakdown = artifacts.get('task_breakdown', {})
        
        # 检查项目分析完整性
        required_analysis_fields = [
            'project_type', 'complexity_level', 'core_features', 'tech_stack'
        ]
        
        for field in required_analysis_fields:
            if field not in analysis or not analysis[field]:
                result.add_issue(
                    'high', 'completeness',
                    f"项目分析缺少必要字段: {field}"
                )
        
        # 检查任务分解质量
        if not task_breakdown or 'tasks' not in task_breakdown:
            result.add_issue(
                'critical', 'completeness',
                "缺少任务分解信息"
            )
        else:
            tasks = task_breakdown['tasks']
            if not isinstance(tasks, list) or len(tasks) == 0:
                result.add_issue(
                    'critical', 'completeness',
                    "任务列表为空或格式错误"
                )
            else:
                # 检查每个任务的完整性
                for i, task in enumerate(tasks):
                    if not isinstance(task, dict):
                        continue
                    
                    required_task_fields = ['title', 'description', 'priority']
                    for field in required_task_fields:
                        if field not in task or not task[field]:
                            result.add_issue(
                                'medium', 'task_definition',
                                f"任务 {i+1} 缺少字段: {field}"
                            )
        
        # 检查技术栈合理性
        tech_stack = analysis.get('tech_stack', {})
        if tech_stack:
            # 检查是否有前端和后端技术（对于web项目）
            project_type = analysis.get('project_type', '').lower()
            if 'web' in project_type or 'fullstack' in project_type:
                if not tech_stack.get('frontend') and not tech_stack.get('backend'):
                    result.add_issue(
                        'medium', 'tech_stack',
                        "Web项目应该包含前端或后端技术栈"
                    )
        
        # 添加改进建议
        if result.issues:
            result.add_recommendation("完善需求分析，确保所有必要信息都已包含")
            result.add_recommendation("验证任务分解的合理性和可执行性")
        
        result.metrics = {
            'analysis_fields_count': len([f for f in required_analysis_fields if f in analysis]),
            'tasks_count': len(task_breakdown.get('tasks', [])) if task_breakdown else 0,
            'tech_stack_completeness': len(tech_stack) if tech_stack else 0
        }
        
        result.calculate_final_score()
        return result


class DesignQualityGate(BaseQualityGate):
    """设计质量门控"""
    
    def __init__(self):
        super().__init__(
            name="设计质量检查",
            description="检查架构设计和UI设计的合理性"
        )
    
    async def check(self, artifacts: Dict[str, Any]) -> QualityResult:
        """检查设计质量"""
        result = QualityResult()
        
        # 检查设计文档
        deliverables = artifacts.get('deliverables', {})
        
        # 检查UI设计
        ui_design = deliverables.get('ui_design', {})
        if ui_design:
            if 'components' not in ui_design:
                result.add_issue(
                    'medium', 'ui_design',
                    "UI设计缺少组件定义"
                )
            if 'style_guide' not in ui_design:
                result.add_issue(
                    'low', 'ui_design',
                    "建议包含样式指南"
                )
        
        # 检查数据库设计
        db_design = deliverables.get('database_design', {})
        if db_design:
            if 'tables' not in db_design and 'entities' not in db_design:
                result.add_issue(
                    'high', 'database_design',
                    "数据库设计缺少表结构或实体定义"
                )
            
            # 检查关系定义
            if 'relationships' not in db_design:
                result.add_issue(
                    'medium', 'database_design',
                    "数据库设计缺少关系定义"
                )
        
        # 检查API设计（如果有）
        api_design = deliverables.get('api_design', {})
        if api_design:
            if 'endpoints' not in api_design:
                result.add_issue(
                    'high', 'api_design',
                    "API设计缺少端点定义"
                )
        
        result.metrics = {
            'ui_design_completeness': len(ui_design) if ui_design else 0,
            'db_design_completeness': len(db_design) if db_design else 0,
            'api_design_completeness': len(api_design) if api_design else 0
        }
        
        result.calculate_final_score()
        return result


class CodeQualityGate(BaseQualityGate):
    """代码质量门控"""
    
    def __init__(self):
        super().__init__(
            name="代码质量检查",
            description="检查代码规范性、可读性和安全性"
        )
    
    async def check(self, artifacts: Dict[str, Any]) -> QualityResult:
        """检查代码质量"""
        result = QualityResult()
        
        # 获取代码文件
        deliverables = artifacts.get('deliverables', {})
        code_files = deliverables.get('code_files', {})
        
        if not code_files:
            result.add_issue(
                'critical', 'completeness',
                "没有生成代码文件"
            )
            result.calculate_final_score()
            return result
        
        total_lines = 0
        files_with_comments = 0
        security_issues = 0
        
        for filename, content in code_files.items():
            if not isinstance(content, str):
                continue
            
            lines = content.split('\n')
            total_lines += len(lines)
            
            # 检查注释
            comment_lines = self._count_comment_lines(content, filename)
            if comment_lines > 0:
                files_with_comments += 1
            
            # 检查安全问题
            security_issues += self._check_security_issues(content, filename)
            
            # 检查代码结构
            structure_issues = self._check_code_structure(content, filename)
            for issue in structure_issues:
                result.add_issue(
                    issue['severity'], 'code_structure',
                    issue['description'], filename
                )
        
        # 计算指标
        comment_ratio = files_with_comments / len(code_files) if code_files else 0
        
        # 评估质量
        if comment_ratio < 0.5:
            result.add_issue(
                'medium', 'documentation',
                f"代码注释覆盖率较低: {comment_ratio:.1%}"
            )
        
        if security_issues > 0:
            result.add_issue(
                'high', 'security',
                f"发现 {security_issues} 个潜在安全问题"
            )
        
        # 添加建议
        if comment_ratio < 0.8:
            result.add_recommendation("增加代码注释，提高可读性")
        
        if security_issues > 0:
            result.add_recommendation("修复安全问题，使用安全的编程实践")
        
        result.metrics = {
            'total_files': len(code_files),
            'total_lines': total_lines,
            'comment_coverage': comment_ratio,
            'security_issues': security_issues,
            'files_with_comments': files_with_comments
        }
        
        result.calculate_final_score()
        return result
    
    def _count_comment_lines(self, content: str, filename: str) -> int:
        """统计注释行数"""
        lines = content.split('\n')
        comment_count = 0
        
        for line in lines:
            line = line.strip()
            # Python注释
            if line.startswith('#'):
                comment_count += 1
            # JavaScript/Java注释
            elif line.startswith('//') or line.startswith('/*'):
                comment_count += 1
            # HTML注释
            elif line.startswith('<!--'):
                comment_count += 1
        
        return comment_count
    
    def _check_security_issues(self, content: str, filename: str) -> int:
        """检查安全问题"""
        issues = 0
        content_lower = content.lower()
        
        # 检查硬编码密码
        password_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'pwd\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']'
        ]
        
        for pattern in password_patterns:
            if re.search(pattern, content_lower):
                issues += 1
        
        # 检查SQL注入风险
        if 'select * from' in content_lower and 'where' in content_lower:
            if not ('prepared' in content_lower or 'parameterized' in content_lower):
                issues += 1
        
        return issues
    
    def _check_code_structure(self, content: str, filename: str) -> List[Dict[str, str]]:
        """检查代码结构"""
        issues = []
        lines = content.split('\n')
        
        # 检查函数长度
        current_function_lines = 0
        in_function = False
        
        for line in lines:
            line = line.strip()
            
            # 检测函数开始（简单检测）
            if ('def ' in line or 'function ' in line) and ':' in line:
                in_function = True
                current_function_lines = 1
            elif in_function:
                current_function_lines += 1
                
                # 检测函数结束（简单检测）
                if line == '' and current_function_lines > 50:
                    issues.append({
                        'severity': 'medium',
                        'description': f'函数过长 ({current_function_lines} 行)，建议拆分'
                    })
                    in_function = False
                elif not line.startswith(' ') and not line.startswith('\t') and line != '':
                    in_function = False
        
        return issues


class TestingQualityGate(BaseQualityGate):
    """测试质量门控"""
    
    def __init__(self):
        super().__init__(
            name="测试质量检查",
            description="检查测试覆盖率和测试用例质量"
        )
    
    async def check(self, artifacts: Dict[str, Any]) -> QualityResult:
        """检查测试质量"""
        result = QualityResult()
        
        # 获取测试相关信息
        deliverables = artifacts.get('deliverables', {})
        test_files = deliverables.get('test_files', {})
        test_results = artifacts.get('test_results', {})
        
        if not test_files:
            result.add_issue(
                'critical', 'completeness',
                "没有生成测试文件"
            )
        else:
            # 检查测试文件质量
            total_test_cases = 0
            for filename, content in test_files.items():
                if isinstance(content, str):
                    test_cases = self._count_test_cases(content)
                    total_test_cases += test_cases
            
            if total_test_cases == 0:
                result.add_issue(
                    'high', 'test_coverage',
                    "测试文件中没有发现测试用例"
                )
            elif total_test_cases < 5:
                result.add_issue(
                    'medium', 'test_coverage',
                    f"测试用例数量较少: {total_test_cases}"
                )
        
        # 检查测试结果
        if test_results:
            passed_tests = test_results.get('passed', 0)
            failed_tests = test_results.get('failed', 0)
            total_tests = passed_tests + failed_tests
            
            if total_tests > 0:
                pass_rate = passed_tests / total_tests
                if pass_rate < 0.8:
                    result.add_issue(
                        'high', 'test_results',
                        f"测试通过率较低: {pass_rate:.1%}"
                    )
                elif pass_rate < 0.9:
                    result.add_issue(
                        'medium', 'test_results',
                        f"测试通过率需要改进: {pass_rate:.1%}"
                    )
        
        result.metrics = {
            'test_files_count': len(test_files),
            'total_test_cases': total_test_cases,
            'test_pass_rate': test_results.get('pass_rate', 0) if test_results else 0
        }
        
        result.calculate_final_score()
        return result
    
    def _count_test_cases(self, content: str) -> int:
        """统计测试用例数量"""
        # 简单的测试用例计数
        test_patterns = [
            r'def test_\w+',  # Python
            r'it\s*\(',       # JavaScript
            r'@Test',         # Java
            r'TEST\s*\('      # C++
        ]
        
        count = 0
        for pattern in test_patterns:
            count += len(re.findall(pattern, content, re.IGNORECASE))
        
        return count


class DeploymentQualityGate(BaseQualityGate):
    """部署质量门控"""
    
    def __init__(self):
        super().__init__(
            name="部署就绪检查",
            description="检查部署配置和文档完整性"
        )
    
    async def check(self, artifacts: Dict[str, Any]) -> QualityResult:
        """检查部署就绪性"""
        result = QualityResult()
        
        deliverables = artifacts.get('deliverables', {})
        
        # 检查部署配置
        deployment_config = deliverables.get('deployment_config', {})
        if not deployment_config:
            result.add_issue(
                'high', 'deployment',
                "缺少部署配置"
            )
        
        # 检查文档
        documentation = deliverables.get('documentation', {})
        if not documentation:
            result.add_issue(
                'medium', 'documentation',
                "缺少项目文档"
            )
        else:
            required_docs = ['README', 'API文档', '部署指南']
            for doc_type in required_docs:
                if doc_type not in str(documentation):
                    result.add_issue(
                        'low', 'documentation',
                        f"建议添加{doc_type}"
                    )
        
        # 检查环境配置
        if 'environment' not in deployment_config:
            result.add_issue(
                'medium', 'deployment',
                "缺少环境配置信息"
            )
        
        result.metrics = {
            'has_deployment_config': bool(deployment_config),
            'has_documentation': bool(documentation),
            'deployment_completeness': len(deployment_config) if deployment_config else 0
        }
        
        result.calculate_final_score()
        return result


class QualityController:
    """质量控制器"""
    
    def __init__(self):
        """初始化质量控制器"""
        self.quality_gates = {
            'requirements_analysis': RequirementsQualityGate(),
            'design_review': DesignQualityGate(),
            'code_quality': CodeQualityGate(),
            'testing_coverage': TestingQualityGate(),
            'deployment_readiness': DeploymentQualityGate()
        }
        
        # 质量标准配置
        self.quality_standards = {
            'min_score': 70.0,
            'critical_issues_allowed': 0,
            'high_issues_allowed': 2,
            'auto_fix_enabled': True
        }
    
    async def check_quality_gate(self, gate_name: str, artifacts: Dict[str, Any]) -> QualityResult:
        """
        检查质量门控
        
        Args:
            gate_name: 质量门控名称
            artifacts: 检查的工件
            
        Returns:
            质量检查结果
        """
        if gate_name not in self.quality_gates:
            logger.error(f"未知的质量门控: {gate_name}")
            result = QualityResult()
            result.add_issue('critical', 'system', f"未知的质量门控: {gate_name}")
            result.calculate_final_score()
            return result
        
        logger.info(f"执行质量门控检查: {gate_name}")
        
        try:
            gate = self.quality_gates[gate_name]
            result = await gate.check(artifacts)
            
            logger.info(
                f"质量门控 {gate_name} 检查完成: "
                f"分数={result.score:.1f}, 通过={result.passed}, "
                f"问题数={len(result.issues)}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"质量门控检查失败 {gate_name}: {str(e)}")
            result = QualityResult()
            result.add_issue('critical', 'system', f"质量检查执行失败: {str(e)}")
            result.calculate_final_score()
            return result
    
    async def check_multiple_gates(self, gate_names: List[str], artifacts: Dict[str, Any]) -> Dict[str, QualityResult]:
        """
        检查多个质量门控
        
        Args:
            gate_names: 质量门控名称列表
            artifacts: 检查的工件
            
        Returns:
            质量检查结果字典
        """
        results = {}
        
        for gate_name in gate_names:
            result = await self.check_quality_gate(gate_name, artifacts)
            results[gate_name] = result
        
        return results
    
    def get_overall_quality_score(self, gate_results: Dict[str, QualityResult]) -> Tuple[float, bool]:
        """
        计算总体质量分数
        
        Args:
            gate_results: 各个质量门控的结果
            
        Returns:
            (总体分数, 是否通过)
        """
        if not gate_results:
            return 0.0, False
        
        total_score = sum(result.score for result in gate_results.values())
        average_score = total_score / len(gate_results)
        
        # 检查是否有关键问题
        critical_issues = sum(
            len([issue for issue in result.issues if issue['severity'] == 'critical'])
            for result in gate_results.values()
        )
        
        high_issues = sum(
            len([issue for issue in result.issues if issue['severity'] == 'high'])
            for result in gate_results.values()
        )
        
        # 判断是否通过
        passed = (
            average_score >= self.quality_standards['min_score'] and
            critical_issues <= self.quality_standards['critical_issues_allowed'] and
            high_issues <= self.quality_standards['high_issues_allowed']
        )
        
        return average_score, passed
    
    def get_quality_report(self, gate_results: Dict[str, QualityResult]) -> Dict[str, Any]:
        """
        生成质量报告
        
        Args:
            gate_results: 各个质量门控的结果
            
        Returns:
            质量报告
        """
        overall_score, overall_passed = self.get_overall_quality_score(gate_results)
        
        # 收集所有问题
        all_issues = []
        all_recommendations = []
        
        for gate_name, result in gate_results.items():
            for issue in result.issues:
                issue['gate'] = gate_name
                all_issues.append(issue)
            
            for rec in result.recommendations:
                all_recommendations.append(f"[{gate_name}] {rec}")
        
        # 按严重程度排序问题
        all_issues.sort(key=lambda x: {
            'critical': 0, 'high': 1, 'medium': 2, 'low': 3
        }.get(x['severity'], 4))
        
        return {
            'overall_score': overall_score,
            'overall_passed': overall_passed,
            'gate_results': {name: result.to_dict() for name, result in gate_results.items()},
            'summary': {
                'total_gates': len(gate_results),
                'passed_gates': len([r for r in gate_results.values() if r.passed]),
                'total_issues': len(all_issues),
                'critical_issues': len([i for i in all_issues if i['severity'] == 'critical']),
                'high_issues': len([i for i in all_issues if i['severity'] == 'high']),
                'medium_issues': len([i for i in all_issues if i['severity'] == 'medium']),
                'low_issues': len([i for i in all_issues if i['severity'] == 'low'])
            },
            'all_issues': all_issues,
            'recommendations': all_recommendations,
            'timestamp': datetime.now().isoformat()
        }
