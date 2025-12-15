#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据加载模块 - 从 account.csv 读取账户数据并转换为收益率序列
"""

import pandas as pd
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from typing import Tuple, Optional
from loguru import logger

from ..config import config


class DataLoader:
    """账户数据加载器"""
    
    def __init__(self):
        """初始化数据加载器"""
        self._account_data: Optional[pd.DataFrame] = None
        self._returns: Optional[pd.Series] = None
        
    def load_account_data(self, force_reload: bool = False) -> pd.DataFrame:
        """
        加载账户数据
        
        :param force_reload: 是否强制重新加载
        :return: 账户数据 DataFrame
        """
        if self._account_data is not None and not force_reload:
            return self._account_data
            
        try:
            df = pd.read_csv(config.ACCOUNT_CSV_PATH)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date').sort_index()
            
            # 确保数据类型正确
            df['total_assets'] = pd.to_numeric(df['total_assets'], errors='coerce')
            
            self._account_data = df
            logger.info(f"加载账户数据成功，共 {len(df)} 条记录，时间范围: {df.index[0]} - {df.index[-1]}")
            return df
            
        except Exception as e:
            logger.error(f"加载账户数据失败: {e}")
            raise ValueError(f"无法加载账户数据: {e}")
    
    def get_returns(self, force_reload: bool = False) -> pd.Series:
        """
        获取日收益率序列
        
        :param force_reload: 是否强制重新计算
        :return: 日收益率 Series (index 为日期)
        """
        if self._returns is not None and not force_reload:
            return self._returns
            
        df = self.load_account_data(force_reload)
        
        # 计算日收益率: (今日资产 - 昨日资产) / 昨日资产
        returns = df['total_assets'].pct_change().dropna()
        returns.name = 'returns'
        
        self._returns = returns
        logger.info(f"计算收益率序列成功，共 {len(returns)} 个交易日")
        return returns
    
    def get_equity_curve(self, force_reload: bool = False) -> pd.Series:
        """
        获取资产曲线（总资产序列）
        
        :return: 总资产 Series
        """
        df = self.load_account_data(force_reload)
        return df['total_assets']
    
    def filter_by_period(self, data: pd.Series, period: str) -> pd.Series:
        """
        根据时间周期过滤数据
        
        :param data: 原始数据序列
        :param period: 时间周期代码 (7d, 1m, 6m, 1y, all, mtd, ytd)
        :return: 过滤后的数据
        """
        if data.empty:
            return data
            
        end_date = data.index[-1]
        
        if period == "all":
            return data
            
        elif period == "mtd":
            # 本月至今
            start_date = end_date.replace(day=1)
            
        elif period == "ytd":
            # 本年至今
            start_date = end_date.replace(month=1, day=1)
            
        else:
            # 固定天数周期
            days = config.PERIOD_DAYS.get(period)
            if days is None:
                logger.warning(f"未知的时间周期: {period}，使用全部数据")
                return data
            start_date = end_date - pd.Timedelta(days=days)
        
        filtered = data[data.index >= start_date]
        logger.debug(f"按周期 {period} 过滤数据: {len(data)} -> {len(filtered)} 条")
        return filtered
    
    def get_period_range(self, period: str) -> Tuple[date, date]:
        """
        获取时间周期的日期范围
        
        :param period: 时间周期代码
        :return: (start_date, end_date)
        """
        df = self.load_account_data()
        end_date = df.index[-1].date()
        
        if period == "all":
            start_date = df.index[0].date()
            
        elif period == "mtd":
            start_date = end_date.replace(day=1)
            
        elif period == "ytd":
            start_date = end_date.replace(month=1, day=1)
            
        else:
            days = config.PERIOD_DAYS.get(period, 0)
            if days:
                start_date = end_date - pd.Timedelta(days=days)
                start_date = start_date.date() if hasattr(start_date, 'date') else start_date
            else:
                start_date = df.index[0].date()
        
        return start_date, end_date
    
    def get_filtered_returns(self, period: str = "all") -> pd.Series:
        """
        获取指定周期的收益率序列
        
        :param period: 时间周期
        :return: 过滤后的收益率序列
        """
        returns = self.get_returns()
        return self.filter_by_period(returns, period)
    
    def get_filtered_equity(self, period: str = "all") -> pd.Series:
        """
        获取指定周期的资产曲线
        
        :param period: 时间周期
        :return: 过滤后的资产曲线
        """
        equity = self.get_equity_curve()
        return self.filter_by_period(equity, period)


# 全局单例
data_loader = DataLoader()

