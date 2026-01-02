#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基准指数服务 - 使用 akshare 获取基准指数数据
"""

import pandas as pd
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
        获取基准指数的符号
        
        :param benchmark: 基准代码
        :return: 符号
        """
        benchmark_lower = benchmark.lower()
        
        if benchmark_lower in config.AKSHARE_BENCHMARKS:
            return config.AKSHARE_BENCHMARKS[benchmark_lower]["symbol"]
        
        all_benchmarks = list(config.AKSHARE_BENCHMARKS.keys())
        raise ValueError(f"未知的基准指数: {benchmark}，可选: {all_benchmarks}")
    
    def get_benchmark_name(self, benchmark: str) -> str:
        """获取基准指数的中文名称"""
        benchmark_lower = benchmark.lower()
        
        if benchmark_lower in config.AKSHARE_BENCHMARKS:
            return config.AKSHARE_BENCHMARKS[benchmark_lower]["name"]
        
        return benchmark
    
    def _fetch_akshare_data(
        self,
        benchmark: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.Series:
        """
        使用 akshare 获取基准指数数据
        
        :param benchmark: 基准代码
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 收盘价 Series
        """
        try:
            import akshare as ak
        except ImportError:
            logger.error("akshare 未安装，请运行: pip install akshare")
            return pd.Series(dtype=float)
        
        benchmark_config = config.AKSHARE_BENCHMARKS.get(benchmark.lower())
        if not benchmark_config:
            return pd.Series(dtype=float)
        
        symbol = benchmark_config["symbol"]
        index_type = benchmark_config["type"]
        
        try:
            if index_type == "a_index":
                # A股指数
                prices = self._fetch_a_index(ak, symbol, start_date, end_date, benchmark)
                
            elif index_type == "hk_index":
                # 港股指数
                prices = self._fetch_hk_index(ak, symbol, start_date, end_date, benchmark)
                
            elif index_type == "us_index":
                # 美股指数 (新浪财经)
                prices = self._fetch_us_index(ak, symbol, start_date, end_date, benchmark)
                
            else:
                logger.error(f"未知的指数类型: {index_type}")
                return pd.Series(dtype=float)
            
            if not prices.empty:
                logger.info(f"akshare 获取 {symbol} 数据成功，共 {len(prices)} 条记录")
            return prices
            
        except Exception as e:
            logger.error(f"akshare 获取数据失败 {symbol}: {e}")
            return pd.Series(dtype=float)
    
    def _fetch_a_index(self, ak, symbol: str, start_date: datetime, end_date: datetime, benchmark: str) -> pd.Series:
        """获取 A 股指数数据"""
        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')
        logger.info(f"从 akshare 获取 A股指数 {symbol}: {start_str} - {end_str}")
        
        df = ak.index_zh_a_hist(symbol=symbol, period='daily', start_date=start_str, end_date=end_str)
        
        if df.empty:
            return pd.Series(dtype=float)
        
        prices = pd.Series(df['收盘'].values, index=pd.to_datetime(df['日期']))
        prices.name = benchmark
        return prices
    
    def _fetch_hk_index(self, ak, symbol: str, start_date: datetime, end_date: datetime, benchmark: str) -> pd.Series:
        """获取港股指数数据"""
        logger.info(f"从 akshare 获取港股指数 {symbol}")
        
        df = ak.stock_hk_index_daily_em(symbol=symbol)
        
        if df.empty:
            return pd.Series(dtype=float)
        
        # 过滤日期范围
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        df = df[(df['date'] >= start_str) & (df['date'] <= end_str)]
        
        if df.empty:
            return pd.Series(dtype=float)
        
        prices = pd.Series(df['latest'].values, index=pd.to_datetime(df['date']))
        prices.name = benchmark
        return prices
    
    def _fetch_us_index(self, ak, symbol: str, start_date: datetime, end_date: datetime, benchmark: str) -> pd.Series:
        """获取美股指数数据 (新浪财经)"""
        logger.info(f"从 akshare 获取美股指数 {symbol}")
        
        # 使用新浪财经美股指数历史数据接口
        df = ak.index_us_stock_sina(symbol=symbol)
        
        if df.empty:
            return pd.Series(dtype=float)
        
        # 转换日期格式并过滤
        df['date'] = pd.to_datetime(df['date'])
        df = df[(df['date'] >= pd.Timestamp(start_date)) & (df['date'] <= pd.Timestamp(end_date))]
        
        if df.empty:
            return pd.Series(dtype=float)
        
        prices = pd.Series(df['close'].values, index=df['date'])
        prices.name = benchmark
        return prices
    
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
        
        # 使用 akshare 获取数据
        prices = self._fetch_akshare_data(benchmark, start_date, end_date)
        
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
        all_benchmarks = list(config.AKSHARE_BENCHMARKS.keys())
        for benchmark in all_benchmarks:
            returns = self.align_with_portfolio(portfolio_returns, benchmark)
            if not returns.empty:
                results[benchmark] = returns
        return results


# 全局单例
benchmark_service = BenchmarkService()

