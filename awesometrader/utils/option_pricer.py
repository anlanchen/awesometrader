#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期权定价工具模块

使用 Black-Scholes 模型进行期权定价，支持：
- Black-Scholes 期权定价
- Greeks 计算 (Delta, Gamma, Theta, Vega, Rho)
- 隐含波动率计算
"""

import re
import math
from datetime import date
from typing import Optional, Dict, Any
from dataclasses import dataclass

from scipy.stats import norm
from scipy.optimize import brentq


@dataclass
class OptionInfo:
    """期权信息"""
    underlying: str        # 标的代码 (e.g., 'CRCL')
    expiry_date: date      # 到期日
    option_type: str       # 'C' for Call, 'P' for Put
    strike_price: float    # 行权价
    full_symbol: str       # 完整期权代码
    market: str            # 市场 (e.g., 'US', 'HK')


def parse_option_symbol(symbol: str) -> Optional[OptionInfo]:
    """
    解析期权代码
    
    美股期权格式: {UNDERLYING}{YYMMDD}{C/P}{STRIKE*1000}.US
    例如: CRCL260618C120000.US -> CRCL, 2026-06-18, Call, $120
    """
    us_pattern = r'^([A-Z]+)(\d{6})([CP])(\d+)\.US$'
    hk_pattern = r'^(\d+)(\d{6})([CP])(\d+)\.HK$'
    
    match = re.match(us_pattern, symbol)
    market = 'US'
    if not match:
        match = re.match(hk_pattern, symbol)
        market = 'HK'
    
    if not match:
        return None
    
    underlying, date_str, option_type, strike_str = match.groups()
    
    try:
        expiry_date = date(2000 + int(date_str[:2]), int(date_str[2:4]), int(date_str[4:6]))
        strike_price = float(strike_str) / 1000.0
        
        return OptionInfo(
            underlying=underlying,
            expiry_date=expiry_date,
            option_type=option_type,
            strike_price=strike_price,
            full_symbol=symbol,
            market=market
        )
    except (ValueError, IndexError):
        return None


def is_option_symbol(symbol: str) -> bool:
    """判断是否为期权代码"""
    return parse_option_symbol(symbol) is not None


def _d1(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """计算 d1"""
    return (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))


def _d2(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """计算 d2"""
    return _d1(S, K, T, r, sigma) - sigma * math.sqrt(T)


def _bs_call_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Black-Scholes Call 期权价格"""
    d1 = _d1(S, K, T, r, sigma)
    d2 = _d2(S, K, T, r, sigma)
    return S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)


def _bs_put_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Black-Scholes Put 期权价格"""
    d1 = _d1(S, K, T, r, sigma)
    d2 = _d2(S, K, T, r, sigma)
    return K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)


def black_scholes_price(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: str
) -> Dict[str, float]:
    """
    计算期权价格和Greeks
    
    Args:
        S: 标的资产现价
        K: 行权价
        T: 到期时间（年）
        r: 无风险利率
        sigma: 波动率
        option_type: 'c'/'C' Call, 'p'/'P' Put
    """
    flag = option_type.lower()
    d1 = _d1(S, K, T, r, sigma)
    d2 = _d2(S, K, T, r, sigma)
    sqrt_T = math.sqrt(T)
    
    # 期权价格
    if flag == 'c':
        price = _bs_call_price(S, K, T, r, sigma)
        delta_val = norm.cdf(d1)
        theta_val = (
            -S * norm.pdf(d1) * sigma / (2 * sqrt_T)
            - r * K * math.exp(-r * T) * norm.cdf(d2)
        )
        rho_val = K * T * math.exp(-r * T) * norm.cdf(d2)
    else:
        price = _bs_put_price(S, K, T, r, sigma)
        delta_val = norm.cdf(d1) - 1
        theta_val = (
            -S * norm.pdf(d1) * sigma / (2 * sqrt_T)
            + r * K * math.exp(-r * T) * norm.cdf(-d2)
        )
        rho_val = -K * T * math.exp(-r * T) * norm.cdf(-d2)
    
    # Gamma 和 Vega 对 Call 和 Put 相同
    gamma_val = norm.pdf(d1) / (S * sigma * sqrt_T)
    vega_val = S * norm.pdf(d1) * sqrt_T
    
    return {
        'price': float(price),
        'delta': float(delta_val),
        'gamma': float(gamma_val),
        'theta': float(theta_val / 365),  # 每日 theta
        'vega': float(vega_val / 100),    # 每 1% 波动率变化
        'rho': float(rho_val / 100),      # 每 1% 利率变化
    }


def calculate_implied_volatility(
    price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    option_type: str
) -> Optional[float]:
    """计算隐含波动率"""
    flag = option_type.lower()
    
    def objective(sigma):
        if flag == 'c':
            return _bs_call_price(S, K, T, r, sigma) - price
        else:
            return _bs_put_price(S, K, T, r, sigma) - price
    
    try:
        # 使用 Brent 方法求解隐含波动率，搜索范围 0.01% ~ 500%
        iv = brentq(objective, 0.0001, 5.0)
        return float(iv)
    except (ValueError, RuntimeError):
        return None


def price_option(
    option_info: OptionInfo,
    underlying_price: float,
    risk_free_rate: float = 0.04,
    volatility: float = 0.50,
    reference_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    计算期权理论价格和Greeks
    
    Args:
        option_info: 期权信息
        underlying_price: 标的现价
        risk_free_rate: 无风险利率（默认4%）
        volatility: 波动率（默认50%）
        reference_date: 参考日期（默认今天）
    """
    if reference_date is None:
        reference_date = date.today()
    
    T = max((option_info.expiry_date - reference_date).days / 365.0, 0.001)
    
    result = black_scholes_price(
        S=underlying_price,
        K=option_info.strike_price,
        T=T,
        r=risk_free_rate,
        sigma=volatility,
        option_type=option_info.option_type
    )
    
    # 内在价值
    if option_info.option_type.upper() == 'C':
        intrinsic_value = max(underlying_price - option_info.strike_price, 0)
    else:
        intrinsic_value = max(option_info.strike_price - underlying_price, 0)
    
    return {
        'theoretical_price': float(result['price']),
        'intrinsic_value': float(intrinsic_value),
        'time_value': float(max(result['price'] - intrinsic_value, 0)),
        'time_to_expiry_days': int(T * 365),
        'volatility_used': float(volatility),
        'underlying_price': float(underlying_price),
        'strike_price': float(option_info.strike_price),
        'option_type': 'Call' if option_info.option_type == 'C' else 'Put',
        **result,
    }


if __name__ == '__main__':
    # 测试
    symbol = 'CRCL260618C120000.US'
    info = parse_option_symbol(symbol)
    
    if info:
        print(f"期权: {symbol}")
        print(f"  标的: {info.underlying}, 行权价: ${info.strike_price}, 到期: {info.expiry_date}")
        
        pricing = price_option(info, underlying_price=75.46, volatility=0.50)
        print(f"  理论价格: ${pricing['theoretical_price']:.4f}")
        print(f"  Delta: {pricing['delta']:.4f}, Gamma: {pricing['gamma']:.6f}")
        print(f"  剩余: {pricing['time_to_expiry_days']}天")
