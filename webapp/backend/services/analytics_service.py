#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
分析服务 - 使用 quantstats 计算风控指标
"""

import pandas as pd
import numpy as np
import quantstats as qs
from datetime import date
from typing import Dict, List, Optional, Any
from loguru import logger

from ..config import config
from .data_loader import data_loader
from .benchmark_service import benchmark_service


class AnalyticsService:
    """分析服务 - 核心指标计算"""
    
    def __init__(self):
        """初始化分析服务"""
        self.data_loader = data_loader
        self.benchmark_service = benchmark_service
    
    # ==================== 收益指标 ====================
    
    def calculate_return_metrics(self, returns: pd.Series) -> Dict[str, Any]:
        """
        计算收益相关指标
        
        :param returns: 日收益率序列
        :return: 收益指标字典
        """
        if returns.empty or len(returns) < 2:
            return self._empty_return_metrics()
        
        try:
            # 累计收益率
            cumulative_return = qs.stats.comp(returns)
            
            # 年化收益率
            annualized_return = qs.stats.cagr(returns)
            
            # 日收益统计
            daily_mean = returns.mean()
            daily_std = returns.std()
            
            # 最佳/最差单日
            best_day = returns.max()
            worst_day = returns.min()
            
            # 胜率
            win_rate = qs.stats.win_rate(returns)
            
            # YTD 和 MTD
            ytd_return = None
            mtd_return = None
            
            end_date = returns.index[-1]
            
            # 计算 YTD
            ytd_start = end_date.replace(month=1, day=1)
            ytd_returns = returns[returns.index >= ytd_start]
            if len(ytd_returns) > 0:
                ytd_return = qs.stats.comp(ytd_returns)
            
            # 计算 MTD
            mtd_start = end_date.replace(day=1)
            mtd_returns = returns[returns.index >= mtd_start]
            if len(mtd_returns) > 0:
                mtd_return = qs.stats.comp(mtd_returns)
            
            return {
                "cumulative_return": float(cumulative_return) if not np.isnan(cumulative_return) else 0.0,
                "annualized_return": float(annualized_return) if not np.isnan(annualized_return) else 0.0,
                "ytd_return": float(ytd_return) if ytd_return is not None and not np.isnan(ytd_return) else None,
                "mtd_return": float(mtd_return) if mtd_return is not None and not np.isnan(mtd_return) else None,
                "daily_return_mean": float(daily_mean) if not np.isnan(daily_mean) else 0.0,
                "daily_return_std": float(daily_std) if not np.isnan(daily_std) else 0.0,
                "best_day": float(best_day) if not np.isnan(best_day) else 0.0,
                "worst_day": float(worst_day) if not np.isnan(worst_day) else 0.0,
                "win_rate": float(win_rate) if not np.isnan(win_rate) else 0.0,
            }
            
        except Exception as e:
            logger.error(f"计算收益指标失败: {e}")
            return self._empty_return_metrics()
    
    def _empty_return_metrics(self) -> Dict[str, Any]:
        """返回空的收益指标"""
        return {
            "cumulative_return": 0.0,
            "annualized_return": 0.0,
            "ytd_return": None,
            "mtd_return": None,
            "daily_return_mean": 0.0,
            "daily_return_std": 0.0,
            "best_day": 0.0,
            "worst_day": 0.0,
            "win_rate": 0.0,
        }
    
    # ==================== 风险指标 ====================
    
    def calculate_risk_metrics(self, returns: pd.Series) -> Dict[str, Any]:
        """
        计算风险相关指标
        
        :param returns: 日收益率序列
        :return: 风险指标字典
        """
        if returns.empty or len(returns) < 2:
            return self._empty_risk_metrics()
        
        try:
            # 年化波动率
            volatility = qs.stats.volatility(returns, annualize=True)
            
            # 最大回撤
            max_drawdown = qs.stats.max_drawdown(returns)
            
            # 夏普比率
            sharpe = qs.stats.sharpe(returns, rf=config.RISK_FREE_RATE)
            
            # 索提诺比率
            sortino = qs.stats.sortino(returns, rf=config.RISK_FREE_RATE)
            
            # 卡玛比率
            calmar = qs.stats.calmar(returns)
            
            # VaR 和 CVaR (95%)
            var_95 = qs.stats.var(returns, sigma=1.65)  # 95% VaR
            cvar_95 = qs.stats.cvar(returns, sigma=1.65)  # 95% CVaR
            
            # 偏度和峰度
            skewness = qs.stats.skew(returns)
            kurtosis = qs.stats.kurtosis(returns)
            
            # 最大回撤持续时间
            max_dd_duration = None
            try:
                drawdown_details = qs.stats.drawdown_details(returns)
                if drawdown_details is not None and len(drawdown_details) > 0:
                    max_dd_duration = int(drawdown_details['days'].max())
            except:
                pass
            
            return {
                "volatility": float(volatility) if not np.isnan(volatility) else 0.0,
                "max_drawdown": float(max_drawdown) if not np.isnan(max_drawdown) else 0.0,
                "max_drawdown_duration": max_dd_duration,
                "sharpe_ratio": float(sharpe) if not np.isnan(sharpe) else 0.0,
                "sortino_ratio": float(sortino) if not np.isnan(sortino) else 0.0,
                "calmar_ratio": float(calmar) if not np.isnan(calmar) else 0.0,
                "var_95": float(var_95) if not np.isnan(var_95) else 0.0,
                "cvar_95": float(cvar_95) if not np.isnan(cvar_95) else 0.0,
                "skewness": float(skewness) if not np.isnan(skewness) else 0.0,
                "kurtosis": float(kurtosis) if not np.isnan(kurtosis) else 0.0,
            }
            
        except Exception as e:
            logger.error(f"计算风险指标失败: {e}")
            return self._empty_risk_metrics()
    
    def _empty_risk_metrics(self) -> Dict[str, Any]:
        """返回空的风险指标"""
        return {
            "volatility": 0.0,
            "max_drawdown": 0.0,
            "max_drawdown_duration": None,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "calmar_ratio": 0.0,
            "var_95": 0.0,
            "cvar_95": 0.0,
            "skewness": 0.0,
            "kurtosis": 0.0,
        }
    
    # ==================== 基准对比 ====================
    
    def calculate_benchmark_comparison(
        self, 
        returns: pd.Series, 
        benchmark: str
    ) -> Optional[Dict[str, Any]]:
        """
        计算与基准的对比指标
        
        :param returns: 组合日收益率序列
        :param benchmark: 基准代码
        :return: 基准对比指标字典
        """
        if returns.empty:
            return None
        
        try:
            # 获取对齐的基准收益率
            benchmark_returns = self.benchmark_service.align_with_portfolio(returns, benchmark)
            
            if benchmark_returns.empty:
                logger.warning(f"无法获取基准 {benchmark} 的对比数据")
                return None
            
            # 基准收益率
            benchmark_return = qs.stats.comp(benchmark_returns)
            
            # Alpha
            alpha = qs.stats.greeks(returns, benchmark_returns).get('alpha', 0.0)
            
            # Beta
            beta = qs.stats.greeks(returns, benchmark_returns).get('beta', 1.0)
            
            # 相关系数
            correlation = returns.corr(benchmark_returns)
            
            # 信息比率
            info_ratio = qs.stats.information_ratio(returns, benchmark_returns)
            
            # 跟踪误差
            excess_returns = returns - benchmark_returns
            tracking_error = excess_returns.std() * np.sqrt(252)
            
            # 上涨/下跌捕获率
            up_capture = self._calculate_capture_ratio(returns, benchmark_returns, up=True)
            down_capture = self._calculate_capture_ratio(returns, benchmark_returns, up=False)
            
            return {
                "benchmark_name": self.benchmark_service.get_benchmark_name(benchmark),
                "benchmark_return": float(benchmark_return) if not np.isnan(benchmark_return) else 0.0,
                "alpha": float(alpha) if not np.isnan(alpha) else 0.0,
                "beta": float(beta) if not np.isnan(beta) else 1.0,
                "correlation": float(correlation) if not np.isnan(correlation) else 0.0,
                "information_ratio": float(info_ratio) if not np.isnan(info_ratio) else 0.0,
                "tracking_error": float(tracking_error) if not np.isnan(tracking_error) else 0.0,
                "up_capture": float(up_capture),
                "down_capture": float(down_capture),
            }
            
        except Exception as e:
            logger.error(f"计算基准对比失败 {benchmark}: {e}")
            return None
    
    def _calculate_capture_ratio(
        self, 
        returns: pd.Series, 
        benchmark_returns: pd.Series, 
        up: bool = True
    ) -> float:
        """计算上涨/下跌捕获率"""
        try:
            if up:
                mask = benchmark_returns > 0
            else:
                mask = benchmark_returns < 0
            
            if mask.sum() == 0:
                return 1.0
            
            portfolio_capture = (1 + returns[mask]).prod() - 1
            benchmark_capture = (1 + benchmark_returns[mask]).prod() - 1
            
            if benchmark_capture == 0:
                return 1.0
            
            return portfolio_capture / benchmark_capture
            
        except:
            return 1.0
    
    def calculate_all_benchmarks(self, returns: pd.Series) -> List[Dict[str, Any]]:
        """
        计算与所有基准的对比
        
        :param returns: 组合收益率
        :return: 所有基准的对比指标列表
        """
        results = []
        for benchmark in config.BENCHMARK_SYMBOLS.keys():
            comparison = self.calculate_benchmark_comparison(returns, benchmark)
            if comparison:
                results.append(comparison)
        return results
    
    # ==================== 回撤分析 ====================
    
    def calculate_drawdown_series(self, returns: pd.Series) -> pd.Series:
        """
        计算回撤序列
        
        :param returns: 日收益率序列
        :return: 回撤序列
        """
        if returns.empty:
            return pd.Series(dtype=float)
        
        # 计算累计收益
        cumulative = (1 + returns).cumprod()
        
        # 计算滚动最高点
        running_max = cumulative.cummax()
        
        # 计算回撤
        drawdown = (cumulative - running_max) / running_max
        
        return drawdown
    
    def get_worst_drawdowns(self, returns: pd.Series, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        获取最差的 N 次回撤
        
        :param returns: 日收益率序列
        :param top_n: 返回前 N 次最差回撤
        :return: 回撤详情列表
        """
        if returns.empty:
            return []
        
        try:
            details = qs.stats.drawdown_details(returns)
            
            if details is None or len(details) == 0:
                return []
            
            # 按回撤幅度排序
            details = details.nsmallest(top_n, 'max drawdown')
            
            result = []
            for _, row in details.iterrows():
                # 处理日期字段，可能是 Timestamp、datetime 或字符串
                def parse_date(val):
                    if pd.isna(val):
                        return None
                    if hasattr(val, 'date'):
                        return val.date()
                    if isinstance(val, str):
                        try:
                            return pd.to_datetime(val).date()
                        except:
                            return None
                    return None
                
                result.append({
                    "start_date": parse_date(row['start']),
                    "end_date": parse_date(row['end']),
                    "recovery_date": parse_date(row['valley']),
                    "drawdown": float(row['max drawdown']),
                    "duration": int(row['days']) if pd.notna(row['days']) else 0,
                    "recovery_days": None,  # quantstats 不直接提供
                })
            
            return result
            
        except Exception as e:
            logger.error(f"获取回撤详情失败: {e}")
            return []
    
    # ==================== 月度收益 ====================
    
    def calculate_monthly_returns(self, returns: pd.Series) -> List[Dict[str, Any]]:
        """
        计算月度收益
        
        :param returns: 日收益率序列
        :return: 月度收益列表
        """
        if returns.empty:
            return []
        
        try:
            # 按月分组计算累计收益
            monthly = returns.groupby([returns.index.year, returns.index.month]).apply(
                lambda x: (1 + x).prod() - 1
            )
            
            result = []
            for (year, month), value in monthly.items():
                result.append({
                    "year": int(year),
                    "month": int(month),
                    "return_value": float(value) if not np.isnan(value) else 0.0,
                })
            
            return result
            
        except Exception as e:
            logger.error(f"计算月度收益失败: {e}")
            return []
    
    def calculate_yearly_returns(self, returns: pd.Series) -> List[Dict[str, Any]]:
        """
        计算年度收益
        
        :param returns: 日收益率序列
        :return: 年度收益列表
        """
        if returns.empty:
            return []
        
        try:
            yearly = returns.groupby(returns.index.year).apply(
                lambda x: (1 + x).prod() - 1
            )
            
            result = []
            for year, value in yearly.items():
                result.append({
                    str(year): float(value) if not np.isnan(value) else 0.0,
                })
            
            return result
            
        except Exception as e:
            logger.error(f"计算年度收益失败: {e}")
            return []
    
    # ==================== 综合分析 ====================
    
    def get_overview(self, period: str = "all", benchmark: str = "sp500") -> Dict[str, Any]:
        """
        获取总览数据
        
        :param period: 时间周期
        :param benchmark: 基准代码
        :return: 总览数据
        """
        returns = self.data_loader.get_filtered_returns(period)
        equity = self.data_loader.get_filtered_equity(period)
        
        if returns.empty or equity.empty:
            raise ValueError("没有足够的数据进行分析")
        
        start_date, end_date = self.data_loader.get_period_range(period)
        
        return_metrics = self.calculate_return_metrics(returns)
        risk_metrics = self.calculate_risk_metrics(returns)
        benchmark_comparison = self.calculate_benchmark_comparison(returns, benchmark)
        
        return {
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
            "trading_days": len(returns),
            "initial_value": float(equity.iloc[0]),
            "final_value": float(equity.iloc[-1]),
            "returns": return_metrics,
            "risk": risk_metrics,
            "benchmark": benchmark_comparison,
        }
    
    def get_equity_curve_data(
        self, 
        period: str = "all", 
        benchmark: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取资产曲线数据
        
        :param period: 时间周期
        :param benchmark: 基准代码（可选）
        :return: 资产曲线数据
        """
        equity = self.data_loader.get_filtered_equity(period)
        
        if equity.empty:
            return {"period": period, "portfolio": [], "benchmark": None}
        
        # 归一化到起始值为 1
        portfolio_normalized = equity / equity.iloc[0]
        
        portfolio_data = [
            {"date": d.strftime("%Y-%m-%d"), "value": float(v)}
            for d, v in portfolio_normalized.items()
        ]
        
        benchmark_data = None
        if benchmark:
            returns = self.data_loader.get_filtered_returns(period)
            bench_returns = self.benchmark_service.align_with_portfolio(returns, benchmark)
            
            if not bench_returns.empty:
                # 计算累计收益曲线
                bench_cumulative = (1 + bench_returns).cumprod()
                benchmark_data = [
                    {"date": d.strftime("%Y-%m-%d"), "value": float(v)}
                    for d, v in bench_cumulative.items()
                ]
        
        return {
            "period": period,
            "portfolio": portfolio_data,
            "benchmark": benchmark_data,
        }


# 全局单例
analytics_service = AnalyticsService()

