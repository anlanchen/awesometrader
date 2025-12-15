#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理模块
"""

from pathlib import Path
from typing import Dict


class Config:
    """应用配置"""
    
    # 项目根目录
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    
    # 缓存目录
    CACHE_DIR = PROJECT_ROOT / "caches"
    
    # 账户数据文件
    ACCOUNT_CSV_PATH = CACHE_DIR / "account.csv"
    
    # API 配置
    API_PREFIX = "/api"
    API_TITLE = "AwesomeTrader Analytics API"
    API_VERSION = "1.0.0"
    
    # 基准指数配置
    # 注意: yfinance 对某些指数支持不完整，使用 ETF 作为替代
    BENCHMARK_SYMBOLS: Dict[str, str] = {
        "sp500": "^GSPC",        # 标普500
        "nasdaq100": "^NDX",     # 纳斯达克100
        "csi300": "000300.SS",   # 沪深300
        "a500": "510500.SS",     # 中证500ETF (作为A500替代)
        "hstech": "3032.HK",     # 恒生科技ETF (^HSTECH 在yfinance不可用)
    }
    
    # 时间周期配置 (period_code -> days, None 表示特殊处理)
    PERIOD_DAYS: Dict[str, int | None] = {
        "7d": 7,
        "1m": 30,
        "6m": 180,
        "1y": 365,
        "all": None,   # 全部数据
        "mtd": None,   # 本月至今
        "ytd": None,   # 本年至今
    }
    
    # 无风险利率 (年化，用于夏普比率等计算)
    RISK_FREE_RATE = 0.03  # 3%


config = Config()

