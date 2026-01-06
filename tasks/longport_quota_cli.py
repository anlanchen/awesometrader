#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据收集器主程序 (CLI模式)
功能：
1. 获取股票池历史数据
2. 更新股票池最新数据  
3. 同步自选股到股票池
4. 查看交易时段
"""

import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import time
from datetime import datetime
from typing import List
from loguru import logger
from longport.openapi import Period, AdjustType
from awesometrader.collector import LongPortQuotaAPI
from awesometrader.data import DataInterface

class LongPortQuotaCLI:
    def __init__(self):
        """初始化数据收集器"""
        self.collector = LongPortQuotaAPI()
        self.data_interface = DataInterface()
        
        # 配置参数
        self.start_date_str = '2020-01-01'
        self.stock_pool_file = 'stock_pool.csv'

    def load_stock_pool(self) -> List[str]:
        """加载股票池"""
        try:
            stock_codes = self.data_interface.load_stock_pool(self.stock_pool_file)
            if stock_codes:
                logger.info(f"成功加载股票池，共{len(stock_codes)}只股票")
            else:
                logger.warning("股票池为空或加载失败")
            return stock_codes
        except Exception as e:
            logger.error(f"加载股票池失败: {e}")
            return []

    @staticmethod
    def get_market_from_stock_code(stock_code: str) -> str:
        """从股票代码获取市场信息"""
        if '.' in stock_code:
            market_suffix = stock_code.split('.')[-1].upper()
            if market_suffix == 'US':
                return 'US'
            elif market_suffix == 'HK':
                return 'HK'
            elif market_suffix in ['SH', 'SZ']:
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

    def sync_watchlist(self):
        """同步自选股到股票池文件"""
        logger.info("=" * 50)
        logger.info("开始同步自选股到股票池")
        logger.info("=" * 50)
        
        try:
            logger.info("正在获取自选股列表...")
            watchlist_securities = self.collector.get_stock_list()
            
            if not watchlist_securities:
                logger.warning("未获取到自选股，同步停止")
                return
            
            stock_codes = [security.symbol for security in watchlist_securities]
            logger.info(f"获取到 {len(stock_codes)} 只自选股")

            # 获取股票基础信息以获取中文名称
            logger.info("正在获取股票基础信息（包括中文名称）...")
            stock_info_dict = self.collector.get_stock_basic_info(stock_codes)

            # 准备股票数据
            stock_data = []
            for security in watchlist_securities:
                stock_code = str(security.symbol)
                stock_name = str(security.name)
                if stock_code in stock_info_dict:
                    info = stock_info_dict[stock_code]
                    # stock_name列优先显示中文，如果没有中文则显示英文
                    stock_name = str(info.name_cn) if hasattr(info, 'name_cn') and info.name_cn else stock_name

                # 将原始信息传入，具体使用哪个名称由接口决定
                stock_data.append({
                    'stock_code': stock_code,
                    'stock_name': stock_name
                })
            
            # 调用 DataInterface 的 save_stock_pool 接口保存股票池
            success = self.data_interface.save_stock_pool(self.stock_pool_file, stock_data)
            if not success:
                logger.error("股票池文件保存失败")
                sys.exit(1)
            
            logger.info(f"文件包含列: stock_code, stock_name")
            
        except Exception as e:
            logger.error(f"同步自选股到股票池失败: {e}")
            sys.exit(1)

    def get_history(self, market: str = "ALL", period_str: str = "Day"):
        """收集历史数据"""
        logger.info(f"开始收集历史数据 (市场: {market}, 周期: {period_str})")
        
        period_map = {
            "Day": Period.Day,
            "Week": Period.Week,
            "Month": Period.Month,
            "Year": Period.Year
        }
        period = period_map.get(period_str, Period.Day)

        all_stock_codes = self.load_stock_pool()
        if not all_stock_codes:
            return

        if market == "ALL":
            stock_codes = all_stock_codes
        else:
            stock_codes = self.filter_stocks_by_market(all_stock_codes, market)
            
        if not stock_codes:
            logger.warning(f"{market} 市场没有相关股票")
            return

        try:
            start_date = datetime.strptime(self.start_date_str, '%Y-%m-%d')
            end_date = datetime.now()
        except ValueError as e:
            logger.error(f"日期格式错误: {e}")
            return

        success_count = 0
        for i, stock_code in enumerate(stock_codes, 1):
            try:
                logger.info(f"[{i}/{len(stock_codes)}] 正在收集 {stock_code} 的历史数据...")
                df = self.collector.get_stock_history(
                    stock_code=stock_code,
                    period=period,
                    adjust_type=AdjustType.ForwardAdjust,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if not df.empty:
                    success = self.data_interface.save_stock_data(
                        stock_code=stock_code,
                        df=df,
                        period=period,
                        file_format='csv',
                        force_update=True
                    )
                    if success:
                        success_count += 1
                time.sleep(0.5) # Rate limit
                
            except Exception as e:
                logger.error(f"收集 {stock_code} 失败: {e}")

        logger.success(f"历史数据收集完成: {success_count}/{len(stock_codes)} 成功")

    def update_latest(self, market: str = "ALL", period_str: str = "Day"):
        """更新最新数据"""
        logger.info(f"开始更新最新数据 (市场: {market}, 周期: {period_str})")
        
        period_map = {
            "Day": Period.Day,
            "Week": Period.Week,
            "Month": Period.Month,
            "Year": Period.Year
        }
        period = period_map.get(period_str, Period.Day)

        all_stock_codes = self.load_stock_pool()
        if not all_stock_codes:
            return

        if market == "ALL":
            stock_codes = all_stock_codes
        else:
            stock_codes = self.filter_stocks_by_market(all_stock_codes, market)
            
        if not stock_codes:
            logger.warning(f"{market} 市场没有相关股票")
            return

        success_count = 0
        for i, stock_code in enumerate(stock_codes, 1):
            try:
                logger.info(f"[{i}/{len(stock_codes)}] 正在更新 {stock_code} 的最新数据...")
                df = self.collector.get_stock_candlesticks(
                    stock_code=stock_code,
                    period=period,
                    count=1000,
                    adjust_type=AdjustType.ForwardAdjust
                )
                
                if not df.empty:
                    success = self.data_interface.save_stock_data(
                        stock_code=stock_code,
                        df=df,
                        period=period,
                        file_format='csv',
                        force_update=False
                    )
                    if success:
                        success_count += 1
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"更新 {stock_code} 失败: {e}")

        logger.success(f"最新数据更新完成: {success_count}/{len(stock_codes)} 成功")

    def show_sessions(self):
        """查看交易时段"""
        logger.info("获取交易时段信息...")
        sessions = self.collector.get_trading_session()
        if sessions:
            logger.success("交易时段信息获取成功")
        else:
            logger.error("交易时段信息获取失败")

def main():
    # 配置日志
    logger.remove()
    logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO")
    logger.add("logs/longport_quota_cli_{time:YYYY-MM-DD}.log", rotation="1 day", retention="7 days")

    parser = argparse.ArgumentParser(description="AwesomeTrader 数据收集器 CLI")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # Command: show_sessions
    subparsers.add_parser("show_sessions", help="查看交易时段")

    # Command: sync_watchlist
    subparsers.add_parser("sync_watchlist", help="同步自选股到股票池")

    # Command: get_history
    parser_history = subparsers.add_parser("get_history", help="收集历史数据")
    parser_history.add_argument("--market", default="ALL", help="市场代码 (US, HK, CN, SG, ALL)")
    parser_history.add_argument("--period", default="Day", help="K线周期 (Day, Week, Month, Year)")

    # Command: update_latest
    parser_update = subparsers.add_parser("update_latest", help="更新最新数据")
    parser_update.add_argument("--market", default="ALL", help="市场代码 (US, HK, CN, SG, ALL)")
    parser_update.add_argument("--period", default="Day", help="K线周期 (Day, Week, Month, Year)")

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Initialize CLI
    cli = LongPortQuotaCLI()

    try:
        if args.command == "show_sessions":
            cli.show_sessions()
        elif args.command == "sync_watchlist":
            cli.sync_watchlist()
        elif args.command == "get_history":
            cli.get_history(market=args.market, period_str=args.period)
        elif args.command == "update_latest":
            cli.update_latest(market=args.market, period_str=args.period)
            
    except KeyboardInterrupt:
        logger.info("用户中断操作")
        sys.exit(0)
    except Exception as e:
        logger.error(f"执行出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
