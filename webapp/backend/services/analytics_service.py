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
    
    @staticmethod
    def _safe_float(value, default=0.0) -> float:
        """
        安全转换为 float，处理 nan 和 inf 值
        
        :param value: 输入值
        :param default: 当值无效时的默认值
        :return: 安全的 float 值
        """
        if value is None:
            return default
        try:
            f = float(value)
            if np.isnan(f) or np.isinf(f):
                return default
            return f
        except (ValueError, TypeError):
            return default
    
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
            
            # 平均盈利和平均亏损
            positive_returns = returns[returns > 0]
            negative_returns = returns[returns < 0]
            avg_win = positive_returns.mean() if len(positive_returns) > 0 else 0.0
            avg_loss = negative_returns.mean() if len(negative_returns) > 0 else 0.0
            
            # 利润因子
            total_win = positive_returns.sum() if len(positive_returns) > 0 else 0.0
            total_loss = abs(negative_returns.sum()) if len(negative_returns) > 0 else 0.0
            profit_factor = total_win / total_loss if total_loss > 0 else 0.0
            
            # 盈亏比 (Payoff Ratio)
            payoff_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0.0
            
            # 期望收益 (Expectancy)
            expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss) if win_rate > 0 else 0.0
            
            # 几何平均
            geometric_mean = qs.stats.geometric_mean(returns) if hasattr(qs.stats, 'geometric_mean') else ((1 + returns).prod() ** (1/len(returns)) - 1)
            
            # 期望月收益和年收益
            expected_monthly = daily_mean * 21  # 约21个交易日
            expected_yearly = daily_mean * 252  # 约252个交易日
            
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
                "cumulative_return": self._safe_float(cumulative_return),
                "annualized_return": self._safe_float(annualized_return),
                "ytd_return": self._safe_float(ytd_return) if ytd_return is not None else None,
                "mtd_return": self._safe_float(mtd_return) if mtd_return is not None else None,
                "daily_return_mean": self._safe_float(daily_mean),
                "daily_return_std": self._safe_float(daily_std),
                "best_day": self._safe_float(best_day),
                "worst_day": self._safe_float(worst_day),
                "win_rate": self._safe_float(win_rate),
                "avg_win": self._safe_float(avg_win),
                "avg_loss": self._safe_float(avg_loss),
                "profit_factor": self._safe_float(profit_factor),
                "payoff_ratio": self._safe_float(payoff_ratio),
                "expectancy": self._safe_float(expectancy),
                "geometric_mean": self._safe_float(geometric_mean),
                "expected_monthly": self._safe_float(expected_monthly),
                "expected_yearly": self._safe_float(expected_yearly),
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
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "profit_factor": 0.0,
            "payoff_ratio": 0.0,
            "expectancy": 0.0,
            "geometric_mean": 0.0,
            "expected_monthly": 0.0,
            "expected_yearly": 0.0,
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
            
            # 溃疡指数 (Ulcer Index)
            ulcer_index = qs.stats.ulcer_index(returns) if hasattr(qs.stats, 'ulcer_index') else self._calculate_ulcer_index(returns)
            
            # 尾部比率 (Tail Ratio) - 95分位收益 / |5分位收益|
            percentile_95 = np.percentile(returns, 95)
            percentile_5 = np.percentile(returns, 5)
            tail_ratio = abs(percentile_95 / percentile_5) if percentile_5 != 0 else 0.0
            
            # 凯利公式 (Kelly Criterion)
            positive_returns = returns[returns > 0]
            negative_returns = returns[returns < 0]
            win_rate = len(positive_returns) / len(returns) if len(returns) > 0 else 0
            avg_win = positive_returns.mean() if len(positive_returns) > 0 else 0
            avg_loss = abs(negative_returns.mean()) if len(negative_returns) > 0 else 0
            payoff_ratio = avg_win / avg_loss if avg_loss > 0 else 0
            kelly_criterion = (win_rate - (1 - win_rate) / payoff_ratio) if payoff_ratio > 0 else 0
            
            # 欧米伽比率 (Omega Ratio)
            omega_ratio = qs.stats.omega(returns) if hasattr(qs.stats, 'omega') else self._calculate_omega_ratio(returns)
            
            # 增益痛苦比 (Gain to Pain Ratio)
            gain_to_pain = qs.stats.gain_to_pain_ratio(returns) if hasattr(qs.stats, 'gain_to_pain_ratio') else self._calculate_gain_to_pain(returns)
            
            # 常识比率 (Common Sense Ratio) = Profit Factor * Tail Ratio
            total_win = positive_returns.sum() if len(positive_returns) > 0 else 0
            total_loss = abs(negative_returns.sum()) if len(negative_returns) > 0 else 0
            profit_factor = total_win / total_loss if total_loss > 0 else 0
            common_sense_ratio = profit_factor * tail_ratio
            
            # 恢复因子 (Recovery Factor) = 累计收益 / |最大回撤|
            cumulative_return = (1 + returns).prod() - 1
            recovery_factor = cumulative_return / abs(max_drawdown) if max_drawdown != 0 else 0
            
            # 风险收益比 (Risk Return Ratio)
            annualized_return = qs.stats.cagr(returns)
            risk_return_ratio = annualized_return / volatility if volatility > 0 else 0
            
            # 溃疡表现指数 (UPI) = 年化收益 / Ulcer Index
            upi = annualized_return / ulcer_index if ulcer_index > 0 else 0
            
            return {
                "volatility": self._safe_float(volatility),
                "max_drawdown": self._safe_float(max_drawdown),
                "max_drawdown_duration": max_dd_duration,
                "sharpe_ratio": self._safe_float(sharpe),
                "sortino_ratio": self._safe_float(sortino),
                "calmar_ratio": self._safe_float(calmar),
                "var_95": self._safe_float(var_95),
                "cvar_95": self._safe_float(cvar_95),
                "skewness": self._safe_float(skewness),
                "kurtosis": self._safe_float(kurtosis),
                "ulcer_index": self._safe_float(ulcer_index),
                "tail_ratio": self._safe_float(tail_ratio),
                "kelly_criterion": self._safe_float(kelly_criterion),
                "omega_ratio": self._safe_float(omega_ratio),
                "gain_to_pain_ratio": self._safe_float(gain_to_pain),
                "common_sense_ratio": self._safe_float(common_sense_ratio),
                "recovery_factor": self._safe_float(recovery_factor),
                "risk_return_ratio": self._safe_float(risk_return_ratio),
                "ulcer_performance_index": self._safe_float(upi),
            }
            
        except Exception as e:
            logger.error(f"计算风险指标失败: {e}")
            return self._empty_risk_metrics()
    
    def _calculate_ulcer_index(self, returns: pd.Series) -> float:
        """计算溃疡指数"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        return np.sqrt((drawdown ** 2).mean())
    
    def _calculate_omega_ratio(self, returns: pd.Series, threshold: float = 0.0) -> float:
        """计算欧米伽比率"""
        excess = returns - threshold
        gains = excess[excess > 0].sum()
        losses = abs(excess[excess < 0].sum())
        return gains / losses if losses > 0 else 0.0
    
    def _calculate_gain_to_pain(self, returns: pd.Series) -> float:
        """计算增益痛苦比"""
        total_return = returns.sum()
        total_loss = abs(returns[returns < 0].sum())
        return total_return / total_loss if total_loss > 0 else 0.0
    
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
            "ulcer_index": 0.0,
            "tail_ratio": 0.0,
            "kelly_criterion": 0.0,
            "omega_ratio": 0.0,
            "gain_to_pain_ratio": 0.0,
            "common_sense_ratio": 0.0,
            "recovery_factor": 0.0,
            "risk_return_ratio": 0.0,
            "ulcer_performance_index": 0.0,
        }
    
    # ==================== 基准对比 ====================
    
    def calculate_benchmark_metrics(
        self,
        portfolio_returns: pd.Series,
        benchmark: str
    ) -> Optional[Dict[str, Any]]:
        """
        计算基准的完整指标（收益、风险和对比）
        
        :param portfolio_returns: 组合日收益率序列
        :param benchmark: 基准代码
        :return: 基准完整指标字典
        """
        if portfolio_returns.empty:
            return None
        
        try:
            # 获取对齐的基准收益率
            benchmark_returns = self.benchmark_service.align_with_portfolio(portfolio_returns, benchmark)
            
            if benchmark_returns.empty:
                logger.warning(f"无法获取基准 {benchmark} 的数据")
                return None
            
            # ========== 基准收益指标 ==========
            benchmark_cumulative = qs.stats.comp(benchmark_returns)
            benchmark_annualized = qs.stats.cagr(benchmark_returns)
            benchmark_daily_mean = benchmark_returns.mean()
            benchmark_daily_std = benchmark_returns.std()
            benchmark_best_day = benchmark_returns.max()
            benchmark_worst_day = benchmark_returns.min()
            benchmark_win_rate = qs.stats.win_rate(benchmark_returns)
            
            positive_returns = benchmark_returns[benchmark_returns > 0]
            negative_returns = benchmark_returns[benchmark_returns < 0]
            benchmark_avg_win = positive_returns.mean() if len(positive_returns) > 0 else 0.0
            benchmark_avg_loss = negative_returns.mean() if len(negative_returns) > 0 else 0.0
            
            total_win = positive_returns.sum() if len(positive_returns) > 0 else 0.0
            total_loss = abs(negative_returns.sum()) if len(negative_returns) > 0 else 0.0
            benchmark_profit_factor = total_win / total_loss if total_loss > 0 else 0.0
            benchmark_payoff_ratio = abs(benchmark_avg_win / benchmark_avg_loss) if benchmark_avg_loss != 0 else 0.0
            benchmark_expectancy = (benchmark_win_rate * benchmark_avg_win) + ((1 - benchmark_win_rate) * benchmark_avg_loss) if benchmark_win_rate > 0 else 0.0
            benchmark_geometric_mean = qs.stats.geometric_mean(benchmark_returns) if hasattr(qs.stats, 'geometric_mean') else ((1 + benchmark_returns).prod() ** (1/len(benchmark_returns)) - 1)
            benchmark_expected_monthly = benchmark_daily_mean * 21
            benchmark_expected_yearly = benchmark_daily_mean * 252
            
            # ========== 基准风险指标 ==========
            benchmark_volatility = qs.stats.volatility(benchmark_returns, annualize=True)
            benchmark_max_drawdown = qs.stats.max_drawdown(benchmark_returns)
            benchmark_sharpe = qs.stats.sharpe(benchmark_returns, rf=config.RISK_FREE_RATE)
            benchmark_sortino = qs.stats.sortino(benchmark_returns, rf=config.RISK_FREE_RATE)
            benchmark_calmar = qs.stats.calmar(benchmark_returns)
            benchmark_var_95 = qs.stats.var(benchmark_returns, sigma=1.65)
            benchmark_cvar_95 = qs.stats.cvar(benchmark_returns, sigma=1.65)
            benchmark_skewness = qs.stats.skew(benchmark_returns)
            benchmark_kurtosis = qs.stats.kurtosis(benchmark_returns)
            
            # 溃疡指数
            benchmark_ulcer_index = qs.stats.ulcer_index(benchmark_returns) if hasattr(qs.stats, 'ulcer_index') else self._calculate_ulcer_index(benchmark_returns)
            
            # 尾部比率
            percentile_95 = np.percentile(benchmark_returns, 95)
            percentile_5 = np.percentile(benchmark_returns, 5)
            benchmark_tail_ratio = abs(percentile_95 / percentile_5) if percentile_5 != 0 else 0.0
            
            # 凯利公式
            b_win_rate = len(positive_returns) / len(benchmark_returns) if len(benchmark_returns) > 0 else 0
            b_avg_win = positive_returns.mean() if len(positive_returns) > 0 else 0
            b_avg_loss = abs(negative_returns.mean()) if len(negative_returns) > 0 else 0
            b_payoff_ratio = b_avg_win / b_avg_loss if b_avg_loss > 0 else 0
            benchmark_kelly = (b_win_rate - (1 - b_win_rate) / b_payoff_ratio) if b_payoff_ratio > 0 else 0
            
            # 欧米伽比率
            benchmark_omega = qs.stats.omega(benchmark_returns) if hasattr(qs.stats, 'omega') else self._calculate_omega_ratio(benchmark_returns)
            
            # 增益痛苦比
            benchmark_gain_to_pain = qs.stats.gain_to_pain_ratio(benchmark_returns) if hasattr(qs.stats, 'gain_to_pain_ratio') else self._calculate_gain_to_pain(benchmark_returns)
            
            # 常识比率
            benchmark_common_sense = benchmark_profit_factor * benchmark_tail_ratio
            
            # 恢复因子
            benchmark_recovery = benchmark_cumulative / abs(benchmark_max_drawdown) if benchmark_max_drawdown != 0 else 0
            
            # 风险收益比
            benchmark_risk_return = benchmark_annualized / benchmark_volatility if benchmark_volatility > 0 else 0
            
            # UPI
            benchmark_upi = benchmark_annualized / benchmark_ulcer_index if benchmark_ulcer_index > 0 else 0
            
            # ========== 对比指标 ==========
            alpha = qs.stats.greeks(portfolio_returns, benchmark_returns).get('alpha', 0.0)
            beta = qs.stats.greeks(portfolio_returns, benchmark_returns).get('beta', 1.0)
            correlation = portfolio_returns.corr(benchmark_returns)
            info_ratio = qs.stats.information_ratio(portfolio_returns, benchmark_returns)
            excess_returns = portfolio_returns - benchmark_returns
            tracking_error = excess_returns.std() * np.sqrt(252)
            up_capture = self._calculate_capture_ratio(portfolio_returns, benchmark_returns, up=True)
            down_capture = self._calculate_capture_ratio(portfolio_returns, benchmark_returns, up=False)
            
            return {
                "benchmark_name": self.benchmark_service.get_benchmark_name(benchmark),
                # 收益指标
                "benchmark_return": self._safe_float(benchmark_cumulative),
                "benchmark_cagr": self._safe_float(benchmark_annualized),
                "benchmark_daily_mean": self._safe_float(benchmark_daily_mean),
                "benchmark_daily_std": self._safe_float(benchmark_daily_std),
                "benchmark_best_day": self._safe_float(benchmark_best_day),
                "benchmark_worst_day": self._safe_float(benchmark_worst_day),
                "benchmark_win_rate": self._safe_float(benchmark_win_rate),
                "benchmark_avg_win": self._safe_float(benchmark_avg_win),
                "benchmark_avg_loss": self._safe_float(benchmark_avg_loss),
                "benchmark_profit_factor": self._safe_float(benchmark_profit_factor),
                "benchmark_payoff_ratio": self._safe_float(benchmark_payoff_ratio),
                "benchmark_expectancy": self._safe_float(benchmark_expectancy),
                "benchmark_geometric_mean": self._safe_float(benchmark_geometric_mean),
                "benchmark_expected_monthly": self._safe_float(benchmark_expected_monthly),
                "benchmark_expected_yearly": self._safe_float(benchmark_expected_yearly),
                # 风险指标
                "benchmark_volatility": self._safe_float(benchmark_volatility),
                "benchmark_max_drawdown": self._safe_float(benchmark_max_drawdown),
                "benchmark_sharpe": self._safe_float(benchmark_sharpe),
                "benchmark_sortino": self._safe_float(benchmark_sortino),
                "benchmark_calmar": self._safe_float(benchmark_calmar),
                "benchmark_var_95": self._safe_float(benchmark_var_95),
                "benchmark_cvar_95": self._safe_float(benchmark_cvar_95),
                "benchmark_skewness": self._safe_float(benchmark_skewness),
                "benchmark_kurtosis": self._safe_float(benchmark_kurtosis),
                "benchmark_ulcer_index": self._safe_float(benchmark_ulcer_index),
                "benchmark_tail_ratio": self._safe_float(benchmark_tail_ratio),
                "benchmark_kelly_criterion": self._safe_float(benchmark_kelly),
                "benchmark_omega_ratio": self._safe_float(benchmark_omega),
                "benchmark_gain_to_pain_ratio": self._safe_float(benchmark_gain_to_pain),
                "benchmark_common_sense_ratio": self._safe_float(benchmark_common_sense),
                "benchmark_recovery_factor": self._safe_float(benchmark_recovery),
                "benchmark_risk_return_ratio": self._safe_float(benchmark_risk_return),
                "benchmark_ulcer_performance_index": self._safe_float(benchmark_upi),
                # 对比指标
                "alpha": self._safe_float(alpha),
                "beta": self._safe_float(beta, 1.0),
                "correlation": self._safe_float(correlation),
                "information_ratio": self._safe_float(info_ratio),
                "tracking_error": self._safe_float(tracking_error),
                "up_capture": self._safe_float(up_capture, 1.0),
                "down_capture": self._safe_float(down_capture, 1.0),
            }
            
        except Exception as e:
            logger.error(f"计算基准指标失败 {benchmark}: {e}")
            return None
    
    def calculate_benchmark_comparison(
        self, 
        returns: pd.Series, 
        benchmark: str
    ) -> Optional[Dict[str, Any]]:
        """
        计算与基准的对比指标（兼容旧接口）
        
        :param returns: 组合日收益率序列
        :param benchmark: 基准代码
        :return: 基准对比指标字典
        """
        # 调用新方法获取完整指标
        full_metrics = self.calculate_benchmark_metrics(returns, benchmark)
        
        if full_metrics is None:
            return None
        
        # 返回兼容旧格式的数据
        return {
            "benchmark_name": full_metrics["benchmark_name"],
            "benchmark_return": full_metrics["benchmark_return"],
            "alpha": full_metrics["alpha"],
            "beta": full_metrics["beta"],
            "correlation": full_metrics["correlation"],
            "information_ratio": full_metrics["information_ratio"],
            "tracking_error": full_metrics["tracking_error"],
            "up_capture": full_metrics["up_capture"],
            "down_capture": full_metrics["down_capture"],
        }
    
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
        for benchmark in config.LONGPORT_BENCHMARKS.keys():
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
                    "drawdown": self._safe_float(row['max drawdown']),
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
                    "return_value": self._safe_float(value),
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
                    str(year): self._safe_float(value),
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
        # 使用新方法获取 benchmark 完整指标
        benchmark_metrics = self.calculate_benchmark_metrics(returns, benchmark)
        
        return {
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
            "trading_days": len(returns),
            "initial_value": self._safe_float(equity.iloc[0]),
            "final_value": self._safe_float(equity.iloc[-1]),
            "returns": return_metrics,
            "risk": risk_metrics,
            "benchmark": benchmark_metrics,
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
            {"date": d.strftime("%Y-%m-%d"), "value": self._safe_float(v, 1.0)}
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
                    {"date": d.strftime("%Y-%m-%d"), "value": self._safe_float(v, 1.0)}
                    for d, v in bench_cumulative.items()
                ]
        
        return {
            "period": period,
            "portfolio": portfolio_data,
            "benchmark": benchmark_data,
        }


# 全局单例
analytics_service = AnalyticsService()

