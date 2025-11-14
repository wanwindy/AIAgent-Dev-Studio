"""
前端开发Agent实现
"""

import json
import logging
from typing import Dict, Any, List

from .base_agent import BaseAgent
from ..models.task import Task, AgentType
from ..api.claude_client import ClaudeAPIClient

logger = logging.getLogger(__name__)


class FrontendAgent(BaseAgent):
    """前端开发Agent"""
    
    def __init__(self, name: str, api_client: ClaudeAPIClient):
        super().__init__(
            name=name,
            agent_type=AgentType.FRONTEND,
            api_client=api_client
        )
    
    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示"""
        return """你是一个资深的前端开发工程师，专门负责Web应用的前端开发。

你的专业技能包括：
1. 现代前端框架：React、Vue.js、Angular
2. 前端技术栈：HTML5、CSS3、JavaScript/TypeScript
3. 状态管理：Redux、Vuex、MobX
4. 构建工具：Webpack、Vite、Parcel
5. UI组件库：Ant Design、Material-UI、Element UI
6. 响应式设计和移动端适配
7. 前端性能优化和SEO
8. 前端测试：Jest、Cypress、Testing Library

请根据项目需求和UI设计，生成高质量的前端代码，包括：
- 组件结构和实现
- 样式文件（CSS/SCSS/Less）
- 路由配置
- 状态管理
- API调用逻辑
- 构建配置文件

返回格式为JSON，包含以下字段：
- components: 组件代码文件
- styles: 样式文件
- config: 配置文件
- package_json: 依赖配置
- documentation: 开发文档

确保代码遵循最佳实践，具有良好的可读性和可维护性。"""

    def build_prompt(self, task: Task) -> str:
        """构建前端开发任务提示"""
        project_plan = task.input_data.get('project_plan', {})
        agent_context = task.input_data.get('agent_context', {})
        global_context = task.input_data.get('global_context', {})
        
        # 提取相关信息
        requirements = global_context.get('requirements', '')
        ui_design = global_context.get('artifact_ui_design', {})
        api_design = global_context.get('artifact_api_design', {})
        tech_stack = project_plan.get('project_analysis', {}).get('tech_stack', {})
        
        context = self.get_context_summary()
        
        prompt = f"""
作为前端开发工程师，请根据以下信息开发前端应用：

## 项目需求
{requirements}

## UI设计规范
{json.dumps(ui_design, indent=2, ensure_ascii=False) if ui_design else '暂无UI设计，请根据需求创建简洁美观的界面'}

## API接口设计
{json.dumps(api_design, indent=2, ensure_ascii=False) if api_design else '暂无API设计，请根据需求设计前端数据交互'}

## 技术栈要求
{json.dumps(tech_stack, indent=2, ensure_ascii=False) if tech_stack else '请选择合适的前端技术栈'}

## 开发上下文
{context}

请完成以下前端开发任务：

### 1. 技术选型和架构设计
- 选择合适的前端框架（React/Vue/Angular）
- 确定状态管理方案
- 设计组件架构和目录结构
- 选择UI组件库和样式方案

### 2. 核心组件开发
- 页面组件（路由页面）
- 业务组件（功能模块）
- 通用组件（按钮、表单、弹窗等）
- 布局组件（头部、侧边栏、底部等）

### 3. 样式和主题
- 全局样式和CSS变量
- 组件样式（CSS Modules/Styled Components）
- 响应式设计
- 主题配置

### 4. 状态管理和数据流
- 全局状态管理
- 组件间通信
- API数据获取和缓存
- 表单状态管理

### 5. 路由和导航
- 路由配置
- 导航组件
- 权限控制
- 懒加载

### 6. 工具配置
- 构建配置（Webpack/Vite）
- 开发服务器配置
- 代码规范配置（ESLint/Prettier）
- 环境变量配置

### 7. 性能优化
- 代码分割
- 懒加载
- 图片优化
- 缓存策略

请以JSON格式返回完整的前端代码和配置：

```json
{{
  "components": {{
    "App.jsx": "主应用组件代码",
    "components/Header.jsx": "头部组件代码",
    "pages/Home.jsx": "首页组件代码",
    "...": "其他组件文件"
  }},
  "styles": {{
    "index.css": "全局样式",
    "components/Header.module.css": "组件样式",
    "...": "其他样式文件"
  }},
  "config": {{
    "webpack.config.js": "构建配置",
    "vite.config.js": "Vite配置",
    ".eslintrc.js": "ESLint配置",
    "...": "其他配置文件"
  }},
  "package_json": {{
    "name": "项目名称",
    "dependencies": {{}},
    "devDependencies": {{}},
    "scripts": {{}}
  }},
  "documentation": {{
    "README.md": "项目说明文档",
    "DEVELOPMENT.md": "开发指南",
    "DEPLOYMENT.md": "部署说明"
  }}
}}
```

确保代码质量高、结构清晰、注释完整。
        """
        
        return prompt.strip()

    def parse_response(self, response: str, task: Task) -> Dict[str, Any]:
        """解析前端开发响应"""
        try:
            result = self._extract_json_from_response(response)
            
            # 验证必需字段
            required_fields = ['components', 'styles', 'config', 'package_json']
            for field in required_fields:
                if field not in result:
                    logger.warning(f"前端开发响应中缺少字段: {field}")
                    result[field] = {}
            
            # 确保有基本的组件文件
            if not result['components']:
                result['components'] = {
                    'App.jsx': '// 主应用组件\nimport React from "react";\n\nfunction App() {\n  return (\n    <div className="App">\n      <h1>Hello World</h1>\n    </div>\n  );\n}\n\nexport default App;'
                }
            
            # 确保有package.json
            if not result['package_json']:
                result['package_json'] = {
                    "name": "frontend-app",
                    "version": "1.0.0",
                    "dependencies": {
                        "react": "^18.0.0",
                        "react-dom": "^18.0.0"
                    },
                    "devDependencies": {
                        "@vitejs/plugin-react": "^4.0.0",
                        "vite": "^4.0.0"
                    },
                    "scripts": {
                        "dev": "vite",
                        "build": "vite build",
                        "preview": "vite preview"
                    }
                }
            
            # 添加文件统计信息
            result['statistics'] = {
                'component_count': len(result['components']),
                'style_count': len(result['styles']),
                'config_count': len(result['config']),
                'total_files': len(result['components']) + len(result['styles']) + len(result['config'])
            }
            
            return result
            
        except Exception as e:
            logger.error(f"解析前端开发响应失败: {str(e)}")
            return {
                'error': f'响应解析失败: {str(e)}',
                'raw_response': response[:500],
                'components': {},
                'styles': {},
                'config': {},
                'package_json': {}
            }

    def validate_result(self, result: Dict[str, Any], task: Task) -> bool:
        """验证前端开发结果"""
        if "error" in result:
            return False
        
        # 检查是否有基本的组件文件
        components = result.get('components', {})
        if not components:
            logger.error("前端开发结果缺少组件文件")
            return False
        
        # 检查是否有主应用组件
        has_main_component = any(
            'app' in filename.lower() or 'main' in filename.lower() or 'index' in filename.lower()
            for filename in components.keys()
        )
        
        if not has_main_component:
            logger.warning("前端开发结果缺少主应用组件")
        
        # 检查package.json
        package_json = result.get('package_json', {})
        if not package_json or 'dependencies' not in package_json:
            logger.warning("前端开发结果缺少有效的package.json")
        
        return True

    def get_capabilities(self) -> List[str]:
        """获取Agent能力列表"""
        return [
            "React开发",
            "Vue.js开发", 
            "Angular开发",
            "TypeScript开发",
            "响应式设计",
            "组件化开发",
            "状态管理",
            "前端路由",
            "API集成",
            "性能优化",
            "构建配置",
            "前端测试"
        ]

    def estimate_effort(self, task_description: str) -> Dict[str, Any]:
        """估算开发工作量"""
        # 简单的工作量估算逻辑
        base_hours = 8
        
        # 根据关键词调整工作量
        complexity_keywords = {
            'complex': 2.0,
            'advanced': 1.8,
            'simple': 0.5,
            'basic': 0.6,
            'dashboard': 1.5,
            'admin': 1.8,
            'ecommerce': 2.2,
            'social': 1.9,
            'mobile': 1.3,
            'responsive': 1.2
        }
        
        multiplier = 1.0
        for keyword, factor in complexity_keywords.items():
            if keyword in task_description.lower():
                multiplier = max(multiplier, factor)
        
        estimated_hours = base_hours * multiplier
        
        return {
            'estimated_hours': estimated_hours,
            'complexity_level': 'high' if multiplier > 1.5 else 'medium' if multiplier > 1.0 else 'low',
            'key_components': self._extract_components_from_description(task_description),
            'recommended_tech_stack': self._recommend_tech_stack(task_description)
        }
    
    def _extract_components_from_description(self, description: str) -> List[str]:
        """从描述中提取组件需求"""
        components = []
        
        component_keywords = {
            'login': '登录组件',
            'register': '注册组件',
            'dashboard': '仪表板组件',
            'table': '表格组件',
            'form': '表单组件',
            'chart': '图表组件',
            'navigation': '导航组件',
            'sidebar': '侧边栏组件',
            'header': '头部组件',
            'footer': '底部组件',
            'modal': '弹窗组件',
            'search': '搜索组件',
            'pagination': '分页组件'
        }
        
        description_lower = description.lower()
        for keyword, component in component_keywords.items():
            if keyword in description_lower:
                components.append(component)
        
        return components
    
    def _recommend_tech_stack(self, description: str) -> Dict[str, str]:
        """推荐技术栈"""
        description_lower = description.lower()
        
        # 框架推荐
        if 'vue' in description_lower:
            framework = 'Vue.js'
        elif 'angular' in description_lower:
            framework = 'Angular'
        else:
            framework = 'React'  # 默认推荐React
        
        # UI库推荐
        if 'admin' in description_lower or 'dashboard' in description_lower:
            ui_library = 'Ant Design'
        elif 'material' in description_lower:
            ui_library = 'Material-UI'
        else:
            ui_library = 'Ant Design'
        
        # 状态管理推荐
        if framework == 'React':
            state_management = 'Redux Toolkit'
        elif framework == 'Vue.js':
            state_management = 'Vuex'
        else:
            state_management = 'NgRx'
        
        return {
            'framework': framework,
            'ui_library': ui_library,
            'state_management': state_management,
            'build_tool': 'Vite',
            'language': 'TypeScript'
        }
