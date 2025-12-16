#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期权定价工具模块

使用 py_vollib 库进行期权定价，支持：
- Black-Scholes 期权定价
- Greeks 计算 (Delta, Gamma, Theta, Vega, Rho)
- 隐含波动率计算
"""

import re
from datetime import date
from typing import Optional, Dict, Any
from dataclasses import dataclass

from py_vollib.black_scholes import black_scholes as bs_price
from py_vollib.black_scholes.greeks.analytical import delta, gamma, theta, vega, rho
from py_vollib.black_scholes.implied_volatility import implied_volatility


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


def black_scholes_price(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: str
) -> Dict[str, float]:
    """
    使用 py_vollib 计算期权价格和Greeks
    
    Args:
        S: 标的资产现价
        K: 行权价
        T: 到期时间（年）
        r: 无风险利率
        sigma: 波动率
        option_type: 'c'/'C' Call, 'p'/'P' Put
    """
    flag = option_type.lower()
    
    # 使用 float() 确保返回 Python 原生类型（而非 numpy 类型），以支持 JSON 序列化
    return {
        'price': float(bs_price(flag, S, K, T, r, sigma)),
        'delta': float(delta(flag, S, K, T, r, sigma)),
        'gamma': float(gamma(flag, S, K, T, r, sigma)),
        'theta': float(theta(flag, S, K, T, r, sigma) / 365),
        'vega': float(vega(flag, S, K, T, r, sigma) / 100),
        'rho': float(rho(flag, S, K, T, r, sigma) / 100),
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
    try:
        return implied_volatility(price, S, K, T, r, option_type.lower())
    except Exception:
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
