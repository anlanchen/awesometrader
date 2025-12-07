#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
汇率查询工具

提供汇率获取、币种转换等功能，支持 USD, HKD, CNH 三种币种。
"""

import os
import sys
import argparse
import requests
from datetime import datetime, timedelta
from typing import Dict, Any
from loguru import logger

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ExchangeRateService:
    """汇率服务类"""

    # 币种与市场的映射关系
    MARKET_CURRENCY_MAP = {
        'US': 'USD',
        'HK': 'HKD',
        'CN': 'CNH',
    }
    
    def __init__(self):
        """初始化汇率服务"""

        # 汇率缓存，以基准币种为key，包含汇率数据和时间戳
        # 结构: {base_currency: {'rates': {...}, 'timestamp': datetime}}
        self._exchange_rates: Dict[str, Dict[str, Any]] = {}

        # 缓存有效期（1天）
        self._cache_ttl = timedelta(days=1)

        logger.info("汇率服务初始化完成")
    
    def get_exchange_rates(self, base_currency: str = 'CNH') -> Dict[str, float]:
        """
        获取汇率数据
        
        Args:
            base_currency: 基准币种 (USD, HKD, CNH)，所有汇率以此币种为基准
            
        Returns:
            Dict[str, float]: 汇率字典，key为币种，value为对基准币种的汇率
        """
        try:
            # 如果已缓存且未过期，直接返回
            if base_currency in self._exchange_rates:
                cache_data = self._exchange_rates[base_currency]
                cache_time = cache_data.get('timestamp')
                if cache_time and datetime.now() - cache_time < self._cache_ttl:
                    return cache_data['rates']
                else:
                    logger.info(f"缓存已过期，重新获取汇率数据，基准币种: {base_currency}")

            logger.info(f"正在获取汇率数据，基准币种: {base_currency}")
            
            # 使用免费的汇率API（exchangerate-api.com）
            # CNH需要映射为CNY
            api_base = 'CNY' if base_currency == 'CNH' else base_currency
            url = f"https://api.exchangerate-api.com/v4/latest/{api_base}"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                rates = data.get('rates', {})
                
                # 构建汇率字典（相对于base_currency）
                rates_data = {}
                if base_currency == 'CNH':
                    rates_data = {
                        'USD': 1.0 / rates.get('USD', 1.0),
                        'HKD': 1.0 / rates.get('HKD', 1.0),
                        'CNH': 1.0,
                    }
                elif base_currency == 'USD':
                    rates_data = {
                        'USD': 1.0,
                        'HKD': rates.get('HKD', 7.8),
                        'CNH': rates.get('CNY', 7.2),
                    }
                elif base_currency == 'HKD':
                    rates_data = {
                        'USD': rates.get('USD', 0.128),
                        'HKD': 1.0,
                        'CNH': rates.get('CNY', 0.92),
                    }

                # 保存汇率数据和时间戳
                self._exchange_rates[base_currency] = {
                    'rates': rates_data,
                    'timestamp': datetime.now()
                }

                logger.success(f"成功获取汇率数据: {rates_data}")
                return rates_data
            else:
                logger.warning(f"获取汇率失败，使用默认汇率，HTTP状态码: {response.status_code}")
                return self._get_default_exchange_rates(base_currency)
                
        except Exception as e:
            logger.warning(f"获取汇率数据失败: {e}，使用默认汇率")
            return self._get_default_exchange_rates(base_currency)
    
    def _get_default_exchange_rates(self, base_currency: str) -> Dict[str, float]:
        """获取默认汇率（当API调用失败时使用）"""
        if base_currency == 'CNH':
            return {
                'USD': 7.08,   # 1 USD = 7.08 CNH
                'HKD': 0.92,   # 1 HKD = 0.92 CNH
                'CNH': 1.0,
            }
        elif base_currency == 'USD':
            return {
                'USD': 1.0,
                'HKD': 0.129,  # 1 HKD = 0.129 USD
                'CNH': 0.142,  # 1 CNH = 0.142 USD
            }
        elif base_currency == 'HKD':
            return {
                'USD': 7.77,    # 1 USD = 7.77 HKD
                'HKD': 1.0,
                'CNH': 1.10,   # 1 CNH = 1.10 HKD
            }
        else:
            return {
                'USD': 1.0,
                'HKD': 1.0,
                'CNH': 1.0,
            }
    
    def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> float:
        """
        币种转换
        
        Args:
            amount: 金额
            from_currency: 源币种
            to_currency: 目标币种
            
        Returns:
            float: 转换后的金额
        """
        if from_currency == to_currency:
            return amount
        
        rates = self.get_exchange_rates(to_currency)
        rate = rates.get(from_currency, 1.0)
        return amount * rate
    
    def clear_cache(self) -> None:
        """清除汇率缓存"""
        self._exchange_rates = {}
        logger.info("汇率缓存已清除")

    def query_exchange_rates(self, base_currency: str = 'CNH') -> None:
        """
        查询并显示汇率信息
        
        Args:
            base_currency: 基准币种 (USD, HKD, CNH)，默认为 CNH
        """
        try:
            logger.info(f"开始查询汇率，基准币种: {base_currency}")
            
            # 清除缓存以获取最新汇率
            self.clear_cache()
            rates = self.get_exchange_rates(base_currency)
            
            if not rates:
                logger.warning("未能获取汇率信息")
                return
            
            # 格式化输出内容
            output_lines = []
            output_lines.append("=" * 60)
            output_lines.append("汇率信息")
            output_lines.append("=" * 60)
            output_lines.append(f"查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            output_lines.append(f"基准币种: {base_currency}")
            output_lines.append("")
            output_lines.append("【当前汇率】")
            output_lines.append("-" * 60)
            
            for curr, rate in rates.items():
                if curr != base_currency:
                    output_lines.append(f"  1 {curr} = {rate:.4f} {base_currency}")

            output_lines.append("")
            output_lines.append("=" * 60)
            
            output_content = "\n".join(output_lines)

            # 输出到控制台
            print(output_content)

        except Exception as e:
            logger.error(f"查询汇率失败: {e}")
    
def main():
    """主函数"""
    # 配置日志
    logger.remove()
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="INFO"
    )
    
    # 创建主解析器
    parser = argparse.ArgumentParser(
        description="汇率查询工具 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查询汇率（以人民币为基准）
  python exchange_rate.py rates
  
  # 查询汇率（以美元为基准）
  python exchange_rate.py rates --base-currency USD
"""
    )
    
    # 创建子命令解析器
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 子命令: rates
    parser_rates = subparsers.add_parser(
        "rates",
        help="查询当前汇率"
    )
    parser_rates.add_argument(
        "--base-currency",
        choices=['USD', 'HKD', 'CNH'],
        default='CNH',
        help="基准币种，所有汇率以此币种为基准 (可选: USD, HKD, CNH，默认: CNH)"
    )
    
    # 解析参数
    args = parser.parse_args()
    
    # 如果没有提供命令，显示帮助信息
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # 初始化服务
    try:
        service = ExchangeRateService()
        
        # 执行对应的命令
        if args.command == "rates":
            service.query_exchange_rates(base_currency=args.base_currency)
        
    
    except KeyboardInterrupt:
        logger.info("用户中断操作")
        sys.exit(0)
    except Exception as e:
        logger.error(f"执行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
