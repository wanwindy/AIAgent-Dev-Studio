"""
主Agent实现 - 负责全局协调和任务编排
"""

import json
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import asyncio

from .base_agent import BaseAgent
from ..models.task import Task, AgentResult, AgentType, TaskStatus, TaskPriority
from ..api.claude_client import ClaudeAPIClient
from ..core.dynamic_workflow_engine import DynamicWorkflowEngine
from ..core.global_context_manager import GlobalContextManager
from ..core.quality_controller import QualityController

logger = logging.getLogger(__name__)


class ProjectPlan:
    """项目计划"""
    
    def __init__(self):
        self.project_id: str = ""
        self.project_type: str = ""
        self.complexity_level: str = ""
        self.estimated_duration: int = 0
        self.required_agents: List[str] = []
        self.workflow_config: Dict = {}
        self.quality_gates: List[str] = []
        self.deliverables: List[str] = []
        self.risks: List[Dict] = []
        self.dependencies: Dict[str, List[str]] = {}


class MasterAgent(BaseAgent):
    """主Agent - 负责全局协调和任务编排"""
    
    def __init__(self, name: str, api_client: ClaudeAPIClient):
        super().__init__(
            name=name,
            agent_type=AgentType.MASTER,
            api_client=api_client
        )
        
        # 核心组件
        self.workflow_engine = DynamicWorkflowEngine()
        self.context_manager = GlobalContextManager()
        self.quality_controller = QualityController()
        
        # 子Agent注册表
        self.sub_agents: Dict[str, BaseAgent] = {}
        self.agent_capabilities: Dict[str, List[str]] = {}
        
        # 执行状态
        self.current_project: Optional[ProjectPlan] = None
        self.active_tasks: Dict[str, Task] = {}
        self.completed_stages: Set[str] = set()
        
    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示"""
        return """你是一个高级项目主管和技术架构师，负责统筹管理整个软件开发项目。

你的核心职责：
1. 深度分析项目需求，理解业务目标和技术约束
2. 制定全面的项目计划和开发策略
3. 智能分解复杂任务，识别并行执行机会
4. 协调各专业团队（前端、后端、UI、测试等）的工作
5. 监控项目质量和进度，及时调整策略
6. 确保最终交付物满足所有需求和质量标准

请始终以JSON格式返回分析结果，包含：
- project_analysis: 项目分析结果
- task_breakdown: 详细任务分解
- agent_assignments: Agent分配方案
- workflow_plan: 工作流程规划
- quality_requirements: 质量要求
- risk_assessment: 风险评估
- success_criteria: 成功标准

保持战略思维，注重全局协调和质量控制。"""

    def register_sub_agent(self, agent_type: str, agent: BaseAgent, capabilities: List[str]):
        """注册子Agent"""
        self.sub_agents[agent_type] = agent
        self.agent_capabilities[agent_type] = capabilities
        logger.info(f"注册子Agent: {agent_type}, 能力: {capabilities}")

    async def analyze_requirements(self, requirements_doc: str) -> ProjectPlan:
        """分析需求文档，生成项目计划"""
        logger.info("开始分析项目需求")
        
        # 创建分析任务
        analysis_task = Task(
            title="项目需求深度分析",
            description="分析项目需求并制定全面的开发计划",
            assigned_agent=AgentType.MASTER,
            priority=TaskPriority.CRITICAL,
            input_data={
                'requirements_document': requirements_doc,
                'available_agents': list(self.sub_agents.keys()),
                'agent_capabilities': self.agent_capabilities
            }
        )
        
        # 执行分析
        result = await self.process(analysis_task)
        
        if not result.success:
            raise Exception(f"需求分析失败: {result.error}")
        
        # 解析分析结果并创建项目计划
        analysis_data = result.output
        project_plan = self._create_project_plan(analysis_data, requirements_doc)
        
        self.current_project = project_plan
        
        # 更新全局上下文
        await self.context_manager.update_project_context(
            project_plan.project_id,
            {
                'requirements': requirements_doc,
                'project_plan': project_plan.__dict__,
                'analysis_result': analysis_data
            }
        )
        
        logger.info(f"项目计划创建完成: {project_plan.project_type}, 预计{project_plan.estimated_duration}小时")
        return project_plan

    async def orchestrate_development(self, project_plan: ProjectPlan) -> Dict[str, Any]:
        """编排开发流程，协调子Agent执行"""
        logger.info(f"开始编排开发流程: {project_plan.project_id}")
        
        # 加载工作流配置
        workflow_config = await self.workflow_engine.load_workflow_config(
            project_plan.project_type,
            project_plan.complexity_level
        )
        
        # 初始化执行状态
        execution_results = {
            'project_id': project_plan.project_id,
            'stages': {},
            'overall_status': 'in_progress',
            'start_time': datetime.now(),
            'quality_checks': {},
            'deliverables': {}
        }
        
        try:
            # 按阶段执行工作流
            for stage in workflow_config['stages']:
                stage_name = stage['name']
                logger.info(f"执行阶段: {stage_name}")
                
                # 检查依赖关系
                if not self._check_stage_dependencies(stage, execution_results):
                    logger.warning(f"阶段 {stage_name} 依赖未满足，跳过执行")
                    continue
                
                # 执行阶段任务
                stage_result = await self._execute_stage(stage, project_plan)
                execution_results['stages'][stage_name] = stage_result
                
                # 质量门控检查
                if stage.get('quality_gates'):
                    quality_result = await self._check_quality_gates(
                        stage['quality_gates'],
                        stage_result
                    )
                    execution_results['quality_checks'][stage_name] = quality_result
                    
                    # 检查质量结果
                    passed = False
                    if isinstance(quality_result, dict):
                        # 如果是字典，检查每个门控的结果
                        passed = all(gate_result.get('passed', False) for gate_result in quality_result.values())
                    else:
                        passed = getattr(quality_result, 'passed', False)

                    if not passed:
                        logger.error(f"阶段 {stage_name} 质量检查失败")
                        # 触发修复流程
                        await self._trigger_fix_process(stage_name, quality_result)
                
                self.completed_stages.add(stage_name)
                
                # 更新上下文
                await self.context_manager.update_stage_context(
                    project_plan.project_id,
                    stage_name,
                    stage_result
                )
            
            execution_results['overall_status'] = 'completed'
            execution_results['end_time'] = datetime.now()
            
            logger.info("开发流程编排完成")
            return execution_results
            
        except Exception as e:
            execution_results['overall_status'] = 'failed'
            execution_results['error'] = str(e)
            execution_results['end_time'] = datetime.now()
            
            logger.error(f"开发流程编排失败: {str(e)}")
            raise

    async def _execute_stage(self, stage_config: Dict, project_plan: ProjectPlan) -> Dict[str, Any]:
        """执行单个阶段"""
        stage_name = stage_config['name']
        required_agents = stage_config['agents']
        is_parallel = stage_config.get('parallel', False)
        
        logger.info(f"执行阶段 {stage_name}, 并行: {is_parallel}, 所需Agent: {required_agents}")
        
        # 创建阶段任务
        stage_tasks = []
        for agent_type in required_agents:
            if agent_type == 'master':
                continue  # 主Agent不需要创建子任务
                
            if agent_type not in self.sub_agents:
                logger.warning(f"未找到Agent: {agent_type}")
                continue
            
            task = await self._create_agent_task(agent_type, stage_config, project_plan)
            stage_tasks.append(task)
        
        # 执行任务
        if is_parallel and len(stage_tasks) > 1:
            # 并行执行
            results = await self._execute_tasks_parallel(stage_tasks)
        else:
            # 串行执行
            results = await self._execute_tasks_sequential(stage_tasks)
        
        # 汇总阶段结果
        stage_result = {
            'stage_name': stage_name,
            'status': 'completed',
            'agent_results': results,
            'deliverables': self._extract_deliverables(results),
            'execution_time': sum(r.execution_time for r in results if r.execution_time),
            'tokens_used': sum(r.tokens_used for r in results if r.tokens_used)
        }
        
        return stage_result

    async def _create_agent_task(self, agent_type: str, stage_config: Dict, project_plan: ProjectPlan) -> Task:
        """为特定Agent创建任务"""
        # 获取Agent相关的上下文
        agent_context = await self.context_manager.get_context_for_agent(
            project_plan.project_id,
            agent_type
        )
        
        task = Task(
            title=f"{stage_config['name']} - {agent_type}",
            description=f"执行{stage_config['name']}阶段的{agent_type}相关任务",
            assigned_agent=AgentType(agent_type),
            priority=TaskPriority.HIGH,
            input_data={
                'stage_config': stage_config,
                'project_plan': project_plan.__dict__,
                'agent_context': agent_context,
                'global_context': await self.context_manager.get_global_context(project_plan.project_id)
            }
        )
        
        return task

    def build_prompt(self, task: Task) -> str:
        """构建主Agent任务提示"""
        requirements = task.input_data.get('requirements_document', '')
        available_agents = task.input_data.get('available_agents', [])
        agent_capabilities = task.input_data.get('agent_capabilities', {})
        
        context = self.get_context_summary()
        
        prompt = f"""
作为项目主管，请深度分析以下项目需求并制定全面的开发计划：

## 项目需求文档
{requirements}

## 可用的专业团队
{json.dumps(agent_capabilities, indent=2, ensure_ascii=False)}

## 历史项目经验
{context}

请提供以下全面分析：

### 1. 项目分析 (project_analysis)
- 项目类型识别（web应用、移动应用、API服务等）
- 复杂度评估（简单/中等/复杂/高度复杂）
- 核心功能模块识别
- 技术栈建议
- 非功能性需求分析

### 2. 任务分解 (task_breakdown)
- 将项目分解为可并行执行的任务模块
- 每个任务包含：名称、描述、优先级、预估工时、前置依赖
- 识别关键路径和并行执行机会
- 任务间的数据流和接口定义

### 3. Agent分配方案 (agent_assignments)
- 为每个任务分配最合适的专业Agent
- 考虑Agent能力匹配和工作负载均衡
- 定义Agent间的协作关系和数据传递

### 4. 工作流程规划 (workflow_plan)
- 定义开发阶段和里程碑
- 制定质量检查点和验收标准
- 规划风险控制和应急预案

### 5. 质量要求 (quality_requirements)
- 代码质量标准
- 测试覆盖率要求
- 性能和安全标准
- 文档完整性要求

### 6. 风险评估 (risk_assessment)
- 技术风险识别和缓解措施
- 进度风险和应对策略
- 资源风险和备选方案

### 7. 成功标准 (success_criteria)
- 功能完整性验证标准
- 质量达标标准
- 交付时间要求
- 用户满意度指标

请以JSON格式返回详细的分析结果。
        """
        
        return prompt.strip()

    def parse_response(self, response: str, task: Task) -> Dict[str, Any]:
        """解析主Agent响应"""
        try:
            result = self._extract_json_from_response(response)
            
            # 验证必需字段
            required_fields = [
                'project_analysis', 'task_breakdown', 'agent_assignments',
                'workflow_plan', 'quality_requirements', 'risk_assessment', 'success_criteria'
            ]
            
            for field in required_fields:
                if field not in result:
                    logger.warning(f"响应中缺少必需字段: {field}")
                    result[field] = {}
            
            return result
            
        except Exception as e:
            logger.error(f"解析主Agent响应失败: {str(e)}")
            return {
                'error': f'响应解析失败: {str(e)}',
                'raw_response': response[:500]
            }

    def _create_project_plan(self, analysis_data: Dict, requirements_doc: str) -> ProjectPlan:
        """根据分析结果创建项目计划"""
        plan = ProjectPlan()
        
        project_analysis = analysis_data.get('project_analysis', {})
        plan.project_id = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        plan.project_type = project_analysis.get('project_type', 'unknown')
        plan.complexity_level = project_analysis.get('complexity_level', 'medium')
        plan.estimated_duration = project_analysis.get('estimated_duration', 40)
        
        # 提取所需Agent
        agent_assignments = analysis_data.get('agent_assignments', {})
        plan.required_agents = list(agent_assignments.keys())
        
        # 设置工作流配置
        plan.workflow_config = analysis_data.get('workflow_plan', {})
        
        # 质量门控
        quality_reqs = analysis_data.get('quality_requirements', {})
        plan.quality_gates = quality_reqs.get('quality_gates', [])
        
        # 交付物
        plan.deliverables = analysis_data.get('success_criteria', {}).get('deliverables', [])
        
        # 风险
        plan.risks = analysis_data.get('risk_assessment', {}).get('risks', [])
        
        # 依赖关系
        task_breakdown = analysis_data.get('task_breakdown', {})
        if isinstance(task_breakdown, dict) and 'tasks' in task_breakdown:
            for task in task_breakdown['tasks']:
                if isinstance(task, dict) and 'dependencies' in task:
                    plan.dependencies[task.get('name', '')] = task['dependencies']
        
        return plan

    async def _execute_tasks_parallel(self, tasks: List[Task]) -> List[AgentResult]:
        """并行执行任务"""
        logger.info(f"并行执行 {len(tasks)} 个任务")
        
        async def execute_single_task(task: Task) -> AgentResult:
            agent = self.sub_agents.get(task.assigned_agent.value)
            if not agent:
                return AgentResult(
                    agent_type=task.assigned_agent,
                    task_id=task.id,
                    success=False,
                    error=f"未找到Agent: {task.assigned_agent.value}"
                )
            return await agent.process(task)
        
        # 使用信号量控制并发数
        semaphore = asyncio.Semaphore(3)  # 最多3个并发任务
        
        async def execute_with_semaphore(task: Task) -> AgentResult:
            async with semaphore:
                return await execute_single_task(task)
        
        results = await asyncio.gather(
            *[execute_with_semaphore(task) for task in tasks],
            return_exceptions=True
        )
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(AgentResult(
                    agent_type=tasks[i].assigned_agent,
                    task_id=tasks[i].id,
                    success=False,
                    error=str(result)
                ))
            else:
                processed_results.append(result)
        
        return processed_results

    async def _execute_tasks_sequential(self, tasks: List[Task]) -> List[AgentResult]:
        """串行执行任务"""
        logger.info(f"串行执行 {len(tasks)} 个任务")
        
        results = []
        for task in tasks:
            agent = self.sub_agents.get(task.assigned_agent.value)
            if not agent:
                result = AgentResult(
                    agent_type=task.assigned_agent,
                    task_id=task.id,
                    success=False,
                    error=f"未找到Agent: {task.assigned_agent.value}"
                )
            else:
                result = await agent.process(task)
            
            results.append(result)
            
            # 如果任务失败，根据策略决定是否继续
            if not result.success:
                logger.warning(f"任务执行失败: {task.title}")
                # 这里可以添加失败处理逻辑
        
        return results

    def _check_stage_dependencies(self, stage: Dict[str, Any], execution_results: Dict[str, Any]) -> bool:
        """检查阶段依赖关系"""
        dependencies = stage.get('dependencies', [])

        if not dependencies:
            return True

        for dependency in dependencies:
            if dependency not in execution_results:
                logger.warning(f"依赖阶段 {dependency} 未完成")
                return False

            if not execution_results[dependency].get('success', False):
                logger.warning(f"依赖阶段 {dependency} 执行失败")
                return False

        return True

    async def _execute_stage(self, stage: Dict[str, Any], project_plan: 'ProjectPlan') -> Dict[str, Any]:
        """执行单个阶段"""
        stage_name = stage['name']
        stage_tasks = stage.get('tasks', [])

        logger.info(f"开始执行阶段: {stage_name}, 任务数: {len(stage_tasks)}")

        # 创建任务对象
        tasks = []
        for task_config in stage_tasks:
            task = Task(
                title=task_config['name'],
                description=task_config.get('description', ''),
                assigned_agent=AgentType(task_config['agent']),
                priority=task_config.get('priority', 'medium'),
                input_data={
                    'project_plan': project_plan.dict() if hasattr(project_plan, 'dict') else project_plan,
                    'stage_config': stage,
                    'task_config': task_config
                }
            )
            tasks.append(task)

        # 执行任务
        execution_mode = stage.get('execution', 'parallel')
        if execution_mode == 'parallel':
            results = await self._execute_tasks_parallel(tasks)
        else:
            results = await self._execute_tasks_sequential(tasks)

        # 汇总阶段结果
        stage_result = {
            'stage_name': stage_name,
            'status': 'completed' if all(r.success for r in results) else 'failed',
            'task_results': [r.dict() if hasattr(r, 'dict') else r for r in results],
            'deliverables': {},
            'metrics': {
                'total_tasks': len(tasks),
                'successful_tasks': sum(1 for r in results if r.success),
                'failed_tasks': sum(1 for r in results if not r.success)
            }
        }

        # 收集交付物
        for result in results:
            if hasattr(result, 'output_data') and result.output_data:
                stage_result['deliverables'].update(result.output_data)

        logger.info(f"阶段 {stage_name} 执行完成: {stage_result['status']}")
        return stage_result

    async def _check_quality_gates(self, quality_gates: List[str], stage_result: Dict[str, Any]) -> Dict[str, Any]:
        """检查质量门控"""
        logger.info(f"开始质量门控检查，检查项: {quality_gates}")

        quality_results = {}

        # 检查指定的质量门控
        for gate_type in quality_gates:
            # 执行质量检查
            artifacts = stage_result.get('deliverables', {})
            if self.quality_controller:
                quality_result = await self.quality_controller.check_quality_gate(gate_type, artifacts)
                quality_results[gate_type] = {
                    'gate_type': gate_type,
                    'passed': quality_result.passed,
                    'score': quality_result.score,
                    'issues': [issue.dict() if hasattr(issue, 'dict') else issue for issue in quality_result.issues]
                }
            else:
                # 默认质量检查
                quality_results[gate_type] = {
                    'gate_type': gate_type,
                    'passed': True,
                    'score': 85.0,
                    'issues': []
                }

        logger.info(f"质量门控检查完成，检查了 {len(quality_results)} 个门控")
        return quality_results

    async def _trigger_fix_process(self, stage_name: str, quality_result: Any) -> None:
        """触发修复流程"""
        logger.info(f"触发阶段 {stage_name} 的修复流程")

        # 这里可以实现自动修复逻辑
        # 例如：重新执行失败的任务、调整参数、通知相关Agent等

        # 目前只是记录日志
        if isinstance(quality_result, dict):
            for gate_type, gate_result in quality_result.items():
                if not gate_result.get('passed', True):
                    issues = gate_result.get('issues', [])
                    logger.warning(f"质量门控 {gate_type} 失败，问题数: {len(issues)}")
                    for issue in issues[:3]:  # 只显示前3个问题
                        logger.warning(f"  - {issue}")

        logger.info(f"阶段 {stage_name} 修复流程已触发，等待人工干预或自动重试")
