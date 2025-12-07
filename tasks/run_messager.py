#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
from datetime import date, datetime, timedelta
from typing import Dict, List, Any
import pytz
from loguru import logger

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from awesometrader import LongPortTradeAPI
from awesometrader.notify import DingTalkMessager
from awesometrader.collector import LongPortQuotaAPI

class AccountReporter:
    """账户信息报告器"""
    
    def __init__(self):
        """初始化账户报告器"""
        self.trader = LongPortTradeAPI()

        self.webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=56b1816700f3fd34ca58e1db36bcb23c8bd048745622a121c44b4ec1f805a3b8"
        self.secret = "SECc148e9dc5e5bc7914d332f5e5687ee000302a46f61f4df4045aabbbe17ba2e0a"
        self.messager = DingTalkMessager(dingtalk_webhook=self.webhook_url, dingtalk_secret=self.secret)
        
        # 初始化数据收集器（用于获取交易时段和股票报价）
        self.collector = LongPortQuotaAPI()
        
        # 初始资金设定
        self.initial_capital = 100000.0  # 美元
        
        # 获取用户所在时区
        try:
            system_tz = datetime.now().astimezone().tzinfo
            if hasattr(system_tz, 'zone'):
                self.user_timezone = system_tz
            else:
                self.user_timezone = pytz.timezone('Asia/Shanghai')
        except Exception:
            self.user_timezone = pytz.timezone('Asia/Shanghai')
        
        logger.info("账户报告器初始化完成")
    
    def is_trading_day(self, market: str) -> bool:
        """
        判断今天是否为指定市场的交易日
        """
        try:
            today = date.today()
            
            # 获取今天的交易日信息
            trading_days_response = self.collector.get_trading_days(
                market=market,
                begin_date=today,
                end_date=today
            )
            
            today_str = today.strftime('%Y%m%d')
            is_trading = any(
                trading_day.strftime('%Y%m%d') == today_str 
                for trading_day in trading_days_response.trading_days
            )
            
            market_name = '美股' if market == 'US' else '港股'
            if is_trading:
                logger.info(f"今天是{market_name}交易日")
            else:
                logger.info(f"今天不是{market_name}交易日")
            
            return is_trading
            
        except Exception as e:
            logger.error(f"检查交易日失败: {e}")
            return True
    
    def get_stock_quote_data(self, symbols: List[str]) -> Dict[str, float]:
        """批量获取股票报价数据"""
        try:
            quotes_dict = self.collector.get_stock_quote(symbols)
            quote_data = {}
            for symbol, quote in quotes_dict.items():
                quote_data[symbol] = float(quote.last_done)
            return quote_data
        except Exception as e:
            logger.error(f"批量获取股票报价失败: {e}")
            return {}
    
    def get_position_markets(self) -> List[str]:
        """获取当前持仓涉及的市场"""
        try:
            positions = self.trader.get_stock_positions()
            markets = set()
            if positions:
                for account in positions:
                    if hasattr(account, 'positions') and account.positions:
                        for stock in account.positions:
                            symbol = stock.symbol
                            if symbol.endswith('.US'):
                                markets.add('US')
                            elif symbol.endswith('.HK'):
                                markets.add('HK')
            return list(markets)
        except Exception as e:
            logger.error(f"获取持仓市场失败: {e}")
            return []

    def calculate_account_metrics(self) -> Dict[str, Any]:
        """计算账户各项指标"""
        try:
            # 获取账户余额信息
            balances = self.trader.get_account_balance(currency='USD')
            # 获取持仓信息
            positions = self.trader.get_stock_positions()
            
            if not balances:
                logger.error("无法获取账户余额信息")
                return {}
            
            # 找到美元账户
            usd_balance = None
            for balance in balances:
                if balance.currency == 'USD':
                    usd_balance = balance
                    break
            
            if not usd_balance:
                logger.error("未找到美元账户")
                return {}
            
            # 基础账户信息
            total_assets = float(usd_balance.net_assets)  # 总资产
            cash_balance = float(usd_balance.total_cash)  # 现金余额
            
            # 计算持仓信息
            total_market_value = 0.0  # 持仓总市值
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
                
                for account in positions:
                    if hasattr(account, 'positions') and account.positions:
                        for stock in account.positions:
                            symbol = stock.symbol
                            quantity = int(stock.quantity)
                            cost_price = float(stock.cost_price)
                            
                            # 从批量获取的报价数据中提取价格信息
                            if symbol in quote_data:
                                current_price = quote_data[symbol]
                                market_value = current_price * quantity
                                position_pnl = (current_price - cost_price) * quantity
                                total_market_value += market_value
                                
                                position_details.append({
                                    'symbol': symbol,
                                    'name': getattr(stock, 'symbol_name', symbol),
                                    'quantity': quantity,
                                    'current_price': current_price,
                                    'cost_price': cost_price,
                                    'market_value': market_value,
                                    'position_pnl': position_pnl,
                                    'has_price_data': True
                                })
                            else:
                                position_details.append({
                                    'symbol': symbol,
                                    'name': getattr(stock, 'symbol_name', symbol),
                                    'quantity': quantity,
                                    'cost_price': cost_price,
                                    'has_price_data': False
                                })
            
            # 获取所有有持仓的市场
            position_markets = self.get_position_markets()
            
            # 计算杠杆率
            leverage_ratio = (total_market_value / total_assets) if total_assets > 0 else 0.0
            
            # 计算账户总盈亏（相对于初始资金）
            total_account_pnl = total_assets - self.initial_capital
            total_account_pnl_pct = (total_account_pnl / self.initial_capital) if self.initial_capital > 0 else 0.0
            
            return {
                'total_assets': total_assets,
                'total_account_pnl': total_account_pnl,
                'total_account_pnl_pct': total_account_pnl_pct,
                'total_market_value': total_market_value,
                'leverage_ratio': leverage_ratio,
                'position_details': position_details,
                'position_markets': position_markets,
                'cash_balance': cash_balance,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            logger.error(f"计算账户指标失败: {e}")
            return {}
    
    def format_account_message(self, metrics: Dict[str, Any], trigger_market: str = None) -> str:
        """格式化账户信息消息"""
        if not metrics:
            return "## ❌ 账户信息获取失败\n\n请检查系统状态。"
        
        # 根据触发市场确定标题
        if trigger_market:
            trigger_market_name = '美股' if trigger_market == 'US' else '港股'
            title = f"## 📊 账户报告（{trigger_market_name}收盘后）"
        else:
            title = "## 📊 每日账户报告"
        
        message = f"""{title}

### 💰 账户概览
- **总资产**: ${metrics['total_assets']:,.2f}
- **账户总盈亏**: ${metrics['total_account_pnl']:+,.2f} ({metrics['total_account_pnl_pct']:+.2%})
- **持仓总市值**: ${metrics['total_market_value']:,.2f}
- **杠杆率**: {metrics['leverage_ratio']:.2%}

### 📋 持仓分布
"""
        
        if metrics['position_details']:
            for position in metrics['position_details']:
                if position.get('has_price_data', False):
                    pnl_emoji = "📈" if position['position_pnl'] >= 0 else "📉"
                    message += f"""
**{position['symbol']}** ({position['name']})
- 数量: {position['quantity']:,} 股
- 成本: ${position['cost_price']:.2f}
- 现价: ${position['current_price']:.2f}
- 市值: ${position['market_value']:,.2f}
- 总盈亏: {pnl_emoji} ${position['position_pnl']:+,.2f}

---
"""
                else:
                    message += f"""
**{position['symbol']}** ({position['name']})
- 数量: {position['quantity']:,} 股
- 成本: ${position['cost_price']:.2f}
- ⚠️ 无法获取实时报价

---
"""
        else:
            message += "\n暂无持仓\n"
        
        message += f"""
### ⏰ 报告时间
{metrics['timestamp']}

> 数据来源: AwesomeTrader | 初始资金: ${self.initial_capital:,.0f}
"""
        return message

    def send_market_report(self, market: str) -> bool:
        """发送账户报告"""
        try:
            market_name = '美股' if market == 'US' else '港股'
            logger.info(f"开始生成账户报告（{market_name}）...")
            
            # 计算账户指标
            metrics = self.calculate_account_metrics()
            if not metrics:
                logger.error("无法获取账户数据，跳过发送")
                return False
            
            # 检查是否有该市场的持仓
            if metrics['position_details']:
                market_suffix = f'.{market}'
                has_market_positions = any(
                    pos['symbol'].endswith(market_suffix) 
                    for pos in metrics['position_details']
                )
                
                if not has_market_positions:
                    logger.info(f"{market_name}无持仓，跳过发送")
                    return False
            else:
                logger.info("当前无任何持仓，跳过发送")
                return False
            
            # 格式化消息
            message = self.format_account_message(metrics, trigger_market=market)
            
            # 发送消息
            success = self.messager.send_dingtalk_markdown(
                title=f"账户报告（{market_name}）",
                text=message
            )
            
            if success:
                logger.success(f"账户报告发送成功（{market_name}）")
            else:
                logger.error(f"账户报告发送失败（{market_name}）")
            
            return success
            
        except Exception as e:
            logger.error(f"发送账户报告失败: {e}")
            return False

    def test_report(self) -> bool:
        """测试报告功能"""
        try:
            logger.info("开始测试账户报告功能...")
            metrics = self.calculate_account_metrics()
            if not metrics:
                logger.error("无法获取账户数据")
                return False
            
            message = self.format_account_message(metrics)
            success = self.messager.send_dingtalk_markdown(
                title="账户报告测试",
                text=message + "\n\n⚠️ 这是一条测试消息"
            )
            
            if success:
                logger.success("账户报告测试成功")
            else:
                logger.error("账户报告测试失败")
            return success
        except Exception as e:
            logger.error(f"测试报告失败: {e}")
            return False

class MessagerCLI:
    def __init__(self):
        self.reporter = AccountReporter()

    def report(self, market: str):
        """执行报告发送任务"""
        # 1. 检查是否为交易日
        if not self.reporter.is_trading_day(market):
            market_name = "美股" if market == "US" else "港股"
            logger.info(f"今天不是{market_name}交易日，跳过发送")
            return

        # 2. 发送报告
        self.reporter.send_market_report(market)

    def test(self):
        """执行测试"""
        self.reporter.test_report()

def main():
    # 配置日志
    logger.remove()
    logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO")
    logger.add("logs/messager_cli_{time:YYYY-MM-DD}.log", rotation="1 day", retention="30 days")

    parser = argparse.ArgumentParser(description="AwesomeTrader 消息推送 CLI")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # Command: report
    parser_report = subparsers.add_parser("report", help="发送市场报告")
    parser_report.add_argument("--market", required=True, choices=['US', 'HK'], help="市场代码 (US, HK)")

    # Command: test
    subparsers.add_parser("test", help="发送测试报告")

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)

    cli = MessagerCLI()

    try:
        if args.command == "report":
            cli.report(market=args.market)
        elif args.command == "test":
            cli.test()
            
    except KeyboardInterrupt:
        logger.info("用户中断操作")
        sys.exit(0)
    except Exception as e:
        logger.error(f"执行出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
