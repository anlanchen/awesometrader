#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import csv
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from loguru import logger

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from awesometrader import LongPortTradeAPI
from awesometrader import LongPortQuotaAPI
from awesometrader.utils.option_pricer import parse_option_symbol, price_option, OptionInfo
from tasks.exchange_rate import ExchangeRateService

class LongPortTradeCLI:
    """交易账户查询CLI"""
    
    # CSV 字段定义
    CSV_FIELDS = [
        'date', 'total_assets', 'total_market_value', 'total_cash_balance',
        'total_adjustment', 'leverage_ratio'
    ]

    def __init__(self):
        """初始化交易CLI"""
        self.trader = LongPortTradeAPI()
        self.quote_api = LongPortQuotaAPI()
        self.exchange_rate_service = ExchangeRateService()
        
        # 创建输出目录
        self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'caches')
        self.output_dir = os.path.join(self.cache_dir, 'account')
        os.makedirs(self.output_dir, exist_ok=True)
        
        # CSV 文件路径
        self.csv_path = os.path.join(self.cache_dir, 'account.csv')
        
        logger.info("交易CLI初始化完成")

    def _get_output_filename(self, command: str, extension: str = 'txt') -> str:
        """生成输出文件名"""
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"{timestamp}.{extension}"
        return os.path.join(self.output_dir, filename)
    
    def _save_to_file(self, content: str, filepath: str) -> None:
        """保存内容到文件"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.success(f"结果已保存到: {filepath}")
        except Exception as e:
            logger.error(f"保存文件失败: {e}")
    
    def _extract_csv_row(self, data: dict, date_str: str) -> dict:
        """从账户指标数据中提取 CSV 行数据"""
        # 格式化日期为 YYYY-MM-DD
        formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        
        # 格式化数值：保留2位小数，百分比字段转换为%显示
        return {
            'date': formatted_date,
            'total_assets': f"{data.get('total_assets', 0):.2f}",
            'total_market_value': f"{data.get('total_market_value', 0):.2f}",
            'total_cash_balance': f"{data.get('total_cash_balance', 0):.2f}",
            'total_adjustment': f"{data.get('total_adjustment', 0):.2f}",
            'leverage_ratio': f"{data.get('leverage_ratio', 0) * 100:.2f}%",
        }
    
    def _update_csv(self, row_data: dict) -> bool:
        """更新 CSV 文件，如果日期已存在则更新，否则追加"""
        try:
            # 读取现有数据
            existing_rows = []
            if os.path.exists(self.csv_path):
                with open(self.csv_path, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.DictReader(f)
                    existing_rows = list(reader)
            
            # 查找是否已存在该日期的记录
            date_found = False
            for i, row in enumerate(existing_rows):
                if row['date'] == row_data['date']:
                    existing_rows[i] = row_data
                    date_found = True
                    logger.info(f"更新已存在的日期记录: {row_data['date']}")
                    break
            
            if not date_found:
                existing_rows.append(row_data)
                logger.info(f"添加新的日期记录: {row_data['date']}")
            
            # 按日期排序
            existing_rows.sort(key=lambda x: x['date'])
            
            # 写入 CSV 文件
            with open(self.csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.CSV_FIELDS)
                writer.writeheader()
                writer.writerows(existing_rows)
            
            logger.success(f"CSV 文件更新成功: {self.csv_path}")
            return True
            
        except Exception as e:
            logger.error(f"更新 CSV 文件失败: {e}")
            return False
    
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

    def get_option_quote_data(self, option_symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """批量获取期权报价数据
        
        Args:
            option_symbols: 期权代码列表
            
        Returns:
            期权报价字典，键为期权代码，值为包含价格和Greeks的字典
        """
        option_data = {}
        
        if not option_symbols:
            return option_data
        
        try:
            # 尝试通过LongPort API获取期权行情
            option_quotes = self.quote_api.get_option_quote(option_symbols)
            
            for symbol, quote in option_quotes.items():
                last_price = float(quote.last_done) if hasattr(quote, 'last_done') else 0.0
                option_data[symbol] = {
                    'price': last_price,
                    'source': 'api',
                    'implied_volatility': float(getattr(quote, 'implied_volatility', 0)) if hasattr(quote, 'implied_volatility') else None,
                    'delta': float(getattr(quote, 'delta', 0)) if hasattr(quote, 'delta') else None,
                    'gamma': float(getattr(quote, 'gamma', 0)) if hasattr(quote, 'gamma') else None,
                    'theta': float(getattr(quote, 'theta', 0)) if hasattr(quote, 'theta') else None,
                    'vega': float(getattr(quote, 'vega', 0)) if hasattr(quote, 'vega') else None,
                }
                logger.info(f"从API获取期权 {symbol} 报价: ${last_price:.2f}")
                
        except Exception as e:
            logger.warning(f"从API获取期权报价失败: {e}，将使用Black-Scholes模型计算")
        
        return option_data

    def calculate_option_theoretical_price(
        self, 
        option_info: OptionInfo, 
        underlying_price: float,
        volatility: Optional[float] = None
    ) -> Dict[str, Any]:
        """使用Black-Scholes模型计算期权理论价格
        
        Args:
            option_info: 期权信息
            underlying_price: 标的资产现价
            volatility: 波动率，如果为None则使用默认值
            
        Returns:
            包含理论价格和Greeks的字典
        """
        try:
            pricing = price_option(
                option_info=option_info,
                underlying_price=underlying_price,
                risk_free_rate=0.036,  # 使用当前美国国债利率约4.5%
                volatility=volatility
            )
            
            return {
                'price': pricing['theoretical_price'],
                'source': 'black_scholes',
                'implied_volatility': pricing['volatility_used'],
                'delta': pricing['delta'],
                'gamma': pricing['gamma'],
                'theta': pricing['theta'],
                'vega': pricing['vega'],
                'intrinsic_value': pricing['intrinsic_value'],
                'time_value': pricing['time_value'],
                'time_to_expiry_days': pricing['time_to_expiry_days'],
            }
        except Exception as e:
            logger.error(f"计算期权 {option_info.full_symbol} 理论价格失败: {e}")
            return {'price': 0.0, 'source': 'error'}

    def calculate_account_metrics(self, currency: str = 'CNH', adjustments: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """计算账户各项指标

        总资产净值 = 长桥返回的 net_assets + 调整金额，并根据当前选择币种折算展示

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

            # 获取汇率（以 CNH 为基准）
            exchange_rates = self.exchange_rate_service.get_exchange_rates()

            # 计算所有币种现金余额和净资产（折算到目标币种）
            total_cash_balance = 0.0
            total_net_assets = 0.0  # 长桥返回的净资产（不含调整）
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
                
                # 获取长桥返回的净资产并折算
                net_assets_value = float(getattr(balance, 'net_assets', 0) or 0)
                converted_net_assets = self.exchange_rate_service.convert_currency(net_assets_value, original_currency, currency)
                total_net_assets += converted_net_assets
            
            # 计算持仓信息
            total_market_value = 0.0  # 持仓总市值（折算后）
            position_details = []  # 持仓明细
            
            if positions:
                # 分离股票和期权代码
                stock_symbols = []
                option_symbols = []
                option_info_map = {}  # 期权代码 -> 期权信息
                
                for account in positions:
                    if hasattr(account, 'positions') and account.positions:
                        for stock in account.positions:
                            symbol = stock.symbol
                            option_info = parse_option_symbol(symbol)
                            if option_info:
                                option_symbols.append(symbol)
                                option_info_map[symbol] = option_info
                            else:
                                stock_symbols.append(symbol)
                
                # 批量获取股票报价数据
                quote_data = self.get_stock_quote_data(stock_symbols) if stock_symbols else {}
                
                # 批量获取期权报价数据（尝试API获取）
                option_quote_data = self.get_option_quote_data(option_symbols) if option_symbols else {}

                # 获取股票基础信息以获取中文名称
                all_symbols = stock_symbols + option_symbols
                stock_info_dict = self.quote_api.get_stock_basic_info(all_symbols) if all_symbols else {}
                
                # 为期权获取标的股票价格（用于Black-Scholes计算）
                underlying_symbols = list(set(
                    f"{info.underlying}.{info.market}" 
                    for info in option_info_map.values()
                ))
                underlying_prices = self.get_stock_quote_data(underlying_symbols) if underlying_symbols else {}

                for account in positions:
                    if hasattr(account, 'positions') and account.positions:
                        for stock in account.positions:
                            symbol = stock.symbol
                            quantity = int(stock.quantity)
                            cost_price = float(stock.cost_price)
                            stock_currency = getattr(stock, 'currency', 'USD')

                            # 根据代码后缀判断市场和币种
                            if symbol.endswith('.US'):
                                stock_currency = 'USD'
                            elif symbol.endswith('.HK'):
                                stock_currency = 'HKD'

                            # 获取名称（优先使用中文名称）
                            stock_name = getattr(stock, 'symbol_name', symbol)
                            if symbol in stock_info_dict:
                                info = stock_info_dict[symbol]
                                stock_name = str(info.name_cn) if hasattr(info, 'name_cn') and info.name_cn else stock_name

                            # 检查是否为期权
                            option_info = option_info_map.get(symbol)
                            
                            if option_info:
                                # 处理期权持仓
                                current_price = 0.0
                                option_details = {}
                                price_source = 'none'
                                
                                # 优先使用API获取的期权报价
                                if symbol in option_quote_data and option_quote_data[symbol].get('price', 0) > 0:
                                    api_data = option_quote_data[symbol]
                                    current_price = api_data['price']
                                    price_source = 'api'
                                    option_details = {
                                        'implied_volatility': api_data.get('implied_volatility'),
                                        'delta': api_data.get('delta'),
                                        'gamma': api_data.get('gamma'),
                                        'theta': api_data.get('theta'),
                                        'vega': api_data.get('vega'),
                                    }
                                else:
                                    # 使用Black-Scholes模型计算
                                    underlying_symbol = f"{option_info.underlying}.{option_info.market}"
                                    underlying_price = underlying_prices.get(underlying_symbol, 0)
                                    
                                    if underlying_price > 0:
                                        bs_result = self.calculate_option_theoretical_price(
                                            option_info, underlying_price, 0.75
                                        )
                                        current_price = bs_result['price']
                                        price_source = 'black_scholes'
                                        option_details = {
                                            'implied_volatility': bs_result.get('implied_volatility'),
                                            'delta': bs_result.get('delta'),
                                            'gamma': bs_result.get('gamma'),
                                            'theta': bs_result.get('theta'),
                                            'vega': bs_result.get('vega'),
                                            'intrinsic_value': bs_result.get('intrinsic_value'),
                                            'time_value': bs_result.get('time_value'),
                                            'time_to_expiry_days': bs_result.get('time_to_expiry_days'),
                                            'underlying_price': underlying_price,
                                        }
                                        logger.info(
                                            f"期权 {symbol} 使用Black-Scholes计算: "
                                            f"标的价格=${underlying_price:.2f}, 行权价=${option_info.strike_price:.2f}, "
                                            f"理论价格=${current_price:.4f}"
                                        )
                                
                                # 期权合约乘数（美股期权通常是100股/张）
                                contract_multiplier = 100
                                # 注意: quantity可能为负（空头），市值计算需要取绝对值
                                original_market_value = current_price * abs(quantity) * contract_multiplier
                                # 对于空头期权，市值应该是负值（表示负债）
                                if quantity < 0:
                                    original_market_value = -original_market_value
                                
                                # 计算盈亏
                                # 对于卖出期权（quantity < 0），成本是收到的权利金
                                # pnl = 收到的权利金 - 当前期权价值
                                cost_total = cost_price * abs(quantity) * contract_multiplier
                                if quantity < 0:
                                    # 空头：收到权利金是正的，当前价值是负债
                                    pnl = cost_total - current_price * abs(quantity) * contract_multiplier
                                else:
                                    # 多头：买入期权
                                    pnl = (current_price - cost_price) * quantity * contract_multiplier

                                # 折算到目标币种
                                converted_market_value = self.exchange_rate_service.convert_currency(
                                    original_market_value, stock_currency, currency
                                )
                                converted_pnl = self.exchange_rate_service.convert_currency(
                                    pnl, stock_currency, currency
                                )

                                total_market_value += converted_market_value

                                position_detail = {
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
                                    'has_price_data': current_price > 0,
                                    'is_option': True,
                                    'option_type': 'Call' if option_info.option_type == 'C' else 'Put',
                                    'strike_price': option_info.strike_price,
                                    'expiry_date': option_info.expiry_date.isoformat(),
                                    'underlying': option_info.underlying,
                                    'price_source': price_source,
                                    'contract_multiplier': contract_multiplier,
                                }
                                position_detail.update(option_details)
                                position_details.append(position_detail)
                            else:
                                # 处理股票持仓
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
                                        'has_price_data': True,
                                        'is_option': False
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
                                        'has_price_data': False,
                                        'is_option': False
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

            # 计算总资产净值（长桥返回的 net_assets + 调整金额）
            total_assets = total_net_assets + total_adjustment
            logger.info(f"总资产计算: 长桥净资产 {total_net_assets:,.2f} + 调整 {total_adjustment:,.2f} = {total_assets:,.2f} {currency}")
            
            # 计算杠杆率
            leverage_ratio = (total_market_value / total_assets) if total_assets > 0 else 0.0

            return {
                'currency': currency,
                'total_assets': total_assets,
                'total_net_assets': total_net_assets,
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
            output_lines.append("")
            
            # 汇率信息（以 CNH 为基准）
            output_lines.append("【汇率信息】")
            output_lines.append("-" * 80)
            for curr, rate in metrics.get('exchange_rates', {}).items():
                if curr != 'CNH':
                    output_lines.append(f"  1 {curr} = {rate:.4f} CNH")
            output_lines.append("")
            
            output_lines.append("【账户概览】")
            output_lines.append("-" * 80)
            output_lines.append(f"  总资产净值:     {currency_symbol}{metrics['total_assets']:,.2f}")
            output_lines.append(f"  ├ 长桥净资产:   {currency_symbol}{metrics['total_net_assets']:,.2f}")
            if metrics.get('adjustment_details'):
                output_lines.append(f"  └ 资金调整:     {currency_symbol}{metrics['total_adjustment']:,.2f}")
            output_lines.append(f"  现金余额合计:   {currency_symbol}{metrics['total_cash_balance']:,.2f}")
            output_lines.append(f"  持仓总市值:     {currency_symbol}{metrics['total_market_value']:,.2f}")
            output_lines.append(f"  杠杆率:         {metrics['leverage_ratio']:.2%}")
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
                # 分别显示股票和期权持仓
                stock_positions = [p for p in metrics['position_details'] if not p.get('is_option', False)]
                option_positions = [p for p in metrics['position_details'] if p.get('is_option', False)]
                
                if stock_positions:
                    output_lines.append("【股票持仓明细】")
                    output_lines.append("-" * 80)
                    for pos in stock_positions:
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
                
                if option_positions:
                    output_lines.append("【期权持仓明细】")
                    output_lines.append("-" * 80)
                    for pos in option_positions:
                        orig_currency = pos.get('original_currency', 'USD')
                        orig_symbol = {'USD': '$', 'HKD': 'HK$', 'CNH': '¥', 'CNY': '¥'}.get(orig_currency, '')
                        
                        # 显示期权基本信息
                        position_type = "空头" if pos['quantity'] < 0 else "多头"
                        option_type = pos.get('option_type', 'Unknown')
                        output_lines.append(f"  {pos['symbol']} ({pos['name']})")
                        output_lines.append(f"    期权类型:     {option_type} ({position_type})")
                        output_lines.append(f"    标的:         {pos.get('underlying', 'N/A')}")
                        output_lines.append(f"    行权价:       {orig_symbol}{pos.get('strike_price', 0):,.2f}")
                        output_lines.append(f"    到期日:       {pos.get('expiry_date', 'N/A')}")
                        output_lines.append(f"    持仓数量:     {pos['quantity']:,} 张 (x{pos.get('contract_multiplier', 100)})")
                        output_lines.append(f"    成本价:       {orig_symbol}{pos['cost_price']:,.4f}/股")
                        
                        # 显示价格和来源
                        price_source = pos.get('price_source', 'none')
                        source_label = {
                            'api': '(API)',
                            'black_scholes': '(BS模型)',
                            'none': '(无数据)'
                        }.get(price_source, '')
                        
                        if pos['has_price_data']:
                            output_lines.append(f"    现价:         {orig_symbol}{pos['current_price']:,.4f}/股 {source_label}")
                        else:
                            output_lines.append(f"    现价:         无数据 {source_label}")
                        
                        # 显示市值（注意期权空头市值为负）
                        output_lines.append(f"    市值:         {orig_symbol}{pos['market_value']:,.2f} ({currency_symbol}{pos['converted_market_value']:,.2f})")
                        
                        pnl_sign = "+" if pos['pnl'] >= 0 else ""
                        output_lines.append(f"    持仓盈亏:     {pnl_sign}{orig_symbol}{pos['pnl']:,.2f} ({pnl_sign}{currency_symbol}{pos['converted_pnl']:,.2f})")
                        
                        # 显示Greeks信息（如果有）
                        if pos.get('delta') is not None:
                            output_lines.append(f"    Delta:        {pos['delta']:.4f}")
                        if pos.get('gamma') is not None:
                            output_lines.append(f"    Gamma:        {pos['gamma']:.6f}")
                        if pos.get('theta') is not None:
                            output_lines.append(f"    Theta:        {pos['theta']:.4f}/天")
                        if pos.get('time_to_expiry_days') is not None:
                            output_lines.append(f"    剩余天数:     {pos['time_to_expiry_days']}天")
                        if pos.get('intrinsic_value') is not None:
                            output_lines.append(f"    内在价值:     {orig_symbol}{pos['intrinsic_value']:,.4f}")
                        if pos.get('time_value') is not None:
                            output_lines.append(f"    时间价值:     {orig_symbol}{pos['time_value']:,.4f}")
                        if pos.get('underlying_price') is not None:
                            output_lines.append(f"    标的现价:     {orig_symbol}{pos['underlying_price']:,.2f}")
                        
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
            
            # 保存JSON格式
            json_filepath = self._get_output_filename('account', 'json')
            self._save_to_file(json.dumps(metrics, indent=2, ensure_ascii=False), json_filepath)
            
            # 同步更新 CSV 文件
            # 由于脚本在早上8点执行，获取的是前一天的收盘数据，所以记录前一天的日期
            yesterday = datetime.now() - timedelta(days=1)
            date_str = yesterday.strftime('%Y%m%d')
            row_data = self._extract_csv_row(metrics, date_str)
            self._update_csv(row_data)
            
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
        retention="7 days",
        encoding="utf-8"
    )
    
    # 创建主解析器
    epilog_text = """
示例用法:
  # 查询账户指标（默认使用CNH币种）
  python tasks/longport_trade_cli.py account

  # 使用USD币种展示
  python tasks/longport_trade_cli.py account --currency USD

  # 添加资金调整
  python tasks/longport_trade_cli.py account --adjust USD 2000 --adjust HKD -1000

使用 "python tasks/longport_trade_cli.py <command> -h" 查看具体命令的详细帮助
"""
    parser = argparse.ArgumentParser(
        description="LongPort 交易账户查询 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog_text
    )
    
    # 创建子命令解析器
    subparsers = parser.add_subparsers(dest="command", help="可用命令", metavar="<command>")
    
    # 子命令: account
    parser_metrics = subparsers.add_parser(
        "account",
        help="计算账户各项指标（资产、持仓、盈亏等）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="计算账户各项指标（资产、持仓、盈亏等），包括总资产、现金余额、持仓市值、杠杆率等"
    )
    parser_metrics.add_argument(
        "--currency",
        choices=['USD', 'HKD', 'CNH'],
        default='CNH',
        help="目标币种，所有资产将折算为此币种 (可选: USD, HKD, CNH，默认: CNH)"
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
        cli = LongPortTradeCLI()

        # 执行对应的命令
        if args.command == "account":
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
