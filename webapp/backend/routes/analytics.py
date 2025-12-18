#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
分析 API 路由
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from loguru import logger

from ..models.schemas import (
    OverviewResponse,
    ReturnsResponse,
    RiskResponse,
    BenchmarkResponse,
    DrawdownResponse,
    MonthlyResponse,
    EquityCurveResponse,
    ReturnMetrics,
    RiskMetrics,
    BenchmarkComparison,
    BenchmarkMetrics,
    DrawdownInfo,
    MonthlyReturn,
)
from ..services.analytics_service import analytics_service
from ..services.data_loader import data_loader
from ..config import config


router = APIRouter(prefix="/analytics", tags=["Analytics"])


def validate_period(period: str) -> str:
    """验证时间周期参数"""
    valid_periods = list(config.PERIOD_DAYS.keys())
    if period not in valid_periods:
        raise HTTPException(
            status_code=400, 
            detail=f"无效的时间周期: {period}，可选: {valid_periods}"
        )
    return period


def validate_benchmark(benchmark: str) -> str:
    """验证基准参数"""
    # 合并 yfinance 和 akshare 两个数据源的基准
    valid_benchmarks = list(config.BENCHMARK_SYMBOLS.keys()) + list(config.AKSHARE_BENCHMARKS.keys())
    if benchmark not in valid_benchmarks:
        raise HTTPException(
            status_code=400,
            detail=f"无效的基准: {benchmark}，可选: {valid_benchmarks}"
        )
    return benchmark


@router.get("/overview", response_model=OverviewResponse, summary="获取总览数据")
async def get_overview(
    period: str = Query(default="all", description="时间周期: 7d, 1m, 6m, 1y, all, mtd, ytd"),
    benchmark: str = Query(default="sp500", description="基准指数: sp500, nasdaq100, csi300, a500, hstech")
):
    """
    获取账户分析总览数据，包含收益指标、风险指标和基准对比
    """
    try:
        period = validate_period(period)
        benchmark = validate_benchmark(benchmark)
        
        result = analytics_service.get_overview(period, benchmark)
        
        return OverviewResponse(
            period=result["period"],
            start_date=result["start_date"],
            end_date=result["end_date"],
            trading_days=result["trading_days"],
            initial_value=result["initial_value"],
            final_value=result["final_value"],
            returns=ReturnMetrics(**result["returns"]),
            risk=RiskMetrics(**result["risk"]),
            benchmark=BenchmarkMetrics(**result["benchmark"]) if result["benchmark"] else None,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取总览数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {e}")


@router.get("/returns", response_model=ReturnsResponse, summary="获取收益分析")
async def get_returns(
    period: str = Query(default="all", description="时间周期")
):
    """
    获取收益分析数据，包含收益指标和每日收益率序列
    """
    try:
        period = validate_period(period)
        
        returns = data_loader.get_filtered_returns(period)
        
        if returns.empty:
            raise HTTPException(status_code=404, detail="没有找到数据")
        
        metrics = analytics_service.calculate_return_metrics(returns)
        
        daily_returns = [
            {"date": d.strftime("%Y-%m-%d"), "return": float(v)}
            for d, v in returns.items()
        ]
        
        return ReturnsResponse(
            period=period,
            metrics=ReturnMetrics(**metrics),
            daily_returns=daily_returns,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取收益分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {e}")


@router.get("/risk", response_model=RiskResponse, summary="获取风险指标")
async def get_risk(
    period: str = Query(default="all", description="时间周期")
):
    """
    获取风险指标数据
    """
    try:
        period = validate_period(period)
        
        returns = data_loader.get_filtered_returns(period)
        
        if returns.empty:
            raise HTTPException(status_code=404, detail="没有找到数据")
        
        metrics = analytics_service.calculate_risk_metrics(returns)
        
        return RiskResponse(
            period=period,
            metrics=RiskMetrics(**metrics),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取风险指标失败: {e}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {e}")


@router.get("/benchmark", response_model=BenchmarkResponse, summary="获取基准对比")
async def get_benchmark(
    period: str = Query(default="all", description="时间周期"),
    benchmark: Optional[str] = Query(default=None, description="指定单个基准，不指定则返回所有基准")
):
    """
    获取与基准指数的对比数据
    """
    try:
        period = validate_period(period)
        
        returns = data_loader.get_filtered_returns(period)
        
        if returns.empty:
            raise HTTPException(status_code=404, detail="没有找到数据")
        
        portfolio_return = float((1 + returns).prod() - 1)
        
        if benchmark:
            benchmark = validate_benchmark(benchmark)
            comparison = analytics_service.calculate_benchmark_comparison(returns, benchmark)
            benchmarks = [BenchmarkComparison(**comparison)] if comparison else []
        else:
            all_comparisons = analytics_service.calculate_all_benchmarks(returns)
            benchmarks = [BenchmarkComparison(**c) for c in all_comparisons]
        
        return BenchmarkResponse(
            period=period,
            portfolio_return=portfolio_return,
            benchmarks=benchmarks,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取基准对比失败: {e}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {e}")


@router.get("/drawdown", response_model=DrawdownResponse, summary="获取回撤分析")
async def get_drawdown(
    period: str = Query(default="all", description="时间周期"),
    top_n: int = Query(default=5, ge=1, le=20, description="返回最差的N次回撤")
):
    """
    获取回撤分析数据
    """
    try:
        period = validate_period(period)
        
        returns = data_loader.get_filtered_returns(period)
        
        if returns.empty:
            raise HTTPException(status_code=404, detail="没有找到数据")
        
        # 计算回撤序列
        drawdown_series = analytics_service.calculate_drawdown_series(returns)
        
        # 当前回撤
        current_drawdown = float(drawdown_series.iloc[-1]) if not drawdown_series.empty else 0.0
        
        # 最大回撤
        max_drawdown = float(drawdown_series.min()) if not drawdown_series.empty else 0.0
        
        # 回撤序列数据
        dd_data = [
            {"date": d.strftime("%Y-%m-%d"), "drawdown": float(v)}
            for d, v in drawdown_series.items()
        ]
        
        # 最差回撤列表
        worst_drawdowns = analytics_service.get_worst_drawdowns(returns, top_n)
        worst_dd_models = [DrawdownInfo(**dd) for dd in worst_drawdowns]
        
        return DrawdownResponse(
            period=period,
            current_drawdown=current_drawdown,
            max_drawdown=max_drawdown,
            drawdown_series=dd_data,
            worst_drawdowns=worst_dd_models,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取回撤分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {e}")


@router.get("/monthly", response_model=MonthlyResponse, summary="获取月度收益")
async def get_monthly(
    period: str = Query(default="all", description="时间周期")
):
    """
    获取月度和年度收益数据
    """
    try:
        period = validate_period(period)
        
        returns = data_loader.get_filtered_returns(period)
        
        if returns.empty:
            raise HTTPException(status_code=404, detail="没有找到数据")
        
        monthly_returns = analytics_service.calculate_monthly_returns(returns)
        yearly_returns = analytics_service.calculate_yearly_returns(returns)
        
        return MonthlyResponse(
            period=period,
            monthly_returns=[MonthlyReturn(**m) for m in monthly_returns],
            yearly_returns=yearly_returns,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取月度收益失败: {e}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {e}")


@router.get("/equity-curve", response_model=EquityCurveResponse, summary="获取资产曲线")
async def get_equity_curve(
    period: str = Query(default="all", description="时间周期"),
    benchmark: Optional[str] = Query(default=None, description="基准指数（可选）")
):
    """
    获取资产曲线数据，用于绑图展示
    """
    try:
        period = validate_period(period)
        
        if benchmark:
            benchmark = validate_benchmark(benchmark)
        
        result = analytics_service.get_equity_curve_data(period, benchmark)
        
        return EquityCurveResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取资产曲线失败: {e}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {e}")


@router.get("/periods", summary="获取可用的时间周期")
async def get_periods():
    """获取所有可用的时间周期选项"""
    return {
        "periods": [
            {"code": "7d", "name": "7天"},
            {"code": "1m", "name": "1个月"},
            {"code": "6m", "name": "6个月"},
            {"code": "1y", "name": "1年"},
            {"code": "all", "name": "全部"},
            {"code": "mtd", "name": "本月"},
            {"code": "ytd", "name": "本年"},
        ]
    }


@router.get("/benchmarks", summary="获取可用的基准指数")
async def get_benchmarks():
    """获取所有可用的基准指数选项"""
    return {
        "benchmarks": [
            {"code": "sp500", "name": "标普500", "symbol": "^GSPC"},
            {"code": "nasdaq100", "name": "纳斯达克100", "symbol": "^NDX"},
            {"code": "csi300", "name": "沪深300", "symbol": "000300.SS"},
            {"code": "a500", "name": "中证500ETF", "symbol": "510500.SS"},
            {"code": "hstech", "name": "恒生科技ETF", "symbol": "3032.HK"},
        ]
    }

