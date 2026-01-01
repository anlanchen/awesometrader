#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理模块
"""

import os
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
    
    # 基准指数配置 - 全部使用 akshare 数据源
    AKSHARE_BENCHMARKS: Dict[str, Dict] = {
        # 美股指数 (新浪财经)
        "sp500": {"symbol": ".INX", "type": "us_index", "name": "标普500"},
        "nasdaq100": {"symbol": ".NDX", "type": "us_index", "name": "纳斯达克100"},
        # A股指数
        "csi300": {"symbol": "000300", "type": "a_index", "name": "沪深300"},
        "a500": {"symbol": "000510", "type": "a_index", "name": "中证A500"},
        # 港股指数
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
    
    # ============== 认证配置 ==============
    # JWT 配置（必须通过环境变量设置）
    SECRET_KEY = os.environ["SECRET_KEY"]  # JWT 签名密钥，必须设置
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 天
    
    # 用户配置（必须通过环境变量设置）
    # 密码哈希使用 bcrypt，可以通过命令生成: python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('your-password'))"
    DEFAULT_USERNAME = os.environ["ADMIN_USERNAME"]  # 管理员用户名，必须设置
    DEFAULT_PASSWORD_HASH = os.environ["ADMIN_PASSWORD_HASH"]  # 管理员密码哈希，必须设置
    
    # 是否启用 API 认证保护 (默认启用)
    AUTH_ENABLED = os.getenv("AUTH_ENABLED", "true").lower() in ("true", "1", "yes")


config = Config()

