"""
UI设计Agent实现
"""

import json
import logging
from typing import Dict, Any, List

from .base_agent import BaseAgent
from ..models.task import Task, AgentType
from ..api.claude_client import ClaudeAPIClient

logger = logging.getLogger(__name__)


class UIDesignAgent(BaseAgent):
    """UI设计Agent"""
    
    def __init__(self, name: str, api_client: ClaudeAPIClient):
        super().__init__(
            name=name,
            agent_type=AgentType.UI_DESIGN,
            api_client=api_client
        )
    
    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示"""
        return """你是一个专业的UI/UX设计师，专门负责用户界面和用户体验设计。

你的专业技能包括：
1. 用户体验设计（UX）：用户研究、信息架构、用户流程
2. 用户界面设计（UI）：视觉设计、交互设计、原型设计
3. 设计系统：组件库、设计规范、品牌一致性
4. 响应式设计：移动端适配、多屏幕适配
5. 可访问性设计：无障碍设计、包容性设计
6. 设计工具：Figma、Sketch、Adobe XD
7. 前端协作：设计到开发的交付

请根据项目需求，创建完整的UI设计方案，包括：
- 设计系统和规范
- 页面布局和组件设计
- 交互流程和用户体验
- 响应式设计方案
- 设计资源和素材

返回格式为JSON，包含以下字段：
- design_system: 设计系统规范
- layouts: 页面布局设计
- components: 组件设计
- interactions: 交互设计
- assets: 设计资源
- documentation: 设计文档

确保设计美观、实用、符合用户体验最佳实践。"""

    def build_prompt(self, task: Task) -> str:
        """构建UI设计任务提示"""
        project_plan = task.input_data.get('project_plan', {})
        agent_context = task.input_data.get('agent_context', {})
        global_context = task.input_data.get('global_context', {})
        
        # 提取相关信息
        requirements = global_context.get('requirements', '')
        project_analysis = project_plan.get('project_analysis', {})
        tech_stack = project_analysis.get('tech_stack', {})
        
        context = self.get_context_summary()
        
        prompt = f"""
作为UI/UX设计师，请根据以下信息设计用户界面：

## 项目需求
{requirements}

## 项目分析
{json.dumps(project_analysis, indent=2, ensure_ascii=False) if project_analysis else '暂无项目分析'}

## 技术栈
{json.dumps(tech_stack, indent=2, ensure_ascii=False) if tech_stack else '暂无技术栈信息'}

## 设计上下文
{context}

请完成以下UI设计任务：

### 1. 设计系统规范
- 色彩系统（主色、辅助色、语义色）
- 字体系统（字体族、字号、行高）
- 间距系统（边距、内距、组件间距）
- 圆角和阴影规范
- 图标风格和规范

### 2. 页面布局设计
- 整体布局结构
- 导航设计（顶部导航、侧边导航）
- 页面模板（列表页、详情页、表单页）
- 响应式布局方案

### 3. 组件设计
- 基础组件（按钮、输入框、选择器）
- 数据展示组件（表格、卡片、列表）
- 反馈组件（弹窗、提示、加载）
- 导航组件（面包屑、分页、标签）

### 4. 交互设计
- 用户操作流程
- 状态变化设计
- 动效和过渡
- 错误处理和反馈

### 5. 响应式设计
- 断点设置
- 移动端适配
- 平板端适配
- 桌面端优化

### 6. 可访问性设计
- 颜色对比度
- 键盘导航
- 屏幕阅读器支持
- 多语言支持

请以JSON格式返回完整的UI设计方案：

```json
{{
  "design_system": {{
    "colors": {{
      "primary": "#1890ff",
      "secondary": "#722ed1",
      "success": "#52c41a",
      "warning": "#faad14",
      "error": "#f5222d",
      "text": {{
        "primary": "#262626",
        "secondary": "#595959",
        "disabled": "#bfbfbf"
      }},
      "background": {{
        "primary": "#ffffff",
        "secondary": "#fafafa",
        "disabled": "#f5f5f5"
      }}
    }},
    "typography": {{
      "font_family": "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
      "font_sizes": {{
        "xs": "12px",
        "sm": "14px",
        "md": "16px",
        "lg": "18px",
        "xl": "20px",
        "2xl": "24px",
        "3xl": "32px"
      }},
      "line_heights": {{
        "tight": "1.2",
        "normal": "1.5",
        "relaxed": "1.8"
      }}
    }},
    "spacing": {{
      "xs": "4px",
      "sm": "8px",
      "md": "16px",
      "lg": "24px",
      "xl": "32px",
      "2xl": "48px"
    }},
    "border_radius": {{
      "sm": "4px",
      "md": "8px",
      "lg": "12px",
      "full": "50%"
    }},
    "shadows": {{
      "sm": "0 1px 3px rgba(0,0,0,0.1)",
      "md": "0 4px 6px rgba(0,0,0,0.1)",
      "lg": "0 10px 15px rgba(0,0,0,0.1)"
    }}
  }},
  "layouts": {{
    "main_layout": {{
      "description": "主布局结构",
      "structure": "header + sidebar + content + footer",
      "breakpoints": {{
        "mobile": "768px",
        "tablet": "1024px",
        "desktop": "1200px"
      }}
    }},
    "page_templates": {{
      "list_page": "列表页模板设计",
      "detail_page": "详情页模板设计",
      "form_page": "表单页模板设计"
    }}
  }},
  "components": {{
    "button": {{
      "variants": ["primary", "secondary", "outline", "text"],
      "sizes": ["small", "medium", "large"],
      "states": ["default", "hover", "active", "disabled"]
    }},
    "input": {{
      "types": ["text", "password", "email", "number"],
      "states": ["default", "focus", "error", "disabled"],
      "sizes": ["small", "medium", "large"]
    }},
    "card": {{
      "variants": ["default", "bordered", "hoverable"],
      "sections": ["header", "body", "footer"]
    }}
  }},
  "interactions": {{
    "navigation": {{
      "menu_behavior": "展开/收起动画",
      "page_transitions": "淡入淡出效果",
      "loading_states": "骨架屏和加载动画"
    }},
    "forms": {{
      "validation": "实时验证反馈",
      "submission": "提交状态和结果反馈",
      "auto_save": "自动保存提示"
    }}
  }},
  "assets": {{
    "icons": {{
      "style": "outline",
      "library": "heroicons",
      "custom_icons": []
    }},
    "images": {{
      "placeholders": "占位图规范",
      "optimization": "图片压缩和格式"
    }},
    "illustrations": {{
      "empty_states": "空状态插图",
      "error_pages": "错误页面插图"
    }}
  }},
  "documentation": {{
    "design_guide": "设计指南文档",
    "component_library": "组件库文档",
    "style_guide": "样式指南",
    "accessibility_guide": "可访问性指南"
  }}
}}
```

确保设计现代、美观、易用、符合当前设计趋势。
        """
        
        return prompt.strip()

    def parse_response(self, response: str, task: Task) -> Dict[str, Any]:
        """解析UI设计响应"""
        try:
            result = self._extract_json_from_response(response)
            
            # 验证必需字段
            required_fields = ['design_system', 'layouts', 'components']
            for field in required_fields:
                if field not in result:
                    logger.warning(f"UI设计响应中缺少字段: {field}")
                    result[field] = {}
            
            # 确保有基本的设计系统
            if not result['design_system']:
                result['design_system'] = {
                    'colors': {
                        'primary': '#1890ff',
                        'secondary': '#722ed1',
                        'text': {'primary': '#262626', 'secondary': '#595959'}
                    },
                    'typography': {
                        'font_family': 'Inter, sans-serif',
                        'font_sizes': {'sm': '14px', 'md': '16px', 'lg': '18px'}
                    },
                    'spacing': {'sm': '8px', 'md': '16px', 'lg': '24px'}
                }
            
            # 确保有基本的组件设计
            if not result['components']:
                result['components'] = {
                    'button': {
                        'variants': ['primary', 'secondary'],
                        'sizes': ['small', 'medium', 'large']
                    },
                    'input': {
                        'types': ['text', 'password', 'email'],
                        'states': ['default', 'focus', 'error']
                    }
                }
            
            # 添加设计统计信息
            result['statistics'] = {
                'color_count': len(result['design_system'].get('colors', {})),
                'component_count': len(result['components']),
                'layout_count': len(result['layouts']),
                'has_design_system': bool(result['design_system']),
                'has_responsive_design': 'breakpoints' in str(result)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"解析UI设计响应失败: {str(e)}")
            return {
                'error': f'响应解析失败: {str(e)}',
                'raw_response': response[:500],
                'design_system': {},
                'layouts': {},
                'components': {}
            }

    def validate_result(self, result: Dict[str, Any], task: Task) -> bool:
        """验证UI设计结果"""
        if "error" in result:
            return False
        
        # 检查是否有设计系统
        design_system = result.get('design_system', {})
        if not design_system:
            logger.error("UI设计结果缺少设计系统")
            return False
        
        # 检查是否有颜色定义
        colors = design_system.get('colors', {})
        if not colors:
            logger.warning("设计系统缺少颜色定义")
        
        # 检查是否有组件设计
        components = result.get('components', {})
        if not components:
            logger.warning("UI设计结果缺少组件设计")
        
        return True

    def get_capabilities(self) -> List[str]:
        """获取Agent能力列表"""
        return [
            "用户体验设计",
            "用户界面设计",
            "设计系统构建",
            "响应式设计",
            "交互设计",
            "原型设计",
            "可访问性设计",
            "品牌设计",
            "图标设计",
            "插画设计",
            "设计规范制定",
            "设计交付"
        ]

    def estimate_effort(self, task_description: str) -> Dict[str, Any]:
        """估算设计工作量"""
        base_hours = 16
        
        # 根据关键词调整工作量
        complexity_keywords = {
            'complex': 2.0,
            'advanced': 1.8,
            'simple': 0.6,
            'basic': 0.7,
            'dashboard': 1.5,
            'admin': 1.3,
            'ecommerce': 1.8,
            'mobile': 1.4,
            'responsive': 1.3,
            'design system': 1.6,
            'branding': 1.5,
            'illustration': 1.7
        }
        
        multiplier = 1.0
        for keyword, factor in complexity_keywords.items():
            if keyword in task_description.lower():
                multiplier = max(multiplier, factor)
        
        estimated_hours = base_hours * multiplier
        
        return {
            'estimated_hours': estimated_hours,
            'complexity_level': 'high' if multiplier > 1.5 else 'medium' if multiplier > 1.0 else 'low',
            'key_deliverables': self._extract_deliverables_from_description(task_description),
            'design_style': self._recommend_design_style(task_description)
        }
    
    def _extract_deliverables_from_description(self, description: str) -> List[str]:
        """从描述中提取设计交付物"""
        deliverables = []
        
        deliverable_keywords = {
            'wireframe': '线框图',
            'prototype': '原型设计',
            'mockup': '视觉稿',
            'design system': '设计系统',
            'component': '组件库',
            'icon': '图标设计',
            'logo': 'Logo设计',
            'branding': '品牌设计',
            'illustration': '插画设计',
            'animation': '动效设计',
            'responsive': '响应式设计',
            'mobile': '移动端设计'
        }
        
        description_lower = description.lower()
        for keyword, deliverable in deliverable_keywords.items():
            if keyword in description_lower:
                deliverables.append(deliverable)
        
        return deliverables
    
    def _recommend_design_style(self, description: str) -> Dict[str, str]:
        """推荐设计风格"""
        description_lower = description.lower()
        
        # 设计风格推荐
        if 'modern' in description_lower or 'minimal' in description_lower:
            style = 'Modern Minimal'
        elif 'corporate' in description_lower or 'business' in description_lower:
            style = 'Corporate'
        elif 'creative' in description_lower or 'artistic' in description_lower:
            style = 'Creative'
        elif 'tech' in description_lower or 'startup' in description_lower:
            style = 'Tech/Startup'
        else:
            style = 'Clean & Professional'
        
        # 颜色方案推荐
        if 'blue' in description_lower:
            color_scheme = 'Blue-based'
        elif 'green' in description_lower:
            color_scheme = 'Green-based'
        elif 'dark' in description_lower:
            color_scheme = 'Dark Theme'
        else:
            color_scheme = 'Neutral with Accent'
        
        return {
            'design_style': style,
            'color_scheme': color_scheme,
            'typography': 'Sans-serif',
            'layout': 'Grid-based',
            'interaction': 'Subtle animations'
        }

    def generate_css_variables(self, design_system: Dict[str, Any]) -> str:
        """生成CSS变量"""
        css_lines = [":root {"]
        
        # 颜色变量
        colors = design_system.get('colors', {})
        if colors:
            css_lines.append("  /* Colors */")
            for color_name, color_value in colors.items():
                if isinstance(color_value, dict):
                    for sub_name, sub_value in color_value.items():
                        css_lines.append(f"  --color-{color_name}-{sub_name}: {sub_value};")
                else:
                    css_lines.append(f"  --color-{color_name}: {color_value};")
        
        # 字体变量
        typography = design_system.get('typography', {})
        if typography:
            css_lines.append("\n  /* Typography */")
            if 'font_family' in typography:
                css_lines.append(f"  --font-family: {typography['font_family']};")
            
            font_sizes = typography.get('font_sizes', {})
            for size_name, size_value in font_sizes.items():
                css_lines.append(f"  --font-size-{size_name}: {size_value};")
        
        # 间距变量
        spacing = design_system.get('spacing', {})
        if spacing:
            css_lines.append("\n  /* Spacing */")
            for space_name, space_value in spacing.items():
                css_lines.append(f"  --spacing-{space_name}: {space_value};")
        
        # 圆角变量
        border_radius = design_system.get('border_radius', {})
        if border_radius:
            css_lines.append("\n  /* Border Radius */")
            for radius_name, radius_value in border_radius.items():
                css_lines.append(f"  --border-radius-{radius_name}: {radius_value};")
        
        # 阴影变量
        shadows = design_system.get('shadows', {})
        if shadows:
            css_lines.append("\n  /* Shadows */")
            for shadow_name, shadow_value in shadows.items():
                css_lines.append(f"  --shadow-{shadow_name}: {shadow_value};")
        
        css_lines.append("}")
        
        return "\n".join(css_lines)
