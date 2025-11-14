"""
验证工具
"""

import re
from typing import Dict, List, Any, Tuple


def validate_project_requirements(requirements: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    验证项目需求
    
    Args:
        requirements: 项目需求字典
        
    Returns:
        (是否有效, 错误信息列表)
    """
    errors = []
    
    # 检查必需字段
    required_fields = ['title', 'description']
    for field in required_fields:
        if field not in requirements:
            errors.append(f"缺少必需字段: {field}")
        elif not requirements[field] or not str(requirements[field]).strip():
            errors.append(f"字段 {field} 不能为空")
    
    # 验证标题长度
    if 'title' in requirements:
        title = str(requirements['title']).strip()
        if len(title) < 3:
            errors.append("项目标题至少需要3个字符")
        elif len(title) > 100:
            errors.append("项目标题不能超过100个字符")
    
    # 验证描述长度
    if 'description' in requirements:
        description = str(requirements['description']).strip()
        if len(description) < 10:
            errors.append("项目描述至少需要10个字符")
        elif len(description) > 5000:
            errors.append("项目描述不能超过5000个字符")
    
    # 验证功能列表
    if 'features' in requirements:
        features = requirements['features']
        if not isinstance(features, list):
            errors.append("功能列表必须是数组格式")
        elif len(features) > 50:
            errors.append("功能列表不能超过50项")
        else:
            for i, feature in enumerate(features):
                if not feature or not str(feature).strip():
                    errors.append(f"功能项 {i+1} 不能为空")
    
    # 验证技术栈
    if 'tech_stack' in requirements:
        tech_stack = requirements['tech_stack']
        if tech_stack is not None and not isinstance(tech_stack, list):
            errors.append("技术栈必须是数组格式")
        elif isinstance(tech_stack, list) and len(tech_stack) > 20:
            errors.append("技术栈不能超过20项")
    
    return len(errors) == 0, errors


def validate_code_files(code_files: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    验证代码文件
    
    Args:
        code_files: 代码文件字典 {文件路径: 文件内容}
        
    Returns:
        (是否有效, 错误信息列表)
    """
    errors = []
    
    if not isinstance(code_files, dict):
        errors.append("代码文件必须是字典格式")
        return False, errors
    
    if len(code_files) == 0:
        errors.append("至少需要一个代码文件")
        return False, errors
    
    # 验证文件路径和内容
    for file_path, content in code_files.items():
        # 验证文件路径
        if not file_path or not file_path.strip():
            errors.append("文件路径不能为空")
            continue
        
        # 检查路径安全性
        if '..' in file_path or file_path.startswith('/'):
            errors.append(f"不安全的文件路径: {file_path}")
            continue
        
        # 验证文件扩展名
        if not _is_valid_file_extension(file_path):
            errors.append(f"不支持的文件类型: {file_path}")
            continue
        
        # 验证文件内容
        if not isinstance(content, str):
            errors.append(f"文件内容必须是字符串: {file_path}")
            continue
        
        if len(content.strip()) == 0:
            errors.append(f"文件内容不能为空: {file_path}")
            continue
        
        # 检查文件大小（限制为1MB）
        if len(content.encode('utf-8')) > 1024 * 1024:
            errors.append(f"文件过大 (>1MB): {file_path}")
            continue
    
    return len(errors) == 0, errors


def validate_agent_type(agent_type: str) -> bool:
    """
    验证Agent类型
    
    Args:
        agent_type: Agent类型字符串
        
    Returns:
        是否有效
    """
    valid_types = [
        'project_manager',
        'architect', 
        'developer',
        'tester',
        'reviewer'
    ]
    return agent_type in valid_types


def validate_task_priority(priority: str) -> bool:
    """
    验证任务优先级
    
    Args:
        priority: 优先级字符串
        
    Returns:
        是否有效
    """
    valid_priorities = ['low', 'medium', 'high', 'critical']
    return priority.lower() in valid_priorities


def validate_email(email: str) -> bool:
    """
    验证邮箱地址
    
    Args:
        email: 邮箱地址
        
    Returns:
        是否有效
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """
    验证URL
    
    Args:
        url: URL字符串
        
    Returns:
        是否有效
    """
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))


def _is_valid_file_extension(file_path: str) -> bool:
    """
    检查文件扩展名是否有效
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否有效
    """
    valid_extensions = {
        # 代码文件
        '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.cs', '.php',
        '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.clj', '.hs',
        
        # Web文件
        '.html', '.htm', '.css', '.scss', '.sass', '.less',
        '.jsx', '.tsx', '.vue', '.svelte',
        
        # 配置文件
        '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
        '.xml', '.properties', '.env',
        
        # 文档文件
        '.md', '.rst', '.txt', '.doc', '.docx',
        
        # 数据文件
        '.sql', '.csv', '.tsv',
        
        # 脚本文件
        '.sh', '.bat', '.ps1', '.fish',
        
        # 其他
        '.dockerfile', '.gitignore', '.gitattributes'
    }
    
    # 获取文件扩展名
    ext = '.' + file_path.split('.')[-1].lower() if '.' in file_path else ''
    
    # 特殊文件名处理
    special_files = {
        'dockerfile', 'makefile', 'rakefile', 'gemfile', 
        'requirements.txt', 'package.json', 'composer.json',
        'cargo.toml', 'go.mod', 'pom.xml'
    }
    
    filename = file_path.lower().split('/')[-1]
    
    return ext in valid_extensions or filename in special_files
