#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import schedule
from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
import pytz
from loguru import logger

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from awesometrader import LongPortTraderAPI
from awesometrader.notify import DingTalkMessager
from awesometrader.collector import LongPortAPI



class AccountReporter:
    """账户信息报告器"""
    
    def __init__(self):
        """初始化账户报告器"""
        self.trader = LongPortTraderAPI()

        self.webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=56b1816700f3fd34ca58e1db36bcb23c8bd048745622a121c44b4ec1f805a3b8"
        self.secret = "SECc148e9dc5e5bc7914d332f5e5687ee000302a46f61f4df4045aabbbe17ba2e0a"
        self.messager = DingTalkMessager(dingtalk_webhook=self.webhook_url, dingtalk_secret=self.secret)
        
        # 初始化数据收集器（用于获取交易时段和股票报价）
        self.collector = LongPortAPI()
        
        # 初始资金设定
        self.initial_capital = 100000.0  # 美元
        
        # 延迟发送时间（收盘后多少分钟发送）
        self.send_delay_minutes = 30

        # 获取用户所在时区
        try:
            system_tz = datetime.now().astimezone().tzinfo
            if hasattr(system_tz, 'zone'):
                self.user_timezone = system_tz
            else:
                self.user_timezone = pytz.timezone('Asia/Shanghai')
        except Exception:
            self.user_timezone = pytz.timezone('Asia/Shanghai')
        
        # 市场时区映射
        self.market_timezones = {
            'US': pytz.timezone('America/New_York'),  # 美东时间
            'HK': pytz.timezone('Asia/Hong_Kong'),    # 港股时间
        }
        
        logger.info("账户报告器初始化完成")
    
    def is_trading_day(self, market: str) -> bool:
        """
        判断今天是否为指定市场的交易日
        
        Args:
            market: 市场代码 ('US' 或 'HK')
            
        Returns:
            bool: 是否为交易日
        """
        try:
            today = date.today()
            
            # 获取今天的交易日信息（查询今天到今天的范围）
            trading_days_response = self.collector.get_trading_days(
                market=market,
                begin_date=today,
                end_date=today
            )
            
            # 检查今天是否在交易日列表中
            today_str = today.strftime('%Y%m%d')
            is_trading = any(
                trading_day.strftime('%Y%m%d') == today_str 
                for trading_day in trading_days_response.trading_days
            )
            
            market_name = '美股' if market == 'US' else '港股'
            if is_trading:
                logger.info(f"今天是{market_name}交易日")
            else:
                logger.info(f"今天不是{market_name}交易日，跳过推送")
            
            return is_trading
            
        except Exception as e:
            logger.error(f"检查交易日失败: {e}")
            # 出错时默认认为是交易日，避免漏发
            return True
    
    def get_trading_sessions(self) -> Dict[str, Any]:
        """
        从API获取实时交易时段信息
        
        Returns:
            Dict[str, Any]: 交易时段信息 {market: {close_time: datetime.time}}
        """
        try:
            sessions = self.collector.get_trading_session()
            market_sessions = {}
            
            for market_session in sessions:
                market_name = str(market_session.market).split('.')[-1]  # 获取枚举名称
                trade_sessions = market_session.trade_sessions
                
                if trade_sessions:
                    # 查找 Intraday 交易时段的收盘时间
                    for session in trade_sessions:
                        session_type = str(session.trade_session).split('.')[-1]
                        if session_type == 'Intraday':
                            market_sessions[market_name] = {
                                'close_time': session.end_time
                            }
                            break
            
            logger.info(f"获取到交易时段信息: {market_sessions}")
            return market_sessions
            
        except Exception as e:
            logger.error(f"获取交易时段失败: {e}")
            # 返回默认时间
            return {
                'US': {'close_time': datetime.strptime('16:00', '%H:%M').time()},
                'HK': {'close_time': datetime.strptime('16:00', '%H:%M').time()}
            }
    
    def convert_market_time_to_user_time(self, market_time: datetime.time, market: str) -> datetime:
        """
        将市场时间转换为用户本地时间
        
        Args:
            market_time: 市场时间 (datetime.time 对象)
            market: 市场代码
            
        Returns:
            datetime: 用户本地时间的datetime对象
        """
        try:
            # 获取市场时区
            market_tz = self.market_timezones.get(market, pytz.UTC)
            
            # 创建今天的市场时间
            today = datetime.now(market_tz).date()
            market_datetime = market_tz.localize(
                datetime.combine(today, market_time)
            )
            
            # 转换为用户本地时间
            user_datetime = market_datetime.astimezone(self.user_timezone)
            
            return user_datetime
            
        except Exception as e:
            logger.error(f"时间转换失败: {e}")
            return datetime.now(self.user_timezone)
    
    def get_stock_quote_data(self, symbols: List[str]) -> Dict[str, float]:
        """
        批量获取股票报价数据
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            Dict[str, float]: 股票报价数据 {symbol: current_price}
        """
        try:
            # 使用 LongPortAPI 获取实时报价
            quotes_dict = self.collector.get_stock_quote(symbols)
            quote_data = {}
            
            for symbol, quote in quotes_dict.items():
                quote_data[symbol] = float(quote.last_done)
            
            logger.info(f"成功获取 {len(quote_data)} 只股票的报价数据")
            return quote_data
            
        except Exception as e:
            logger.error(f"批量获取股票报价失败: {e}")
            return {}
    
    def calculate_account_metrics(self) -> Dict[str, Any]:
        """
        计算账户各项指标
        
        Returns:
            Dict[str, Any]: 账户指标数据
        """
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
                                
                                # 计算市值和盈亏
                                market_value = current_price * quantity
                                position_pnl = (current_price - cost_price) * quantity
                                
                                total_market_value += market_value
                                
                                # 添加到持仓明细（有价格数据）
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
                                logger.warning(f"无法获取 {symbol} 报价数据，显示持仓但不计算价格相关信息")
                                
                                # 添加到持仓明细（无价格数据）
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
            
            # 计算账户总盈亏百分比
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
        """
        格式化账户信息消息
        
        Args:
            metrics: 账户指标数据
            trigger_market: 触发推送的市场代码，用于显示触发信息
            
        Returns:
            str: 格式化的Markdown消息
        """
        if not metrics:
            return "## ❌ 账户信息获取失败\n\n请检查系统状态。"
        
        # 根据触发市场确定标题
        if trigger_market:
            trigger_market_name = '美股' if trigger_market == 'US' else '港股'
            title = f"## 📊 账户报告（{trigger_market_name}收盘后）"
        else:
            title = "## 📊 每日账户报告"
        
        # 构建Markdown消息
        message = f"""{title}

### 💰 账户概览
- **总资产**: ${metrics['total_assets']:,.2f}
- **账户总盈亏**: ${metrics['total_account_pnl']:+,.2f} ({metrics['total_account_pnl_pct']:+.2%})
- **持仓总市值**: ${metrics['total_market_value']:,.2f}
- **杠杆率**: {metrics['leverage_ratio']:.2%}

### 📋 持仓分布
"""
        
        # 添加持仓明细
        if metrics['position_details']:
            for position in metrics['position_details']:
                if position.get('has_price_data', False):
                    # 有价格数据的持仓，显示完整信息
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
                    # 无价格数据的持仓，只显示基本信息
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
    
    def get_position_markets(self) -> List[str]:
        """
        获取当前持仓涉及的市场
        
        Returns:
            List[str]: 市场列表，如 ['US', 'HK']
        """
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


    def send_market_report(self, market: str) -> bool:
        """
        发送账户报告（按市场交易时间触发）
        
        Args:
            market: 触发推送的市场代码 ('US' 或 'HK')，用于确定推送时间和标题
            
        Returns:
            bool: 发送是否成功
        """
        try:
            market_name = '美股' if market == 'US' else '港股'
            logger.info(f"开始生成账户报告（{market_name}收盘后触发）...")
            
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
                title=f"账户报告（{market_name}收盘后）",
                text=message
            )
            
            if success:
                logger.success(f"账户报告发送成功（{market_name}收盘后触发）")
            else:
                logger.error(f"账户报告发送失败（{market_name}收盘后触发）")
            
            return success
            
        except Exception as e:
            logger.error(f"发送账户报告失败（{market}市场触发）: {e}")
            return False
    

    
    def test_report(self) -> bool:
        """
        测试报告功能（不检查时间限制）
        
        Returns:
            bool: 测试是否成功
        """
        try:
            logger.info("开始测试账户报告功能...")
            
            # 计算账户指标
            metrics = self.calculate_account_metrics()
            if not metrics:
                logger.error("无法获取账户数据")
                return False
            
            # 格式化消息
            message = self.format_account_message(metrics)
            logger.info("账户报告消息格式化完成")
            
            # 发送测试消息
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


class MessagerMain:
    """消息推送主程序"""
    
    def __init__(self):
        """初始化主程序"""
        self.reporter = AccountReporter()
        logger.info("消息推送主程序初始化完成")
    
    def setup_daily_report_scheduler(self):
        """设置每日报告调度器"""
        # 每天早上00:01获取交易时段信息并设置当日的推送任务
        schedule.every().day.at("00:01").do(self.daily_setup_market_reports)
        logger.info("已设置每日00:01获取交易时段并安排账户报告任务")
    
    def daily_setup_market_reports(self):
        """每日设置账户报告任务（按各市场收盘时间推送）"""
        logger.info("=" * 50)
        logger.info("开始设置今日账户报告任务")
        logger.info("=" * 50)
        
        # 清除今天的旧任务（除了每日00:01的任务）
        schedule.clear('market_report')
        
        try:
            # 获取当前持仓涉及的市场
            position_markets = self.reporter.get_position_markets()
            if not position_markets:
                logger.warning("当前无持仓，不设置报告任务")
                return
            
            logger.info(f"当前持仓涉及市场: {position_markets}")
            
            # 为每个有持仓的市场检查交易日并设置账户报告任务
            tasks_scheduled = 0
            for market in position_markets:
                market_name = "美股" if market == "US" else "港股"
                
                # 1. 检查是否为交易日
                if not self.reporter.is_trading_day(market):
                    logger.info(f"今天不是{market_name}交易日，跳过设置 {market_name} 市场的报告任务")
                    continue
                
                # 2. 是交易日才获取交易时间
                try:
                    trading_sessions = self.reporter.get_trading_sessions()
                    if market in trading_sessions:
                        market_info = trading_sessions[market]
                        close_time = market_info['close_time']
                        
                        # 3. 设置定时任务
                        self._schedule_market_report(market, close_time)
                        tasks_scheduled += 1
                    else:
                        logger.warning(f"{market_name} 市场未找到交易时段信息，跳过设置任务")
                        
                except Exception as e:
                    logger.error(f"获取 {market_name} 市场交易时段信息失败: {e}")
                    continue
            
            if tasks_scheduled > 0:
                logger.success(f"今日账户报告任务设置完成，共设置 {tasks_scheduled} 个推送任务")
            else:
                logger.info("今日无交易日或无持仓，未设置推送任务")
            
        except Exception as e:
            logger.error(f"设置账户报告任务失败: {e}")
    
    def _schedule_market_report(self, market: str, close_time: datetime.time):
        """安排单个市场收盘后的账户报告任务"""
        try:
            # 将市场收盘时间转换为用户本地时间
            market_close_time = self.reporter.convert_market_time_to_user_time(close_time, market)
            
            # 添加延迟时间
            report_time = market_close_time + timedelta(minutes=self.reporter.send_delay_minutes)
            report_time_str = report_time.strftime('%H:%M')
            
            # 安排报告任务
            schedule.every().day.at(report_time_str).do(
                self.scheduled_market_report, market=market
            ).tag('market_report')
            
            # 格式化显示时间
            display_time = f"{close_time.hour:02d}:{close_time.minute:02d}"
            market_name = "美股" if market == "US" else "港股"
            
            logger.info(f"已安排 {market_name} 收盘后账户报告任务:")
            logger.info(f"  市场收盘时间: {display_time} ({self.reporter.market_timezones.get(market, 'UTC')})")
            logger.info(f"  用户本地推送时间: {report_time_str} ({self.reporter.user_timezone})")
            
        except Exception as e:
            logger.error(f"安排 {market} 市场收盘后账户报告任务失败: {e}")
    
    def scheduled_market_report(self, market: str):
        """执行定时账户报告任务（按市场收盘时间触发）"""
        market_name = "美股" if market == "US" else "港股"
        logger.info(f"执行定时账户报告任务（{market_name}收盘后触发）")
        try:
            # 发送账户报告
            success = self.reporter.send_market_report(market)
            if success:
                logger.success(f"定时账户报告任务完成（{market_name}收盘后触发）")
            else:
                logger.error(f"定时账户报告任务失败（{market_name}收盘后触发）")
        except Exception as e:
            logger.error(f"定时账户报告任务异常（{market_name}收盘后触发）: {e}")
    
    def run_scheduler(self):
        """运行定时调度器"""
        logger.info("启动定时调度器...")
        
        # 设置每日报告调度器
        self.setup_daily_report_scheduler()
        
        # 立即执行一次今日任务设置
        self.daily_setup_market_reports()
        
        logger.info("定时任务已设置，等待执行...")
        logger.info("按 Ctrl+C 退出")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
            except KeyboardInterrupt:
                logger.info("接收到中断信号，退出程序")
                break
            except Exception as e:
                logger.error(f"调度器运行异常: {e}")
                time.sleep(60)  # 异常时等待1分钟后继续
    
    def run_test(self):
        """运行测试模式"""
        logger.info("运行测试模式...")
        
        # 获取当前持仓涉及的市场
        position_markets = self.reporter.get_position_markets()
        
        if not position_markets:
            logger.warning("当前无持仓，发送通用测试报告")
            success = self.reporter.test_report()
        else:
            logger.info(f"检测到持仓市场: {position_markets}")
            success = True
            
            # 为每个有持仓的市场发送账户测试报告
            for market in position_markets:
                market_name = "美股" if market == "US" else "港股"
                logger.info(f"发送账户测试报告（{market_name}收盘后触发）...")
                
                market_success = self.reporter.send_market_report(market)
                if market_success:
                    logger.success(f"账户测试报告发送成功（{market_name}收盘后触发）")
                else:
                    logger.error(f"账户测试报告发送失败（{market_name}收盘后触发）")
                    success = False
        
        if success:
            logger.success("测试完成：账户报告功能正常")
        else:
            logger.error("测试失败：请检查配置和网络连接")
        
        return success


if __name__ == "__main__":
    """主程序入口"""
    
    # 配置日志
    logger.add("logs/messager_{time}.log", rotation="1 day", retention="30 days")
    
    # 加载环境变量
    from dotenv import load_dotenv
    load_dotenv()
    
    import argparse
    parser = argparse.ArgumentParser(description="账户信息推送系统")
    parser.add_argument("--test", action="store_true", help="运行测试模式")
    parser.add_argument("--daemon", action="store_true", help="运行守护进程模式")
    
    args = parser.parse_args()
    
    try:
        messager_main = MessagerMain()
        
        if args.test:
            # 测试模式
            messager_main.run_test()
        elif args.daemon:
            # 守护进程模式
            messager_main.run_scheduler()
        else:
            # 交互模式
            print("账户信息推送系统")
            print("1. 运行测试")
            print("2. 启动定时推送")
            print("3. 退出")
            
            choice = input("请选择操作 (1-3): ").strip()
            
            if choice == "1":
                messager_main.run_test()
            elif choice == "2":
                messager_main.run_scheduler()
            else:
                print("退出程序")
    
    except Exception as e:
        logger.error(f"程序运行失败: {e}")
        sys.exit(1) 