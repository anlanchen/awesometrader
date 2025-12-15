#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基准指数服务 - 使用 yfinance 获取基准指数数据
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, Optional
from loguru import logger

from ..config import config


class BenchmarkService:
    """基准指数服务"""
    
    def __init__(self):
        """初始化基准指数服务"""
        # 内存缓存
        self._cache: Dict[str, pd.Series] = {}
        self._cache_time: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(hours=1)  # 缓存1小时
        
    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self._cache_time:
            return False
        return datetime.now() - self._cache_time[cache_key] < self._cache_ttl
    
    def get_benchmark_symbol(self, benchmark: str) -> str:
        """
        获取基准指数的 yfinance 符号
        
        :param benchmark: 基准代码 (sp500, nasdaq100, csi300, a500, hstech)
        :return: yfinance 符号
        """
        symbol = config.BENCHMARK_SYMBOLS.get(benchmark.lower())
        if not symbol:
            raise ValueError(f"未知的基准指数: {benchmark}，可选: {list(config.BENCHMARK_SYMBOLS.keys())}")
        return symbol
    
    def get_benchmark_name(self, benchmark: str) -> str:
        """获取基准指数的中文名称"""
        names = {
            "sp500": "标普500",
            "nasdaq100": "纳斯达克100",
            "csi300": "沪深300",
            "a500": "中证500ETF",
            "hstech": "恒生科技ETF",
        }
        return names.get(benchmark.lower(), benchmark)
    
    def fetch_benchmark_data(
        self, 
        benchmark: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> pd.Series:
        """
        获取基准指数收盘价数据
        
        :param benchmark: 基准代码
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 收盘价 Series
        """
        symbol = self.get_benchmark_symbol(benchmark)
        cache_key = f"{symbol}_{start_date.date()}_{end_date.date()}"
        
        # 检查缓存
        if self._is_cache_valid(cache_key) and cache_key in self._cache:
            logger.debug(f"使用缓存数据: {cache_key}")
            return self._cache[cache_key]
        
        try:
            logger.info(f"从 yfinance 获取 {symbol} 数据: {start_date.date()} - {end_date.date()}")
            
            # 扩展开始日期以确保有足够的历史数据
            fetch_start = start_date - timedelta(days=10)
            
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=fetch_start, end=end_date + timedelta(days=1))
            
            if df.empty:
                logger.warning(f"未获取到 {symbol} 的数据")
                return pd.Series(dtype=float)
            
            # 提取收盘价
            prices = df['Close']
            prices.index = pd.to_datetime(prices.index).tz_localize(None)
            prices.name = benchmark
            
            # 过滤到请求的日期范围
            prices = prices[prices.index >= pd.Timestamp(start_date)]
            
            # 更新缓存
            self._cache[cache_key] = prices
            self._cache_time[cache_key] = datetime.now()
            
            logger.info(f"获取 {symbol} 数据成功，共 {len(prices)} 条记录")
            return prices
            
        except Exception as e:
            logger.error(f"获取基准指数数据失败 {symbol}: {e}")
            return pd.Series(dtype=float)
    
    def get_benchmark_returns(
        self, 
        benchmark: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> pd.Series:
        """
        获取基准指数收益率序列
        
        :param benchmark: 基准代码
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 日收益率 Series
        """
        prices = self.fetch_benchmark_data(benchmark, start_date, end_date)
        
        if prices.empty:
            return pd.Series(dtype=float)
        
        returns = prices.pct_change().dropna()
        returns.name = f"{benchmark}_returns"
        
        return returns
    
    def align_with_portfolio(
        self, 
        portfolio_returns: pd.Series, 
        benchmark: str
    ) -> pd.Series:
        """
        获取与组合收益率对齐的基准收益率
        
        :param portfolio_returns: 组合收益率序列
        :param benchmark: 基准代码
        :return: 对齐后的基准收益率
        """
        if portfolio_returns.empty:
            return pd.Series(dtype=float)
        
        start_date = portfolio_returns.index[0]
        end_date = portfolio_returns.index[-1]
        
        # 转换为 datetime
        if hasattr(start_date, 'to_pydatetime'):
            start_date = start_date.to_pydatetime()
        if hasattr(end_date, 'to_pydatetime'):
            end_date = end_date.to_pydatetime()
        
        benchmark_returns = self.get_benchmark_returns(benchmark, start_date, end_date)
        
        if benchmark_returns.empty:
            logger.warning(f"无法获取基准 {benchmark} 的收益率数据")
            return pd.Series(dtype=float)
        
        # 对齐到组合的交易日
        aligned = benchmark_returns.reindex(portfolio_returns.index, method='ffill')
        
        # 填充缺失值为 0
        aligned = aligned.fillna(0)
        
        logger.debug(f"基准 {benchmark} 对齐后共 {len(aligned)} 条记录")
        return aligned
    
    def get_all_benchmarks_returns(
        self, 
        portfolio_returns: pd.Series
    ) -> Dict[str, pd.Series]:
        """
        获取所有基准指数的收益率（与组合对齐）
        
        :param portfolio_returns: 组合收益率序列
        :return: {benchmark_code: returns_series}
        """
        results = {}
        for benchmark in config.BENCHMARK_SYMBOLS.keys():
            returns = self.align_with_portfolio(portfolio_returns, benchmark)
            if not returns.empty:
                results[benchmark] = returns
        return results


# 全局单例
benchmark_service = BenchmarkService()

