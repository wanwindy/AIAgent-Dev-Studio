# API参考文档

## 核心类和接口

### MultiAgentDevSystem

主系统类，提供完整的项目开发功能。

#### 方法

##### `__init__()`
初始化多Agent开发系统。

##### `async initialize()`
初始化系统组件，包括API客户端、Agent管理器等。

**异常:**
- `Exception`: 系统初始化失败时抛出

##### `async develop_project(title, description, features=None, tech_stack=None, constraints=None)`
开发项目的主要方法。

**参数:**
- `title` (str): 项目标题
- `description` (str): 项目描述
- `features` (list, optional): 功能列表
- `tech_stack` (list, optional): 技术栈
- `constraints` (dict, optional): 约束条件

**返回:**
- `ProjectResult`: 项目开发结果

**示例:**
```python
result = await system.develop_project(
    title="博客系统",
    description="一个简单的博客管理系统",
    features=["文章发布", "评论系统"],
    tech_stack=["Python", "Django"],
    constraints={"complexity": "medium"}
)
```

### AgentManager

Agent管理器，负责管理和调度各个Agent。

#### 方法

##### `__init__(api_client)`
初始化Agent管理器。

**参数:**
- `api_client` (ClaudeAPIClient): Claude API客户端

##### `get_agent(agent_type)`
获取指定类型的Agent。

**参数:**
- `agent_type` (AgentType): Agent类型枚举

**返回:**
- `BaseAgent`: Agent实例

##### `async execute_task(task)`
执行单个任务。

**参数:**
- `task` (Task): 要执行的任务

**返回:**
- `AgentResult`: 执行结果

### ClaudeAPIClient

Claude API客户端，处理与Claude API的交互。

#### 方法

##### `__init__(api_key=None)`
初始化API客户端。

**参数:**
- `api_key` (str, optional): API密钥，默认从配置获取

##### `async generate_response(prompt, system_prompt=None, **kwargs)`
生成AI响应。

**参数:**
- `prompt` (str): 用户提示
- `system_prompt` (str, optional): 系统提示
- `**kwargs`: 其他参数

**返回:**
- `str`: AI生成的响应

**异常:**
- `ClaudeAPIError`: API调用失败时抛出

##### `async generate_response_with_retry(prompt, max_retries=None, **kwargs)`
带重试机制的响应生成。

**参数:**
- `prompt` (str): 用户提示
- `max_retries` (int, optional): 最大重试次数
- `**kwargs`: 其他参数

**返回:**
- `str`: AI生成的响应

## 数据模型

### ProjectRequirements

项目需求模型。

**字段:**
- `title` (str): 项目标题
- `description` (str): 项目描述
- `features` (List[str]): 功能列表
- `tech_stack` (List[str], optional): 技术栈
- `constraints` (Dict[str, Any]): 约束条件
- `timeline` (str, optional): 时间线
- `budget` (float, optional): 预算

### ProjectResult

项目开发结果模型。

**字段:**
- `project_id` (str): 项目ID
- `requirements` (ProjectRequirements): 项目需求
- `tasks` (List[Task]): 任务列表
- `agent_results` (List[AgentResult]): Agent执行结果
- `final_code` (Dict[str, str]): 最终生成的代码
- `test_reports` (List[Dict]): 测试报告
- `review_feedback` (List[Dict]): 审查反馈
- `status` (TaskStatus): 项目状态
- `total_execution_time` (float): 总执行时间
- `total_tokens_used` (int): 总Token使用量

### Task

任务模型。

**字段:**
- `id` (str): 任务ID
- `title` (str): 任务标题
- `description` (str): 任务描述
- `status` (TaskStatus): 任务状态
- `priority` (TaskPriority): 任务优先级
- `assigned_agent` (AgentType): 分配的Agent
- `dependencies` (List[str]): 依赖任务
- `input_data` (Dict): 输入数据
- `output_data` (Dict): 输出数据

### AgentResult

Agent执行结果模型。

**字段:**
- `agent_type` (AgentType): Agent类型
- `task_id` (str): 任务ID
- `success` (bool): 是否成功
- `output` (Dict): 输出结果
- `error` (str, optional): 错误信息
- `execution_time` (float): 执行时间
- `tokens_used` (int): 使用的Token数

## 枚举类型

### AgentType

Agent类型枚举。

**值:**
- `PROJECT_MANAGER`: 项目经理
- `ARCHITECT`: 架构师
- `DEVELOPER`: 开发者
- `TESTER`: 测试员
- `REVIEWER`: 审查员

### TaskStatus

任务状态枚举。

**值:**
- `PENDING`: 待处理
- `IN_PROGRESS`: 进行中
- `COMPLETED`: 已完成
- `FAILED`: 失败
- `CANCELLED`: 已取消

### TaskPriority

任务优先级枚举。

**值:**
- `LOW`: 低优先级
- `MEDIUM`: 中等优先级
- `HIGH`: 高优先级
- `CRITICAL`: 关键优先级

## 扩展功能

### GitIntegration

Git版本控制集成。

#### 方法

##### `create_feature_branch(feature_name)`
创建功能分支。

##### `commit_changes(message, files=None)`
提交更改。

##### `save_generated_code(code_files, project_name)`
保存生成的代码到Git仓库。

### CIIntegration

CI/CD集成。

#### 方法

##### `async run_tests(test_command=None)`
运行测试。

##### `async run_linting(lint_command=None)`
运行代码检查。

##### `async run_full_pipeline()`
运行完整的CI/CD流水线。

### MetricsCollector

指标收集器。

#### 方法

##### `record_api_call(agent_type, duration, tokens_used, success)`
记录API调用指标。

##### `record_task_execution(agent_type, duration, success)`
记录任务执行指标。

##### `get_summary_stats()`
获取汇总统计信息。

## 配置

### Settings

系统配置类。

**字段:**
- `claude_api_key` (str): Claude API密钥
- `claude_model` (str): Claude模型名称
- `claude_max_tokens` (int): 最大Token数
- `log_level` (str): 日志级别
- `max_retries` (int): 最大重试次数
- `results_dir` (str): 结果存储目录
- `git_enabled` (bool): 是否启用Git集成
- `metrics_enabled` (bool): 是否启用指标收集

## 异常类

### ClaudeAPIError

Claude API相关异常。

**继承:** `Exception`

**用途:** API调用失败时抛出

## 使用示例

### 基本使用

```python
import asyncio
from multi_agent_dev import MultiAgentDevSystem

async def main():
    system = MultiAgentDevSystem()
    await system.initialize()
    
    result = await system.develop_project(
        title="示例项目",
        description="这是一个示例项目"
    )
    
    print(f"项目完成: {result.project_id}")

asyncio.run(main())
```

### 自定义Agent

```python
from multi_agent_dev.agents.base_agent import BaseAgent
from multi_agent_dev.models.task import AgentType

class CustomAgent(BaseAgent):
    def __init__(self, name, api_client):
        super().__init__(name, AgentType.DEVELOPER, api_client)
    
    def _get_default_system_prompt(self):
        return "你是一个自定义的开发Agent..."
    
    def build_prompt(self, task):
        return f"请处理任务: {task.description}"
    
    def parse_response(self, response, task):
        return {"result": response}
```

### 监控集成

```python
from multi_agent_dev.extensions.monitoring import metrics_collector

# 记录自定义指标
metrics_collector.record_api_call(
    agent_type="custom",
    duration=1.5,
    tokens_used=100,
    success=True
)

# 获取统计信息
stats = metrics_collector.get_summary_stats()
print(stats)
```
