#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据收集器主程序
功能：
1. 获取股票池历史数据
2. 更新股票池最新数据  
3. 定时监控交易时段并自动更新当日数据
"""

import os
import time
import schedule
import pytz
from datetime import datetime, timedelta
from typing import List, Dict
from loguru import logger
from dotenv import load_dotenv
from longport.openapi import Period, AdjustType
from awesometrader.collector import Collector
from awesometrader.datainterface import DataInterface


class DataCollectorMain:
    def __init__(self):
        """初始化数据收集器"""
        # 加载环境变量文件
        load_dotenv()
        
        self.collector = Collector()
        self.data_interface = DataInterface()
        
        # 从环境变量获取配置
        self.start_date_str = os.getenv('START_DATE', '2020-01-01')
        self.stock_pool_file = os.getenv('STOCK_POOL_FILE', 'stock_pool.csv')
        self.update_delay_minutes = int(os.getenv('UPDATE_DELAY_MINUTES', '15'))  # 交易结束后延迟更新时间
        
        # 获取用户所在时区（从系统获取，获取不到设置成东八区）
        try:
            # 获取系统时区
            system_tz = datetime.now().astimezone().tzinfo
            if hasattr(system_tz, 'zone'):
                self.user_timezone = system_tz
                logger.info(f"用户时区（系统获取）: {system_tz.zone}")
            else:
                # 系统时区无法直接获取名称，使用东八区
                self.user_timezone = pytz.timezone('Asia/Shanghai')
                logger.info("用户时区（默认）: Asia/Shanghai")
        except Exception as e:
            # 获取失败，使用东八区
            logger.warning(f"无法获取系统时区: {e}，使用东八区")
            self.user_timezone = pytz.timezone('Asia/Shanghai')
        
        # 市场时区映射
        self.market_timezones = {
            'US': pytz.timezone('America/New_York'),  # 美东时间
            'HK': pytz.timezone('Asia/Hong_Kong'),    # 港股时间
            'CN': pytz.timezone('Asia/Shanghai'),     # A股时间
            'SG': pytz.timezone('Asia/Singapore'),    # 新加坡时间
        }
        
        logger.info(f"数据收集器初始化完成")
        logger.info(f"历史数据开始日期: {self.start_date_str}")
        logger.info(f"股票池文件: {self.stock_pool_file}")
        logger.info(f"交易结束后延迟更新时间: {self.update_delay_minutes}分钟")

    def load_stock_pool(self) -> List[str]:
        """加载股票池"""
        try:
            stock_codes = self.data_interface.load_stock_pool(self.stock_pool_file)
            if stock_codes:
                logger.success(f"成功加载股票池，共{len(stock_codes)}只股票: {stock_codes}")
            else:
                logger.warning("股票池为空或加载失败")
            return stock_codes
        except Exception as e:
            logger.error(f"加载股票池失败: {e}")
            return []

    def get_market_from_stock_code(self, stock_code: str) -> str:
        """从股票代码获取市场信息"""
        if '.' in stock_code:
            market_suffix = stock_code.split('.')[-1].upper()
            if market_suffix == 'US':
                return 'US'
            elif market_suffix == 'HK':
                return 'HK'
            elif market_suffix in ['SH', 'SZ']:  # 上海、深圳
                return 'CN'
            elif market_suffix == 'SG':
                return 'SG'
        return 'UNKNOWN'

    def filter_stocks_by_market(self, stock_codes: List[str], target_market: str) -> List[str]:
        """根据市场过滤股票"""
        filtered_stocks = []
        for stock_code in stock_codes:
            stock_market = self.get_market_from_stock_code(stock_code)
            if stock_market == target_market:
                filtered_stocks.append(stock_code)
        return filtered_stocks

    def collect_historical_data(self, period: Period = Period.Day, adjust_type: AdjustType = AdjustType.ForwardAdjust):
        """
        收集股票池历史数据
        :param period: K线周期
        :param adjust_type: 复权类型
        """
        logger.info("=" * 50)
        logger.info("开始收集历史数据")
        logger.info("=" * 50)
        
        # 加载股票池
        stock_codes = self.load_stock_pool()
        if not stock_codes:
            logger.error("股票池为空，无法收集历史数据")
            return
        
        # 解析日期
        try:
            start_date = datetime.strptime(self.start_date_str, '%Y-%m-%d')
            end_date = datetime.now()
            logger.info(f"历史数据收集时间范围: {start_date.date()} 到 {end_date.date()}")
        except ValueError as e:
            logger.error(f"日期格式错误: {e}")
            return
        
        # 逐个收集股票历史数据
        success_count = 0
        failed_stocks = []
        
        for i, stock_code in enumerate(stock_codes, 1):
            try:
                logger.info(f"[{i}/{len(stock_codes)}] 正在收集 {stock_code} 的历史数据...")
                
                # 获取历史数据
                df = self.collector.get_stock_history(
                    stock_code=stock_code,
                    period=period,
                    adjust_type=adjust_type,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if not df.empty:
                    # 保存数据
                    success = self.data_interface.save_stock_data(
                        stock_code=stock_code,
                        df=df,
                        period=period,
                        file_format='csv',
                        force_update=True
                    )
                    
                    if success:
                        success_count += 1
                        logger.success(f"{stock_code} 历史数据收集完成，共{len(df)}条记录")
                    else:
                        failed_stocks.append(stock_code)
                        logger.error(f"{stock_code} 数据保存失败")
                else:
                    failed_stocks.append(stock_code)
                    logger.warning(f"{stock_code} 未获取到历史数据")
                
                # 避免请求过于频繁
                time.sleep(0.5)
                
            except Exception as e:
                failed_stocks.append(stock_code)
                logger.error(f"收集 {stock_code} 历史数据失败: {e}")
        
        # 汇总结果
        logger.info("=" * 50)
        logger.info("历史数据收集完成")
        logger.info(f"成功: {success_count}/{len(stock_codes)}")
        if failed_stocks:
            logger.warning(f"失败的股票: {failed_stocks}")
        logger.info("=" * 50)

    def update_latest_data_by_market(self, market: str = "ALL", period: Period = Period.Day, adjust_type: AdjustType = AdjustType.ForwardAdjust, count: int = 100):
        """
        根据市场更新最新数据
        :param market: 市场代码 (US, HK, CN, SG, ALL) - ALL代表所有市场
        :param period: K线周期
        :param adjust_type: 复权类型
        :param count: 获取最新数据条数
        """
        logger.info("=" * 50)
        logger.info(f"开始更新 {market} 市场最新数据")
        logger.info("=" * 50)
        
        # 加载股票池
        all_stock_codes = self.load_stock_pool()
        if not all_stock_codes:
            logger.error("股票池为空，无法更新最新数据")
            return
        
        # 根据市场过滤股票（ALL不过滤）
        if market == "ALL":
            stock_codes = all_stock_codes
        else:
            stock_codes = self.filter_stocks_by_market(all_stock_codes, market)
            if not stock_codes:
                logger.warning(f"{market} 市场没有相关股票")
                return
        
        logger.info(f"{market} 市场股票: {stock_codes}")
        
        # 逐个更新股票最新数据
        success_count = 0
        failed_stocks = []
        
        for i, stock_code in enumerate(stock_codes, 1):
            try:
                logger.info(f"[{i}/{len(stock_codes)}] 正在更新 {stock_code} 的最新数据...")
                
                # 获取最新K线数据
                df = self.collector.get_stock_candlesticks(
                    stock_code=stock_code,
                    period=period,
                    count=count,
                    adjust_type=adjust_type
                )
                
                if not df.empty:
                    # 保存数据（与已有数据合并）
                    success = self.data_interface.save_stock_data(
                        stock_code=stock_code,
                        df=df,
                        period=period,
                        file_format='csv',
                        force_update=False
                    )
                    
                    if success:
                        success_count += 1
                        logger.success(f"{stock_code} 最新数据更新完成，共{len(df)}条记录")
                    else:
                        failed_stocks.append(stock_code)
                        logger.error(f"{stock_code} 数据保存失败")
                else:
                    failed_stocks.append(stock_code)
                    logger.warning(f"{stock_code} 未获取到最新数据")
                
                # 避免请求过于频繁
                time.sleep(0.5)
                
            except Exception as e:
                failed_stocks.append(stock_code)
                logger.error(f"更新 {stock_code} 最新数据失败: {e}")
        
        # 汇总结果
        logger.info("=" * 50)
        logger.info(f"{market} 市场最新数据更新完成")
        logger.info(f"成功: {success_count}/{len(stock_codes)}")
        if failed_stocks:
            logger.warning(f"失败的股票: {failed_stocks}")
        logger.info("=" * 50)

    def convert_market_time_to_user_time(self, market_time: datetime.time, market: str) -> datetime:
        """
        将市场时间转换为用户本地时间
        :param market_time: 市场时间 (datetime.time 对象)
        :param market: 市场代码
        :return: 用户本地时间的datetime对象
        """
        try:
            # 获取市场时区
            market_tz = self.market_timezones.get(market, pytz.UTC)
            
            # 从 datetime.time 对象获取时分
            hour = market_time.hour
            minute = market_time.minute
            
            # 创建今天的市场时间
            today = datetime.now(market_tz).date()
            market_datetime = market_tz.localize(datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute)))
            
            # 转换为用户本地时间
            user_datetime = market_datetime.astimezone(self.user_timezone)
            
            return user_datetime
            
        except Exception as e:
            logger.error(f"时间转换失败: {e}")
            # 返回默认时间
            return datetime.now(self.user_timezone)

    def setup_daily_trading_session_update(self):
        """设置每日获取交易时段的任务"""
        # 每天早上00:01获取交易时段信息并设置当日的更新任务
        schedule.every().day.at("00:01").do(self.daily_setup_market_updates)
        logger.info("已设置每日00:01获取交易时段并安排市场更新任务")

    def daily_setup_market_updates(self):
        """每日设置市场更新任务"""
        logger.info("=" * 50)
        logger.info("开始设置今日市场更新任务")
        logger.info("=" * 50)
        
        # 清除今天的旧任务（除了每日00:01的任务）
        schedule.clear('market_update')
        
        # 获取交易时段信息
        sessions = self.collector.get_trading_session()
        
        if not sessions:
            logger.warning("无法获取交易时段信息，使用默认时间安排更新")
            # 使用默认时间
            schedule.every().day.at("16:30").do(self.scheduled_market_update, market="HK").tag('market_update')
            schedule.every().day.at("05:30").do(self.scheduled_market_update, market="US").tag('market_update')
            return
        
        # 根据实际交易时段安排更新任务
        for market_session in sessions:
            market_name = str(market_session.market).split('.')[-1]  # 获取枚举名称，如 "US", "HK", "CN"
            trade_sessions = market_session.trade_sessions
            
            if trade_sessions:
                # 所有市场都使用 trade_session=Intraday 的收盘时间
                intraday_session = None
                for session in trade_sessions:
                    # 查找 trade_session 为 Intraday 的时段
                    session_type = str(session.trade_session).split('.')[-1]  # 获取枚举名称
                    if session_type == 'Intraday':
                        intraday_session = session
                
                if intraday_session:
                    end_time = intraday_session.end_time
                    self._schedule_market_update(market_name, end_time)
                else:
                    logger.warning(f"{market_name} 市场未找到 Intraday 交易时段，跳过安排更新任务")
        
        logger.success("今日市场更新任务设置完成")

    def _schedule_market_update(self, market_name: str, end_time: datetime.time):
        """安排单个市场的更新任务"""
        try:
            # 将市场收盘时间转换为用户本地时间
            market_close_time = self.convert_market_time_to_user_time(end_time, market_name)
            
            # 添加延迟时间
            update_time = market_close_time + timedelta(minutes=self.update_delay_minutes)
            update_time_str = update_time.strftime('%H:%M')
            
            # 安排更新任务
            schedule.every().day.at(update_time_str).do(self.scheduled_market_update, market=market_name).tag('market_update')
            
            # 格式化显示时间
            display_time = f"{end_time.hour:02d}:{end_time.minute:02d}"
            
            logger.info(f"已安排 {market_name} 市场更新任务:")
            logger.info(f"  市场收盘时间: {display_time} ({self.market_timezones.get(market_name, 'UTC')})")
            logger.info(f"  用户本地更新时间: {update_time_str} ({self.user_timezone})")
            
        except Exception as e:
            logger.error(f"安排 {market_name} 市场更新任务失败: {e}")

    def scheduled_market_update(self, market: str):
        """执行定时市场更新任务"""
        logger.info(f"执行 {market} 市场定时更新任务")
        try:
            # 根据市场更新对应股票
            self.update_latest_data_by_market(market)
            logger.success(f"{market} 市场定时更新任务完成")
        except Exception as e:
            logger.error(f"{market} 市场定时更新任务失败: {e}")

    def run_scheduler(self):
        """运行定时任务调度器"""
        logger.info("启动定时任务调度器...")
        logger.info("按 Ctrl+C 退出")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            logger.info("收到退出信号，正在停止定时任务调度器...")
        except Exception as e:
            logger.error(f"定时任务调度器异常: {e}")

    def run_interactive_mode(self):
        """运行交互模式"""
        while True:
            print("\n" + "=" * 50)
            print("数据收集器 - 交互模式")
            print("=" * 50)
            print("1. 收集历史数据")
            print("2. 更新最新数据")
            print("3. 查看交易时段")
            print("4. 启动定时更新")
            print("5. 退出")
            print("-" * 50)
            
            try:
                choice = input("请选择操作 (1-5): ").strip()
                
                if choice == '1':
                    logger.info("用户选择：收集历史数据")
                    self.collect_historical_data()
                elif choice == '2':
                    logger.info("用户选择：更新最新数据")
                    self.update_latest_data_by_market("ALL")
                elif choice == '3':
                    logger.info("用户选择：查看交易时段")
                    self.collector.get_trading_session()
                elif choice == '4':
                    logger.info("用户选择：启动定时更新")
                    self.setup_daily_trading_session_update()
                    self.daily_setup_market_updates()
                    self.run_scheduler()
                elif choice == '5':
                    logger.info("用户选择：退出程序")
                    break
                else:
                    print("无效选择，请重新输入")
                    
            except KeyboardInterrupt:
                logger.info("收到退出信号")
                break
            except Exception as e:
                logger.error(f"交互模式错误: {e}")


def main():
    """主函数"""
    
    # 设置日志
    logger.add("logs/data_collector_{time}.log", rotation="1 day", retention="30 days", 
               format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
    
    logger.info("数据收集器启动")
    
    # 创建数据收集器实例
    collector_main = DataCollectorMain()
    
    # 启动交互模式
    logger.info("启动交互模式")
    collector_main.run_interactive_mode()


if __name__ == "__main__":
    main()


