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
    # yfinance 数据源
    BENCHMARK_SYMBOLS: Dict[str, str] = {
        "sp500": "^GSPC",        # 标普500
        "nasdaq100": "^NDX",     # 纳斯达克100
        "btc": "BTC-USD",        # 比特币
        "gold": "GC=F",          # 黄金期货
    }
    
    # akshare 数据源 (中国/港股指数，yfinance 支持不完整)
    AKSHARE_BENCHMARKS: Dict[str, Dict] = {
        "csi300": {"symbol": "000300", "type": "a_index", "name": "沪深300"},
        "a500": {"symbol": "000510", "type": "a_index", "name": "中证A500"},
        "hstech": {"symbol": "HSTECH", "type": "hk_index", "name": "恒生科技"},
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
    RISK_FREE_RATE = 0.036  # 3.6%


config = Config()

