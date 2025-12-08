#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
from loguru import logger

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from awesometrader import LongPortTradeAPI
from awesometrader import LongPortQuotaAPI
from tasks.exchange_rate import ExchangeRateService

class LongPortTradeCLI:
    """交易账户查询CLI"""

    def __init__(self, initial_capital: float = 1500000.0):
        """初始化交易CLI"""
        self.trader = LongPortTradeAPI()
        self.quote_api = LongPortQuotaAPI()
        self.exchange_rate_service = ExchangeRateService()
        
        self.initial_capital = initial_capital
        
        # 创建输出目录
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'caches', 'account')
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info("交易CLI初始化完成")

    def _get_output_filename(self, command: str, extension: str = 'txt') -> str:
        """生成输出文件名"""
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"{command}_{timestamp}.{extension}"
        return os.path.join(self.output_dir, filename)
    
    def _save_to_file(content: str, filepath: str) -> None:
        """保存内容到文件"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.success(f"结果已保存到: {filepath}")
        except Exception as e:
            logger.error(f"保存文件失败: {e}")
    
    def get_stock_quote_data(self, symbols: List[str]) -> Dict[str, float]:
        """批量获取股票报价数据"""
        try:
            quotes_dict = self.quote_api.get_stock_quote(symbols)
            quote_data = {}
            for symbol, quote in quotes_dict.items():
                quote_data[symbol] = float(quote.last_done)
            return quote_data
        except Exception as e:
            logger.error(f"批量获取股票报价失败: {e}")
            return {}

    def calculate_account_metrics(self, currency: str = 'CNH', adjustments: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """计算账户各项指标

        总资产净值 = 所有币种现金余额 + 所有市场持仓市值 + 调整金额，并根据当前选择币种折算展示

        Args:
            currency: 目标币种 (USD, HKD, CNH)，默认为 CNH
            adjustments: 资金调整字典，键为币种，值为调整金额（可正可负），例如：{'USD': 2000, 'HKD': -200}
        """
        if adjustments is None:
            adjustments = {}
        try:
            # 获取所有币种的账户余额信息
            balances = self.trader.get_account_balance(currency=currency)
            # 获取持仓信息
            positions = self.trader.get_stock_positions()

            if not balances:
                logger.error("无法获取账户余额信息")
                return {}

            # 获取汇率
            exchange_rates = self.exchange_rate_service.get_exchange_rates(currency)

            # 计算所有币种现金余额（折算到目标币种）
            total_cash_balance = 0.0
            # 将balances对象转换为可序列化的字典格式
            balances_data = []
            for balance in balances:
                balance_dict = {
                    'currency': balance.currency,
                    'total_cash': str(balance.total_cash),
                    'max_finance_amount': str(getattr(balance, 'max_finance_amount', '')),
                    'remaining_finance_amount': str(getattr(balance, 'remaining_finance_amount', '')),
                    'risk_level': getattr(balance, 'risk_level', ''),
                    'margin_call': str(getattr(balance, 'margin_call', '')),
                    'net_assets': str(getattr(balance, 'net_assets', '')),
                    'init_margin': str(getattr(balance, 'init_margin', '')),
                    'maintenance_margin': str(getattr(balance, 'maintenance_margin', '')),
                    'buy_power': str(getattr(balance, 'buy_power', ''))
                }

                # 添加cash_infos详细信息
                if hasattr(balance, 'cash_infos') and balance.cash_infos:
                    cash_infos = []
                    for cash_info in balance.cash_infos:
                        cash_infos.append({
                            'withdraw_cash': str(getattr(cash_info, 'withdraw_cash', '')),
                            'available_cash': str(getattr(cash_info, 'available_cash', '')),
                            'frozen_cash': str(getattr(cash_info, 'frozen_cash', '')),
                            'settling_cash': str(getattr(cash_info, 'settling_cash', '')),
                            'currency': getattr(cash_info, 'currency', '')
                        })
                    balance_dict['cash_infos'] = cash_infos

                balances_data.append(balance_dict)

                original_currency = balance.currency
                original_cash = float(balance.total_cash)
                # 折算到目标币种
                converted_cash = self.exchange_rate_service.convert_currency(original_cash, original_currency, currency)
                total_cash_balance += converted_cash
            
            # 计算持仓信息
            total_market_value = 0.0  # 持仓总市值（折算后）
            position_details = []  # 持仓明细
            
            if positions:
                # 收集所有股票代码，批量获取报价
                all_symbols = []
                for account in positions:
                    if hasattr(account, 'positions') and account.positions:
                        for stock in account.positions:
                            all_symbols.append(stock.symbol)
                
                # 批量获取报价数据
                quote_data = self.get_stock_quote_data(all_symbols) if all_symbols else {}

                # 获取股票基础信息以获取中文名称
                stock_info_dict = self.quote_api.get_stock_basic_info(all_symbols) if all_symbols else {}

                for account in positions:
                    if hasattr(account, 'positions') and account.positions:
                        for stock in account.positions:
                            symbol = stock.symbol
                            quantity = int(stock.quantity)
                            cost_price = float(stock.cost_price)
                            stock_currency = getattr(stock, 'currency', 'USD')

                            # 根据股票代码后缀判断市场和币种
                            if symbol.endswith('.US'):
                                stock_currency = 'USD'
                            elif symbol.endswith('.HK'):
                                stock_currency = 'HKD'

                            # 获取股票名称（优先使用中文名称）
                            stock_name = getattr(stock, 'symbol_name', symbol)
                            if symbol in stock_info_dict:
                                info = stock_info_dict[symbol]
                                # 优先显示中文名称，如果没有中文则使用英文
                                stock_name = str(info.name_cn) if hasattr(info, 'name_cn') and info.name_cn else stock_name

                            # 从批量获取的报价数据中提取价格信息
                            if symbol in quote_data:
                                current_price = quote_data[symbol]
                                original_market_value = current_price * quantity
                                pnl = (current_price - cost_price) * quantity

                                # 折算到目标币种
                                converted_market_value = self.exchange_rate_service.convert_currency(
                                    original_market_value, stock_currency, currency
                                )
                                converted_pnl = self.exchange_rate_service.convert_currency(
                                    pnl, stock_currency, currency
                                )

                                total_market_value += converted_market_value

                                position_details.append({
                                    'symbol': symbol,
                                    'name': stock_name,
                                    'quantity': quantity,
                                    'original_currency': stock_currency,
                                    'current_price': current_price,
                                    'cost_price': cost_price,
                                    'market_value': original_market_value,
                                    'converted_market_value': converted_market_value,
                                    'pnl': pnl,
                                    'converted_pnl': converted_pnl,
                                    'has_price_data': True
                                })
                            else:
                                # 没有价格数据，按0计算
                                position_details.append({
                                    'symbol': symbol,
                                    'name': stock_name,
                                    'quantity': quantity,
                                    'original_currency': stock_currency,
                                    'current_price': 0.0,
                                    'cost_price': cost_price,
                                    'market_value': 0.0,
                                    'converted_market_value': 0.0,
                                    'pnl': 0.0,
                                    'converted_pnl': 0.0,
                                    'has_price_data': False
                                })
            
            # 计算调整金额（折算到目标币种）
            total_adjustment = 0.0
            adjustment_details = []
            for adj_currency, adj_amount in adjustments.items():
                converted_adjustment = self.exchange_rate_service.convert_currency(adj_amount, adj_currency, currency)
                total_adjustment += converted_adjustment
                adjustment_details.append({
                    'currency': adj_currency,
                    'amount': adj_amount,
                    'converted_amount': converted_adjustment
                })

            # 计算总资产净值（所有持仓市值 + 所有币种现金 + 调整金额，均已折算）
            total_assets = total_market_value + total_cash_balance + total_adjustment
            
            # 计算杠杆率
            leverage_ratio = (total_market_value / total_assets) if total_assets > 0 else 0.0

            # 计算账户总盈亏（相对于初始资金）
            total_pnl = total_assets - self.initial_capital
            total_pnl_pct = (total_pnl / self.initial_capital) if self.initial_capital > 0 else 0.0

            return {
                'currency': currency,
                'total_assets': total_assets,
                'total_pnl': total_pnl,
                'total_pnl_pct': total_pnl_pct,
                'total_market_value': total_market_value,
                'total_cash_balance': total_cash_balance,
                'total_adjustment': total_adjustment,
                'adjustment_details': adjustment_details,
                'leverage_ratio': leverage_ratio,
                'balances': balances_data,
                'position_details': position_details,
                'exchange_rates': exchange_rates,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            logger.error(f"计算账户指标失败: {e}")
            return {}
    
    def query_account_metrics(self, currency: str = 'CNH', adjustments: Optional[Dict[str, float]] = None) -> None:
        """查询并显示账户指标

        Args:
            currency: 目标币种 (USD, HKD, CNH)，默认为 CNH
            adjustments: 资金调整字典，键为币种，值为调整金额（可正可负）
        """
        try:
            logger.info(f"开始计算账户指标，目标币种: {currency}")

            metrics = self.calculate_account_metrics(currency=currency, adjustments=adjustments)
            
            if not metrics:
                logger.warning("未能计算账户指标")
                return
            
            # 币种符号映射
            currency_symbol = {'USD': '$', 'HKD': 'HK$', 'CNH': '¥', 'CNY': '¥'}.get(currency, '')
            
            # 格式化输出内容
            output_lines = []
            output_lines.append("=" * 80)
            output_lines.append("账户指标信息")
            output_lines.append("=" * 80)
            output_lines.append(f"查询时间: {metrics['timestamp']}")
            output_lines.append(f"展示币种: {currency}")
            output_lines.append(f"初始资金: {currency_symbol}{self.initial_capital:,.2f}")
            output_lines.append("")
            
            # 汇率信息
            output_lines.append("【汇率信息】")
            output_lines.append("-" * 80)
            for curr, rate in metrics.get('exchange_rates', {}).items():
                if curr != currency:
                    output_lines.append(f"  1 {curr} = {rate:.4f} {currency}")
            output_lines.append("")
            
            output_lines.append("【账户概览】")
            output_lines.append("-" * 80)
            output_lines.append(f"  总资产净值:     {currency_symbol}{metrics['total_assets']:,.2f}")
            output_lines.append(f"  现金余额合计:   {currency_symbol}{metrics['total_cash_balance']:,.2f}")
            output_lines.append(f"  持仓总市值:     {currency_symbol}{metrics['total_market_value']:,.2f}")
            if metrics.get('adjustment_details'):
                output_lines.append(f"  资金调整合计:   {currency_symbol}{metrics['total_adjustment']:,.2f}")
            output_lines.append(f"  杠杆率:         {metrics['leverage_ratio']:.2%}")
            pnl_sign = "+" if metrics['total_pnl'] >= 0 else ""
            output_lines.append(f"  账户盈亏:       {pnl_sign}{currency_symbol}{metrics['total_pnl']:,.2f} ({metrics['total_pnl_pct']:.2%})")
            output_lines.append("")

            # 显示资金调整明细
            if metrics.get('adjustment_details'):
                output_lines.append("【资金调整明细】")
                output_lines.append("-" * 80)
                for adj in metrics['adjustment_details']:
                    adj_currency = adj['currency']
                    adj_amount = adj['amount']
                    converted_amount = adj['converted_amount']
                    adj_symbol = {'USD': '$', 'HKD': 'HK$', 'CNH': '¥', 'CNY': '¥'}.get(adj_currency, '')
                    adj_sign = "+" if adj_amount >= 0 else ""
                    output_lines.append(f"  {adj_currency}: {adj_sign}{adj_symbol}{adj_amount:,.2f} ({currency_symbol}{converted_amount:,.2f})")
                output_lines.append("")

            if metrics['position_details']:
                output_lines.append("【持仓明细】")
                output_lines.append("-" * 80)
                for pos in metrics['position_details']:
                    orig_currency = pos.get('original_currency', 'USD')
                    orig_symbol = {'USD': '$', 'HKD': 'HK$', 'CNH': '¥', 'CNY': '¥'}.get(orig_currency, '')
                    
                    output_lines.append(f"  {pos['symbol']} ({pos['name']})")
                    output_lines.append(f"    持仓数量:     {pos['quantity']:,} 股")
                    output_lines.append(f"    原始币种:     {orig_currency}")
                    output_lines.append(f"    成本价:       {orig_symbol}{pos['cost_price']:,.2f}")
                    if pos['has_price_data']:
                        output_lines.append(f"    现价:         {orig_symbol}{pos['current_price']:,.2f}")
                    else:
                        output_lines.append(f"    现价:         无数据")
                    output_lines.append(f"    市值:         {orig_symbol}{pos['market_value']:,.2f} ({currency_symbol}{pos['converted_market_value']:,.2f})")
                    pnl_sign = "+" if pos['pnl'] >= 0 else ""
                    output_lines.append(f"    持仓盈亏:     {pnl_sign}{orig_symbol}{pos['pnl']:,.2f} ({pnl_sign}{currency_symbol}{pos['converted_pnl']:,.2f})")
                    output_lines.append("")
            else:
                output_lines.append("【持仓明细】")
                output_lines.append("-" * 80)
                output_lines.append("  暂无持仓")
                output_lines.append("")
            
            output_lines.append("=" * 80)
            
            output_content = "\n".join(output_lines)
            
            # 输出到控制台
            print(output_content)
            
            # 保存到文件
            filepath = self._get_output_filename('account_metrics')
            self._save_to_file(output_content, filepath)
            
            # 同时保存JSON格式
            json_filepath = self._get_output_filename('account_metrics', 'json')
            self._save_to_file(json.dumps(metrics, indent=2, ensure_ascii=False), json_filepath)
            
        except Exception as e:
            logger.error(f"查询账户指标失败: {e}")


def main():
    """主函数"""
    # 配置日志
    logger.remove()
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="INFO"
    )
    logger.add(
        "logs/longport_trade_cli_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        encoding="utf-8"
    )
    
    # 创建主解析器
    parser = argparse.ArgumentParser(
        description="LongPort 交易账户查询 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # 创建子命令解析器
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 子命令: account-metrics
    parser_metrics = subparsers.add_parser(
        "account-metrics",
        help="计算账户各项指标（资产、持仓、盈亏等）"
    )
    parser_metrics.add_argument(
        "--currency",
        choices=['USD', 'HKD', 'CNH'],
        default='CNH',
        help="目标币种，所有资产将折算为此币种 (可选: USD, HKD, CNH，默认: CNH)"
    )
    parser_metrics.add_argument(
        "--initial-capital",
        type=float,
        default=1800000.0,
        help="初始资金 (默认: 1800000.0)"
    )
    parser_metrics.add_argument(
        "--adjust",
        action="append",
        nargs=2,
        metavar=("CURRENCY", "AMOUNT"),
        help="资金调整，格式: 币种 金额。可多次使用。例如: --adjust USD 2000 --adjust HKD -1000"
    )

    # 解析参数
    args = parser.parse_args()

    # 如果没有提供命令，显示帮助信息
    if not args.command:
        parser.print_help()
        sys.exit(0)

    # 初始化CLI
    try:
        # 根据命令确定初始资金
        initial_capital = getattr(args, 'initial_capital', 1800000.0)
        cli = LongPortTradeCLI(initial_capital=initial_capital)

        # 执行对应的命令
        if args.command == "account-metrics":
            # 解析调整金额参数
            adjustments = {}
            if hasattr(args, 'adjust') and args.adjust:
                for currency, amount in args.adjust:
                    # 验证币种是否有效
                    if currency not in ['USD', 'HKD', 'CNH']:
                        logger.error(f"无效的币种: {currency}，支持的币种: USD, HKD, CNH")
                        sys.exit(1)
                    try:
                        adjustments[currency] = float(amount)
                    except ValueError:
                        logger.error(f"无效的金额: {amount}，请输入数字")
                        sys.exit(1)

            cli.query_account_metrics(currency=args.currency, adjustments=adjustments if adjustments else None)
    
    except KeyboardInterrupt:
        logger.info("用户中断操作")
        sys.exit(0)
    except Exception as e:
        logger.error(f"执行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
