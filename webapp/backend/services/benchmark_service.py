#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基准指数服务 - 使用长桥(LongPort) API 获取基准指数数据
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional
from loguru import logger

from longport.openapi import Period, AdjustType

from ..config import config


class BenchmarkService:
    """基准指数服务"""
    
    def __init__(self):
        """初始化基准指数服务"""
        # 内存缓存
        self._cache: Dict[str, pd.Series] = {}
        self._cache_time: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(hours=1)  # 缓存1小时
        # 延迟初始化长桥 API
        self._longport_api = None
        
    def _get_longport_api(self):
        """获取长桥 API 实例（延迟初始化）"""
        if self._longport_api is None:
            from awesometrader import LongPortQuotaAPI
            self._longport_api = LongPortQuotaAPI()
        return self._longport_api
        
    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self._cache_time:
            return False
        return datetime.now() - self._cache_time[cache_key] < self._cache_ttl
    
    def get_benchmark_symbol(self, benchmark: str) -> str:
        """
        获取基准指数的符号
        
        :param benchmark: 基准代码
        :return: 符号
        """
        benchmark_lower = benchmark.lower()
        
        if benchmark_lower in config.LONGPORT_BENCHMARKS:
            return config.LONGPORT_BENCHMARKS[benchmark_lower]["symbol"]
        
        all_benchmarks = list(config.LONGPORT_BENCHMARKS.keys())
        raise ValueError(f"未知的基准指数: {benchmark}，可选: {all_benchmarks}")
    
    def get_benchmark_name(self, benchmark: str) -> str:
        """获取基准指数的中文名称"""
        benchmark_lower = benchmark.lower()
        
        if benchmark_lower in config.LONGPORT_BENCHMARKS:
            return config.LONGPORT_BENCHMARKS[benchmark_lower]["name"]
        
        return benchmark
    
    def _fetch_longport_data(
        self,
        benchmark: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.Series:
        """
        使用长桥(LongPort) API 获取基准指数数据
        
        :param benchmark: 基准代码
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 收盘价 Series
        """
        benchmark_config = config.LONGPORT_BENCHMARKS.get(benchmark.lower())
        if not benchmark_config:
            logger.error(f"未知的基准指数: {benchmark}")
            return pd.Series(dtype=float)
        
        symbol = benchmark_config["symbol"]
        
        try:
            logger.info(f"从长桥 API 获取指数 {symbol}: {start_date.date()} - {end_date.date()}")
            
            # 获取长桥 API 实例
            api = self._get_longport_api()
            
            # 使用日线数据，不复权
            df = api.get_stock_history(
                stock_code=symbol,
                period=Period.Day,
                adjust_type=AdjustType.NoAdjust,
                start_date=start_date,
                end_date=end_date
            )
            
            if df.empty:
                logger.warning(f"长桥 API 未获取到 {symbol} 的数据")
                return pd.Series(dtype=float)
            
            # 提取收盘价，转换为 float（LongPort 返回 Decimal 类型）
            prices = df['Close'].astype(float).copy()
            # 将时间戳索引转换为日期（去掉时间部分和时区信息）
            prices.index = pd.to_datetime(prices.index).normalize()
            if prices.index.tz is not None:
                prices.index = prices.index.tz_localize(None)
            prices.name = benchmark
            
            logger.info(f"长桥 API 获取 {symbol} 数据成功，共 {len(prices)} 条记录")
            return prices
            
        except Exception as e:
            logger.error(f"长桥 API 获取数据失败 {symbol}: {e}")
            return pd.Series(dtype=float)
    
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
        cache_key = f"{benchmark}_{start_date.date()}_{end_date.date()}"
        
        # 检查缓存
        if self._is_cache_valid(cache_key) and cache_key in self._cache:
            logger.debug(f"使用缓存数据: {cache_key}")
            return self._cache[cache_key]
        
        # 使用长桥 API 获取数据
        prices = self._fetch_longport_data(benchmark, start_date, end_date)
        
        if not prices.empty:
            # 更新缓存
            self._cache[cache_key] = prices
            self._cache_time[cache_key] = datetime.now()
        
        return prices
    
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
        
        # 如果短时间范围获取不到数据，尝试扩展时间范围
        # 这是因为股市在节假日休市，短时间段可能没有交易数据
        if benchmark_returns.empty:
            # 向前扩展30天尝试获取数据
            extended_start = start_date - timedelta(days=30)
            logger.debug(f"扩展时间范围获取基准数据: {extended_start} - {end_date}")
            benchmark_returns = self.get_benchmark_returns(benchmark, extended_start, end_date)
        
        if benchmark_returns.empty:
            logger.warning(f"无法获取基准 {benchmark} 的收益率数据")
            return pd.Series(dtype=float)
        
        # 对齐到组合的交易日
        # 注意：不使用 ffill，因为这会导致周末/节假日的收益率被重复计算
        # 对于没有基准数据的日期（如周末），收益率设为 0
        aligned = benchmark_returns.reindex(portfolio_returns.index)
        
        # 填充缺失值为 0（周末/节假日没有交易，收益为0）
        aligned = aligned.fillna(0)
        
        logger.debug(f"基准 {benchmark} 对齐后共 {len(aligned)} 条记录，其中 {aligned.eq(0).sum()} 条为0")
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
        all_benchmarks = list(config.LONGPORT_BENCHMARKS.keys())
        for benchmark in all_benchmarks:
            returns = self.align_with_portfolio(portfolio_returns, benchmark)
            if not returns.empty:
                results[benchmark] = returns
        return results


# 全局单例
benchmark_service = BenchmarkService()

