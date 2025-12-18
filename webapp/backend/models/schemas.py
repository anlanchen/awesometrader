#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pydantic 数据模型定义
"""

from datetime import date
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


# ==================== 请求参数 ====================

class AnalyticsQuery(BaseModel):
    """分析查询参数"""
    period: str = Field(default="all", description="时间周期: 7d, 1m, 6m, 1y, all, mtd, ytd")
    benchmark: str = Field(default="sp500", description="基准指数: sp500, nasdaq100, csi300, a500, hstech")


# ==================== 响应模型 ====================

class ReturnMetrics(BaseModel):
    """收益指标"""
    cumulative_return: float = Field(..., description="累计收益率")
    annualized_return: float = Field(..., description="年化收益率")
    ytd_return: Optional[float] = Field(None, description="年初至今收益率")
    mtd_return: Optional[float] = Field(None, description="本月至今收益率")
    daily_return_mean: float = Field(..., description="日均收益率")
    daily_return_std: float = Field(..., description="日收益率标准差")
    best_day: float = Field(..., description="最佳单日收益")
    worst_day: float = Field(..., description="最差单日收益")
    win_rate: float = Field(..., description="胜率")
    avg_win: float = Field(default=0.0, description="平均盈利")
    avg_loss: float = Field(default=0.0, description="平均亏损")
    profit_factor: float = Field(default=0.0, description="利润因子")
    payoff_ratio: float = Field(default=0.0, description="盈亏比")
    expectancy: float = Field(default=0.0, description="期望收益")
    geometric_mean: float = Field(default=0.0, description="几何平均")
    expected_monthly: float = Field(default=0.0, description="期望月收益")
    expected_yearly: float = Field(default=0.0, description="期望年收益")
    

class RiskMetrics(BaseModel):
    """风险指标"""
    volatility: float = Field(..., description="年化波动率")
    max_drawdown: float = Field(..., description="最大回撤")
    max_drawdown_duration: Optional[int] = Field(None, description="最大回撤持续天数")
    sharpe_ratio: float = Field(..., description="夏普比率")
    sortino_ratio: float = Field(..., description="索提诺比率")
    calmar_ratio: float = Field(..., description="卡玛比率")
    var_95: float = Field(..., description="95% VaR")
    cvar_95: float = Field(..., description="95% CVaR (条件风险价值)")
    skewness: float = Field(..., description="偏度")
    kurtosis: float = Field(..., description="峰度")
    ulcer_index: float = Field(default=0.0, description="溃疡指数")
    tail_ratio: float = Field(default=0.0, description="尾部比率")
    kelly_criterion: float = Field(default=0.0, description="凯利公式")
    omega_ratio: float = Field(default=0.0, description="欧米伽比率")
    gain_to_pain_ratio: float = Field(default=0.0, description="增益痛苦比")
    common_sense_ratio: float = Field(default=0.0, description="常识比率")
    recovery_factor: float = Field(default=0.0, description="恢复因子")
    risk_return_ratio: float = Field(default=0.0, description="风险收益比")
    ulcer_performance_index: float = Field(default=0.0, description="溃疡表现指数")


class BenchmarkComparison(BaseModel):
    """基准对比指标（简化版，用于兼容旧接口）"""
    benchmark_name: str = Field(..., description="基准名称")
    benchmark_return: float = Field(..., description="基准收益率")
    alpha: float = Field(..., description="Alpha")
    beta: float = Field(..., description="Beta")
    correlation: float = Field(..., description="相关系数")
    information_ratio: float = Field(..., description="信息比率")
    tracking_error: float = Field(..., description="跟踪误差")
    up_capture: float = Field(..., description="上涨捕获率")
    down_capture: float = Field(..., description="下跌捕获率")


class BenchmarkMetrics(BaseModel):
    """基准完整指标（包含收益、风险和对比指标）"""
    benchmark_name: str = Field(..., description="基准名称")
    # 收益指标
    benchmark_return: float = Field(..., description="基准累计收益率")
    benchmark_cagr: float = Field(default=0.0, description="基准年化收益率")
    benchmark_daily_mean: float = Field(default=0.0, description="基准日均收益率")
    benchmark_daily_std: float = Field(default=0.0, description="基准日收益率标准差")
    benchmark_best_day: float = Field(default=0.0, description="基准最佳单日收益")
    benchmark_worst_day: float = Field(default=0.0, description="基准最差单日收益")
    benchmark_win_rate: float = Field(default=0.0, description="基准胜率")
    benchmark_avg_win: float = Field(default=0.0, description="基准平均盈利")
    benchmark_avg_loss: float = Field(default=0.0, description="基准平均亏损")
    benchmark_profit_factor: float = Field(default=0.0, description="基准利润因子")
    benchmark_payoff_ratio: float = Field(default=0.0, description="基准盈亏比")
    benchmark_expectancy: float = Field(default=0.0, description="基准期望收益")
    benchmark_geometric_mean: float = Field(default=0.0, description="基准几何平均")
    benchmark_expected_monthly: float = Field(default=0.0, description="基准期望月收益")
    benchmark_expected_yearly: float = Field(default=0.0, description="基准期望年收益")
    # 风险指标
    benchmark_volatility: float = Field(default=0.0, description="基准年化波动率")
    benchmark_max_drawdown: float = Field(default=0.0, description="基准最大回撤")
    benchmark_sharpe: float = Field(default=0.0, description="基准夏普比率")
    benchmark_sortino: float = Field(default=0.0, description="基准索提诺比率")
    benchmark_calmar: float = Field(default=0.0, description="基准卡玛比率")
    benchmark_var_95: float = Field(default=0.0, description="基准95% VaR")
    benchmark_cvar_95: float = Field(default=0.0, description="基准95% CVaR")
    benchmark_skewness: float = Field(default=0.0, description="基准偏度")
    benchmark_kurtosis: float = Field(default=0.0, description="基准峰度")
    benchmark_ulcer_index: float = Field(default=0.0, description="基准溃疡指数")
    benchmark_tail_ratio: float = Field(default=0.0, description="基准尾部比率")
    benchmark_kelly_criterion: float = Field(default=0.0, description="基准凯利公式")
    benchmark_omega_ratio: float = Field(default=0.0, description="基准欧米伽比率")
    benchmark_gain_to_pain_ratio: float = Field(default=0.0, description="基准增益痛苦比")
    benchmark_common_sense_ratio: float = Field(default=0.0, description="基准常识比率")
    benchmark_recovery_factor: float = Field(default=0.0, description="基准恢复因子")
    benchmark_risk_return_ratio: float = Field(default=0.0, description="基准风险收益比")
    benchmark_ulcer_performance_index: float = Field(default=0.0, description="基准溃疡表现指数")
    # 对比指标
    alpha: float = Field(..., description="Alpha")
    beta: float = Field(..., description="Beta")
    correlation: float = Field(..., description="相关系数")
    information_ratio: float = Field(..., description="信息比率")
    tracking_error: float = Field(..., description="跟踪误差")
    up_capture: float = Field(..., description="上涨捕获率")
    down_capture: float = Field(..., description="下跌捕获率")


class DrawdownInfo(BaseModel):
    """回撤信息"""
    start_date: date = Field(..., description="回撤开始日期")
    end_date: Optional[date] = Field(None, description="回撤结束日期")
    recovery_date: Optional[date] = Field(None, description="恢复日期")
    drawdown: float = Field(..., description="回撤幅度")
    duration: int = Field(..., description="回撤持续天数")
    recovery_days: Optional[int] = Field(None, description="恢复天数")


class MonthlyReturn(BaseModel):
    """月度收益"""
    year: int
    month: int
    return_value: float


class TimeSeriesPoint(BaseModel):
    """时间序列数据点"""
    date: str
    value: float


class DrawdownPoint(BaseModel):
    """回撤序列数据点"""
    date: str
    drawdown: float


class ReturnPoint(BaseModel):
    """收益率序列数据点"""
    date: str
    return_value: float = Field(..., alias="return")


class OverviewResponse(BaseModel):
    """总览响应"""
    period: str
    start_date: date
    end_date: date
    trading_days: int
    initial_value: float
    final_value: float
    returns: ReturnMetrics
    risk: RiskMetrics
    benchmark: Optional[BenchmarkMetrics] = None


class ReturnsResponse(BaseModel):
    """收益分析响应"""
    period: str
    metrics: ReturnMetrics
    daily_returns: List[Dict[str, str | float]] = Field(..., description="每日收益率序列")


class RiskResponse(BaseModel):
    """风险指标响应"""
    period: str
    metrics: RiskMetrics


class BenchmarkResponse(BaseModel):
    """基准对比响应"""
    period: str
    portfolio_return: float
    benchmarks: List[BenchmarkComparison]


class DrawdownResponse(BaseModel):
    """回撤分析响应"""
    period: str
    current_drawdown: float
    max_drawdown: float
    drawdown_series: List[Dict[str, str | float]] = Field(..., description="回撤序列")
    worst_drawdowns: List[DrawdownInfo] = Field(..., description="最差回撤列表")


class MonthlyResponse(BaseModel):
    """月度收益响应"""
    period: str
    monthly_returns: List[MonthlyReturn]
    yearly_returns: List[Dict[str, float]]


class EquityCurveResponse(BaseModel):
    """资产曲线响应"""
    period: str
    portfolio: List[Dict[str, str | float]] = Field(..., description="组合资产曲线")
    benchmark: Optional[List[Dict[str, str | float]]] = Field(None, description="基准资产曲线")


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    detail: Optional[str] = None

