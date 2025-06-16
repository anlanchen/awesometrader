from pathlib import Path
from typing import Optional

class Utils:
    """项目工具类，提供通用的路径和目录管理功能"""
    
    @staticmethod
    def get_project_root(marker_files: Optional[list] = None) -> Path:
        """
        获取项目根目录
        
        :param marker_files: 标记文件列表，用于识别项目根目录。默认为常见的项目标记文件
        :return: 项目根目录的Path对象
        """
        # 常见的项目根目录标记文件
        marker_files = [
            'pyproject.toml',
            '.env',
            'uv.lock'
        ]
        
        # 从当前文件开始向上搜索
        current_path = Path(__file__).resolve()
        
        # 向上遍历目录树
        for parent in [current_path] + list(current_path.parents):
            # 检查是否存在任何标记文件
            for marker in marker_files:
                if (parent / marker).exists():
                    return parent
        
        # 如果没有找到标记文件，返回当前文件的父目录的父目录的父目录
        # 这是基于项目结构 core/utils/utils.py 的回退方案
        return current_path.parent.parent.parent

    @staticmethod
    def get_cache_dir() -> Path:
        """
        获取项目缓存目录
        
        :return: 缓存目录的Path对象
        """
        cache_dir = Utils.get_project_root() / "caches"
        cache_dir.mkdir(exist_ok=True)
        return cache_dir
