"""
AwesomeTrader Core Module
量化交易系统核心模块

提供以下功能模块：
- datainterface: 数据接口，提供数据读取、保存、验证等功能
- collector: 数据收集器，基于长桥OpenAPI获取实时和历史数据
- utils: 通用工具类，提供路径管理和项目配置功能
"""

# 导入主要的数据和工具模块
from .datainterface import DataInterface
from .collector import Collector
from .trader import Trader
from .messager import Messager
from .utils import Utils

__version__ = "0.1.0"
__all__ = [
    'DataInterface', 
    'Collector', 
    'Trader',
    'Utils'
] 