"""
文件操作工具
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional


def ensure_directory(path: str) -> Path:
    """
    确保目录存在
    
    Args:
        path: 目录路径
        
    Returns:
        Path对象
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def save_text_file(file_path: str, content: str, encoding: str = 'utf-8') -> bool:
    """
    保存文本文件
    
    Args:
        file_path: 文件路径
        content: 文件内容
        encoding: 编码格式
        
    Returns:
        是否保存成功
    """
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding=encoding) as f:
            f.write(content)
        
        return True
    except Exception:
        return False


def load_text_file(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
    """
    加载文本文件
    
    Args:
        file_path: 文件路径
        encoding: 编码格式
        
    Returns:
        文件内容，失败时返回None
    """
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except Exception:
        return None


def save_json_file(file_path: str, data: Dict[str, Any], indent: int = 2) -> bool:
    """
    保存JSON文件
    
    Args:
        file_path: 文件路径
        data: 数据字典
        indent: 缩进空格数
        
    Returns:
        是否保存成功
    """
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        
        return True
    except Exception:
        return False


def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    加载JSON文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        数据字典，失败时返回None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def get_file_size(file_path: str) -> int:
    """
    获取文件大小
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件大小（字节），失败时返回-1
    """
    try:
        return os.path.getsize(file_path)
    except Exception:
        return -1


def list_files(directory: str, pattern: str = "*", recursive: bool = False) -> list:
    """
    列出目录中的文件
    
    Args:
        directory: 目录路径
        pattern: 文件模式
        recursive: 是否递归搜索
        
    Returns:
        文件路径列表
    """
    try:
        dir_path = Path(directory)
        if not dir_path.exists():
            return []
        
        if recursive:
            return [str(p) for p in dir_path.rglob(pattern) if p.is_file()]
        else:
            return [str(p) for p in dir_path.glob(pattern) if p.is_file()]
    except Exception:
        return []
