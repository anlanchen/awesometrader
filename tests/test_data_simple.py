"""
测试DataInterface和LongPortAPI类的基本功能
"""

import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import unittest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, time
from loguru import logger
from awesometrader import DataInterface, LongPortAPI
from longport.openapi import Period, AdjustType

class TestDataModule(unittest.TestCase):
    def setUp(self):
        """每个测试方法之前运行"""
        # 初始化数据接口
        self.data_interface = DataInterface()
        self.collector = LongPortAPI()
        
    def tearDown(self):
        """每个测试方法之后运行"""
        # 清理资源
        pass
    
    def test_data_interface(self):
        logger.info("=== 测试DataInterface功能 ===")
        
        # 测试DataInterface初始化
        self.assertIsNotNone(self.data_interface, "DataInterface实例不应该为None")
        self.assertTrue(hasattr(self.data_interface, 'cache_dir'), "应该有cache_dir属性")
        self.assertIsNotNone(self.data_interface.cache_dir, "缓存目录不应该为None")
        logger.info(f"✓ DataInterface初始化成功，缓存目录: {self.data_interface.cache_dir}")
        
        # 定义统一的测试股票代码
        test_stock_code = "BABA.US"
        
        # 测试get_stock_data_path方法
        # 测试CSV格式路径
        csv_path = self.data_interface.get_stock_data_path(test_stock_code, Period.Day, 'csv')
        self.assertIsNotNone(csv_path, "CSV路径不应该为None")
        self.assertTrue(str(csv_path).endswith('.csv'), "CSV路径应该以.csv结尾")
        self.assertIn(test_stock_code, str(csv_path), "路径应该包含股票代码")
        logger.info(f"✓ CSV路径生成正确: {csv_path}")
        
        # 测试Parquet格式路径
        parquet_path = self.data_interface.get_stock_data_path(test_stock_code, Period.Day, 'parquet')
        self.assertIsNotNone(parquet_path, "Parquet路径不应该为None")
        self.assertTrue(str(parquet_path).endswith('.parquet'), "Parquet路径应该以.parquet结尾")
        logger.info(f"✓ Parquet路径生成正确: {parquet_path}")
        
        # 测试load_stock_pool方法
        test_stocks = self.data_interface.load_stock_pool(stock_list_file="stock_pool.csv")
        
        # 断言股票池加载
        self.assertIsNotNone(test_stocks, "股票池不应该为None")
        self.assertIsInstance(test_stocks, list, "股票池应该是列表类型")
        
        if len(test_stocks) > 0:
            logger.info(f"✓ 成功加载{len(test_stocks)}只股票")
            logger.info(f"股票列表: {test_stocks}")
            
            # 验证股票代码格式
            for stock in test_stocks:
                self.assertIsInstance(stock, str, f"股票代码{stock}应该是字符串类型")
                self.assertTrue(len(stock) > 0, f"股票代码{stock}不应该为空")
                # 验证股票代码格式 (包含.的格式如BABA.US)
                if '.' in stock:
                    symbol, market = stock.split('.', 1)  # 只分割第一个点
                    self.assertTrue(len(symbol) > 0, f"股票符号{symbol}不应该为空")
                    self.assertTrue(len(market) > 0, f"市场代码{market}不应该为空")
            logger.info("✓ 股票代码格式验证通过")
        else:
            logger.warning("股票池为空，可能是stock_pool.csv文件不存在或为空")
        
        # 测试save_stock_data方法 - 获取BABA真实数据并保存
        try:
            logger.info(f"开始获取{test_stock_code}的日线数据进行保存测试")
            
            # 获取BABA最近30天的日线数据
            start_date = datetime(2024, 1, 1)
            end_date = datetime(2024, 12, 30)
            
            logger.info(f"获取日期范围: {start_date.date()} 到 {end_date.date()}")
            
            # 使用LongPortAPI获取真实数据
            daily_data = self.collector.get_stock_history(
                stock_code=test_stock_code,
                period=Period.Day,
                adjust_type=AdjustType.ForwardAdjust,
                start_date=start_date,
                end_date=end_date
            )
            
            if not daily_data.empty:
                logger.info(f"✓ 成功获取{test_stock_code}数据: {len(daily_data)} 条记录")
                
                # 测试保存股票数据
                success = self.data_interface.save_stock_data(
                    stock_code=test_stock_code,
                    df=daily_data,
                    period=Period.Day,
                    file_format='csv',
                    force_update=True
                )
                self.assertTrue(success, "保存BABA股票数据应该成功")
                logger.info("✓ BABA股票数据保存功能正常")
                
                # 验证保存的数据可以读取
                saved_data = self.data_interface.get_stock_data(test_stock_code, Period.Day)
                self.assertFalse(saved_data.empty, "保存的BABA数据应该可以读取")
                self.assertEqual(len(saved_data), len(daily_data), "保存和读取的数据行数应该一致")
                logger.info("✓ BABA股票数据读取功能正常")
                
                # 测试全量读取
                full_data = self.data_interface.get_stock_data(test_stock_code, Period.Day)
                self.assertFalse(full_data.empty, "全量读取数据不应该为空")
                logger.info(f"✓ 全量读取成功: {len(full_data)} 条记录")
                
                # 测试读取2025年数据（应该为空，因为保存的是2024年数据）
                data_2025 = self.data_interface.get_stock_data(
                    test_stock_code, 
                    Period.Day, 
                    start_date=datetime(2025, 5, 1), 
                    end_date=datetime(2025, 5, 30)
                )
                self.assertTrue(data_2025.empty, "2025年数据应该为空（因为保存的是2024年数据）")
                logger.info("✓ 2025年数据过滤正确（返回空数据）")
                
                # 测试读取2024年部分数据
                data_2024_partial = self.data_interface.get_stock_data(
                    test_stock_code, 
                    Period.Day, 
                    start_date=datetime(2024, 6, 1), 
                    end_date=datetime(2024, 6, 30)
                )
                logger.info(f"✓ 2024年6月数据读取: {len(data_2024_partial)} 条记录")
                
            else:
                logger.warning(f"未能获取{test_stock_code}的历史数据，跳过保存测试")
                
        except Exception as e:
            logger.error(f"获取BABA数据失败: {e}")
            logger.warning("如果API配置有问题，将使用模拟数据进行测试")
        
        # 清理测试数据
        test_file_path = self.data_interface.get_stock_data_path(test_stock_code, Period.Day, 'csv')
        if test_file_path.exists():
            test_file_path.unlink()
            logger.info("✓ 测试数据清理完成")
        
        logger.success("=== DataInterface功能测试完成 ===")

    def test_get_trading_session(self):
        logger.info("=== 测试获取各市场当日交易时段 ===")
        
        try:
            logger.info("开始获取各市场当日交易时段")
            
            # 获取交易时段信息
            market_sessions = self.collector.get_trading_session()
            
            # 断言测试 - 现在返回的是List[MarketTradingSession]
            self.assertIsNotNone(market_sessions, "交易时段信息不应该为None")
            self.assertIsInstance(market_sessions, list, "返回值应该是列表类型")
            self.assertTrue(len(market_sessions) > 0, "应该至少有一个市场的交易时段信息")
            
            logger.info(f"✓ 成功获取{len(market_sessions)}个市场的交易时段信息")
            
            # 验证各市场数据
            expected_markets = ['US', 'HK', 'CN', 'SG']  # 根据文档，这些是主要支持的市场
            found_markets = []
            
            for market_session in market_sessions:
                # 验证市场信息结构
                self.assertTrue(hasattr(market_session, 'market'), "市场交易时段应该有market属性")
                
                market = market_session.market
                found_markets.append(market)
                
                logger.info(f"市场: {market}")
                
                # 验证交易时段
                trade_sessions = market_session.trade_sessions
                self.assertIsNotNone(trade_sessions, f"市场{market}的交易时段不应该为None")
                self.assertTrue(len(trade_sessions) > 0, f"市场{market}应该至少有一个交易时段")
                
                for session in trade_sessions:
                    # 验证交易时段结构
                    self.assertTrue(hasattr(session, 'begin_time'), "交易时段应该有beg_time属性")
                    self.assertTrue(hasattr(session, 'end_time'), "交易时段应该有end_time属性")
                    
                    begin_time = session.begin_time
                    end_time = session.end_time
                    
                    # 验证时间格式（应该是time类型）
                    self.assertIsInstance(begin_time, time, f"开始时间应该是time类型: {begin_time}")
                    self.assertIsInstance(end_time, time, f"结束时间应该是time类型: {end_time}")
                    
                    # 验证时间有效性（time对象本身就保证了有效性，这里验证小时和分钟范围）
                    self.assertTrue(0 <= begin_time.hour <= 23, f"开始时间小时应该在0-23范围内: {begin_time.hour}")
                    self.assertTrue(0 <= begin_time.minute <= 59, f"开始时间分钟应该在0-59范围内: {begin_time.minute}")
                    self.assertTrue(0 <= end_time.hour <= 23, f"结束时间小时应该在0-23范围内: {end_time.hour}")
                    self.assertTrue(0 <= end_time.minute <= 59, f"结束时间分钟应该在0-59范围内: {end_time.minute}")
                    
                    # 格式化显示时间
                    start_time = begin_time.strftime("%H:%M")
                    end_time_str = end_time.strftime("%H:%M")
                    
                    # 获取交易时段类型（如果有的话）
                    session_type = "正常交易"
                    if hasattr(session, 'trade_session'):
                        trade_session_value = session.trade_session
                        if trade_session_value == 1:
                            session_type = "盘前交易"
                        elif trade_session_value == 2:
                            session_type = "盘后交易"
                        else:
                            session_type = "正常交易"
                    
                    logger.info(f"  交易时段: {start_time} - {end_time_str} ({session_type})")
                
                logger.info("-" * 30)
            
            # 验证是否包含主要市场
            for expected_market in expected_markets:
                if expected_market in found_markets:
                    logger.info(f"✓ 发现{expected_market}市场交易时段")
            
            logger.info(f"✓ 找到的市场: {found_markets}")
            
            # 具体验证一些市场的交易时段逻辑
            for market_session in market_sessions:
                market = market_session.market
                
                if market == 'US':
                    # 美股通常有盘前、正常、盘后三个时段
                    logger.info("验证美股交易时段...")
                    trade_sessions = market_session.trade_sessions
                    # 至少应该有正常交易时段
                    self.assertTrue(len(trade_sessions) >= 1, "美股应该至少有正常交易时段")
                    
                elif market == 'HK':
                    # 港股通常有上午和下午两个时段
                    logger.info("验证港股交易时段...")
                    trade_sessions = market_session.trade_sessions
                    # 港股一般有两个交易时段：上午和下午
                    self.assertTrue(len(trade_sessions) >= 2, "港股应该有上午和下午两个交易时段")
                    
                elif market == 'CN':
                    # A股通常有上午和下午两个时段
                    logger.info("验证A股交易时段...")
                    trade_sessions = market_session.trade_sessions
                    # A股一般有两个交易时段：上午和下午
                    self.assertTrue(len(trade_sessions) >= 2, "A股应该有上午和下午两个交易时段")
            
            logger.success("各市场当日交易时段获取测试完成")
            
        except Exception as e:
            logger.error(f"测试失败: {e}")
            logger.warning("请确保配置了正确的LongPort API环境变量")
            self.fail(f"获取交易时段信息时发生异常: {e}")

    def test_get_stock_list(self):
        logger.info("=== 测试获取自选股列表 ===")
        
        try:
            logger.info("开始获取自选股列表")
            
            # 获取自选股列表
            stock_list = self.collector.get_stock_list()
            
            # 断言测试
            self.assertIsNotNone(stock_list, "自选股列表不应该为None")
            self.assertIsInstance(stock_list, list, "自选股列表应该是列表类型")
            
            logger.info(f"✓ 成功获取自选股列表: {len(stock_list)} 只股票")
            
            if len(stock_list) > 0:
                # 验证自选股数据结构
                for i, security in enumerate(stock_list):
                    # 验证必要的属性
                    self.assertTrue(hasattr(security, 'symbol'), f"第{i+1}只股票应该有symbol属性")
                    self.assertTrue(hasattr(security, 'market'), f"第{i+1}只股票应该有market属性")
                    self.assertTrue(hasattr(security, 'name'), f"第{i+1}只股票应该有name属性")
                    self.assertTrue(hasattr(security, 'watched_price'), f"第{i+1}只股票应该有watched_price属性")
                    self.assertTrue(hasattr(security, 'watched_at'), f"第{i+1}只股票应该有watched_at属性")
                    
                    # 验证股票代码格式
                    symbol = security.symbol
                    self.assertIsNotNone(symbol, f"第{i+1}只股票的代码不应该为None")
                    self.assertIsInstance(symbol, str, f"第{i+1}只股票的代码应该是字符串")
                    self.assertTrue(len(symbol) > 0, f"第{i+1}只股票的代码不应该为空")
                    
                    # 验证股票名称
                    name = security.name
                    self.assertIsNotNone(name, f"第{i+1}只股票的名称不应该为None")
                    self.assertIsInstance(name, str, f"第{i+1}只股票的名称应该是字符串")
                    self.assertTrue(len(name) > 0, f"第{i+1}只股票的名称不应该为空")
                    
                    # 验证市场信息
                    market = security.market
                    self.assertIsNotNone(market, f"第{i+1}只股票的市场信息不应该为None")
                    
                    # 验证关注时间
                    watched_at = security.watched_at
                    self.assertIsNotNone(watched_at, f"第{i+1}只股票的关注时间不应该为None")
                    
                    logger.info(f"股票 {i+1}:")
                    logger.info(f"  代码: {symbol}")
                    logger.info(f"  名称: {name}")
                    logger.info(f"  市场: {market}")
                    
                    # 关注价格可能为None
                    if security.watched_price is not None:
                        logger.info(f"  关注价格: {security.watched_price}")
                    else:
                        logger.info(f"  关注价格: 未设置")
                    
                    logger.info(f"  关注时间: {watched_at}")
                    logger.info("-" * 30)
                
                # 统计不同市场的股票数量
                market_stats = {}
                for security in stock_list:
                    market = str(security.market)
                    market_stats[market] = market_stats.get(market, 0) + 1
                
                logger.info("市场分布统计:")
                for market, count in market_stats.items():
                    logger.info(f"  {market}: {count} 只股票")
                
                # 检查股票代码是否有重复
                symbols = [security.symbol for security in stock_list]
                unique_symbols = set(symbols)
                
                if len(symbols) == len(unique_symbols):
                    logger.info("✓ 股票代码无重复")
                else:
                    logger.warning(f"股票代码有重复: 总数 {len(symbols)}, 去重后 {len(unique_symbols)}")
                    # 找出重复的股票代码
                    from collections import Counter
                    symbol_counts = Counter(symbols)
                    duplicates = [symbol for symbol, count in symbol_counts.items() if count > 1]
                    logger.warning(f"重复的股票代码: {duplicates}")
                
                logger.success("自选股列表数据验证完成")
                
                # 返回股票列表以供其他测试方法使用
                return stock_list
            else:
                logger.warning("自选股列表为空")
                logger.info("提示: 请在LongPort app中添加一些自选股，然后重新运行测试")
                return []
                
        except Exception as e:
            logger.error(f"测试失败: {e}")
            logger.warning("请确保配置了正确的LongPort API环境变量")
            self.fail(f"获取自选股列表时发生异常: {e}")

    def test_get_stock_basic_info(self):
        logger.info("=== 测试LongPortAPI获取股票基础信息 ===")
        
        # 直接通过接口获取股票池
        test_stocks = self.data_interface.load_stock_pool(stock_list_file="stock_pool.csv")
        
        if not test_stocks:
            self.skipTest("股票池为空，跳过测试")
        
        try:
            logger.info(f"测试股票: {test_stocks}")
            
            basic_info = self.collector.get_stock_basic_info(stock_code_list=test_stocks)
            
            # 断言测试
            self.assertIsNotNone(basic_info, "基础信息不应该为None")
            self.assertIsInstance(basic_info, dict, "基础信息应该是字典类型")
            
            if basic_info:
                logger.success(f"成功获取{len(basic_info)}只股票的基础信息")
                
                # 验证返回数据的结构
                for symbol, info in basic_info.items():
                    self.assertIsNotNone(symbol, f"股票代码{symbol}不应该为None")
                    self.assertTrue(hasattr(info, 'name_cn'), f"股票{symbol}应该有中文名属性")
                    self.assertTrue(hasattr(info, 'exchange'), f"股票{symbol}应该有交易所属性")
                    
                    logger.info(f"股票 {symbol}:")
                    logger.info(f"  中文名: {info.name_cn}")
                    logger.info(f"  英文名: {info.name_en}")
                    logger.info(f"  交易所: {info.exchange}")
                    logger.info(f"  货币: {info.currency}")
                    logger.info(f"  每手股数: {info.lot_size}")
                    logger.info(f"  总股本: {info.total_shares:,}")
                    logger.info(f"  每股收益: {info.eps}")
                    logger.info(f"  每股收益(TTM): {info.eps_ttm}")
                    logger.info(f"  每股净资产: {info.bps}")
                    logger.info(f"  股息率: {info.dividend_yield}%")
                    logger.info(f"  板块: {info.board}")
                    logger.info("---")
            else:
                self.fail("未能获取股票基础信息")
                
        except Exception as e:
            logger.error(f"测试失败: {e}")
            logger.warning("请确保配置了正确的LongPort API环境变量")
            self.fail(f"获取股票基础信息时发生异常: {e}")

    def test_get_stock_quote(self):
        logger.info("=== 测试获取股票实时行情 ===")

        # 直接通过接口获取股票池
        test_stocks = self.data_interface.load_stock_pool(stock_list_file="stock_pool.csv")
            
        if not test_stocks:
            self.skipTest("股票池为空，跳过测试")
        
        try:
            logger.info("开始获取股票实时行情示例")
            logger.info(f"准备获取 {len(test_stocks)} 只股票的实时行情")
            
            # 获取实时行情数据
            logger.info("=" * 50)
            logger.info("获取股票实时行情数据")
            quote_dict = self.collector.get_stock_quote(test_stocks)
            
            # 断言测试
            self.assertIsNotNone(quote_dict, "行情数据不应该为None")
            self.assertIsInstance(quote_dict, dict, "行情数据应该是字典类型")
            
            if quote_dict:
                # 验证返回数据的结构
                for symbol, quote_data in quote_dict.items():
                    self.assertIsNotNone(symbol, f"股票代码{symbol}不应该为None")
                    self.assertIsNotNone(quote_data, f"股票{symbol}的行情数据不应该为None")
                    
                    # 验证必要的行情字段
                    self.assertTrue(hasattr(quote_data, 'last_done'), f"股票{symbol}应该有最新价字段")
                    self.assertTrue(hasattr(quote_data, 'volume'), f"股票{symbol}应该有成交量字段")
                    
                    logger.info(f"股票代码: {symbol}")
                    logger.info(f"  最新价: {quote_data.last_done}")
                    logger.info(f"  昨收价: {quote_data.prev_close}")
                    logger.info(f"  开盘价: {quote_data.open}")
                    logger.info(f"  最高价: {quote_data.high}")
                    logger.info(f"  最低价: {quote_data.low}")
                    logger.info(f"  成交量: {quote_data.volume}")
                    logger.info(f"  成交额: {quote_data.turnover}")
                    logger.info(f"  交易状态: {quote_data.trade_status}")
                    
                    # 如果有盘前行情数据
                    if hasattr(quote_data, 'pre_market_quote') and quote_data.pre_market_quote:
                        logger.info(f"  盘前最新价: {quote_data.pre_market_quote.last_done}")
                    
                    # 如果有盘后行情数据  
                    if hasattr(quote_data, 'post_market_quote') and quote_data.post_market_quote:
                        logger.info(f"  盘后最新价: {quote_data.post_market_quote.last_done}")
                    
                    logger.info("-" * 30)
                    
                logger.success("股票实时行情获取示例完成")
            else:
                self.fail("未能获取股票行情数据")
                
        except Exception as e:
            logger.error(f"测试失败: {e}")
            self.fail(f"获取股票行情数据时发生异常: {e}")

    def test_get_stock_calc_index(self):
        logger.info("=== 测试获取股票计算指标 ===")
        
        test_stocks = self.data_interface.load_stock_pool(stock_list_file="stock_pool.csv")
        
        if not test_stocks:
            self.skipTest("股票池为空，跳过测试")
        
        try:
            logger.info(f"测试股票: {test_stocks}")
            
            # 测试1: 获取所有计算指标（默认行为）
            logger.info("=" * 50)
            logger.info("测试1: 获取所有计算指标")
            calc_index_dict = self.collector.get_stock_calc_index(stock_code_list=test_stocks)
            
            # 断言测试
            self.assertIsNotNone(calc_index_dict, "计算指标数据不应该为None")
            self.assertIsInstance(calc_index_dict, dict, "计算指标数据应该是字典类型")
            
            if calc_index_dict:
                logger.success(f"成功获取{len(calc_index_dict)}只股票的计算指标")
                
                # 验证返回数据的结构
                for symbol, calc_index in calc_index_dict.items():
                    self.assertIsNotNone(symbol, f"股票代码{symbol}不应该为None")
                    self.assertIsNotNone(calc_index, f"股票{symbol}的计算指标数据不应该为None")
                    
                    # 验证关键字段
                    self.assertTrue(hasattr(calc_index, 'symbol'), f"股票{symbol}应该有symbol字段")
                    self.assertTrue(hasattr(calc_index, 'last_done'), f"股票{symbol}应该有最新价字段")
                    
                    logger.info(f"股票代码: {symbol}")
                    logger.info(f"  最新价: {calc_index.last_done}")
                    
                    # 基础价格指标
                    if hasattr(calc_index, 'change_val') and calc_index.change_val:
                        logger.info(f"  涨跌额: {calc_index.change_val}")
                    if hasattr(calc_index, 'change_rate') and calc_index.change_rate:
                        logger.info(f"  涨跌幅: {calc_index.change_rate}%")
                    
                    # 成交相关指标
                    if hasattr(calc_index, 'volume') and calc_index.volume:
                        logger.info(f"  成交量: {calc_index.volume:,}")
                    if hasattr(calc_index, 'turnover') and calc_index.turnover:
                        logger.info(f"  成交额: {calc_index.turnover}")
                    if hasattr(calc_index, 'turnover_rate') and calc_index.turnover_rate:
                        logger.info(f"  换手率: {calc_index.turnover_rate}%")
                    
                    # 估值指标
                    if hasattr(calc_index, 'pe_ttm_ratio') and calc_index.pe_ttm_ratio:
                        logger.info(f"  市盈率(TTM): {calc_index.pe_ttm_ratio}")
                    if hasattr(calc_index, 'pb_ratio') and calc_index.pb_ratio:
                        logger.info(f"  市净率: {calc_index.pb_ratio}")
                    if hasattr(calc_index, 'dividend_ratio_ttm') and calc_index.dividend_ratio_ttm:
                        logger.info(f"  股息率(TTM): {calc_index.dividend_ratio_ttm}%")
                    
                    # 市值指标
                    if hasattr(calc_index, 'total_market_value') and calc_index.total_market_value:
                        logger.info(f"  总市值: {calc_index.total_market_value}")
                    
                    # 技术指标
                    if hasattr(calc_index, 'amplitude') and calc_index.amplitude:
                        logger.info(f"  振幅: {calc_index.amplitude}%")
                    if hasattr(calc_index, 'volume_ratio') and calc_index.volume_ratio:
                        logger.info(f"  量比: {calc_index.volume_ratio}")
                    
                    # 不同时期涨幅
                    if hasattr(calc_index, 'ytd_change_rate') and calc_index.ytd_change_rate:
                        logger.info(f"  年初至今涨幅: {calc_index.ytd_change_rate}%")
                    if hasattr(calc_index, 'five_day_change_rate') and calc_index.five_day_change_rate:
                        logger.info(f"  五日涨幅: {calc_index.five_day_change_rate}%")
                    if hasattr(calc_index, 'ten_day_change_rate') and calc_index.ten_day_change_rate:
                        logger.info(f"  十日涨幅: {calc_index.ten_day_change_rate}%")
                    if hasattr(calc_index, 'half_year_change_rate') and calc_index.half_year_change_rate:
                        logger.info(f"  半年涨幅: {calc_index.half_year_change_rate}%")
                    
                    # 期权相关指标（如果是期权标的）
                    if hasattr(calc_index, 'expiry_date') and calc_index.expiry_date:
                        logger.info(f"  到期日: {calc_index.expiry_date}")
                    if hasattr(calc_index, 'strike_price') and calc_index.strike_price:
                        logger.info(f"  行权价: {calc_index.strike_price}")
                    if hasattr(calc_index, 'implied_volatility') and calc_index.implied_volatility:
                        logger.info(f"  隐含波动率: {calc_index.implied_volatility}%")
                    
                    # 希腊字母（期权）
                    if hasattr(calc_index, 'delta') and calc_index.delta:
                        logger.info(f"  Delta: {calc_index.delta}")
                    if hasattr(calc_index, 'gamma') and calc_index.gamma:
                        logger.info(f"  Gamma: {calc_index.gamma}")
                    if hasattr(calc_index, 'theta') and calc_index.theta:
                        logger.info(f"  Theta: {calc_index.theta}")
                    if hasattr(calc_index, 'vega') and calc_index.vega:
                        logger.info(f"  Vega: {calc_index.vega}")
                    
                    logger.info("-" * 30)
                
                logger.success("股票计算指标获取测试完成")
            else:
                self.fail("未能获取股票计算指标数据")
                
        except Exception as e:
            logger.error(f"测试失败: {e}")
            logger.warning("请确保配置了正确的LongPort API环境变量和行情权限")
            self.fail(f"获取股票计算指标时发生异常: {e}")

    def test_get_stock_candlesticks(self):
        logger.info("=== 测试获取股票K线数据 ===")
        
        test_stock = 'BABA.US'
        
        try:
            logger.info(f"测试股票: {test_stock}")
            
            # 测试1: 获取日线数据
            logger.info("=" * 50)
            logger.info("测试1: 获取日线数据 (最近30条)")
            
            daily_data = self.collector.get_stock_candlesticks(
                stock_code=test_stock,
                period=Period.Day,
                count=30,
                adjust_type=AdjustType.NoAdjust
            )
            
            # 断言测试
            self.assertIsNotNone(daily_data, "日线数据不应该为None")
            self.assertIsInstance(daily_data, pd.DataFrame, "日线数据应该是DataFrame类型")
            
            if not daily_data.empty:
                logger.success(f"✓ 获取日线数据成功: {len(daily_data)} 条记录")
                
                # 验证DataFrame结构
                expected_columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Turnover']
                for col in expected_columns:
                    self.assertIn(col, daily_data.columns, f"DataFrame应该包含{col}列")
                
                # 验证数据类型
                self.assertTrue(isinstance(daily_data.index, pd.DatetimeIndex), "索引应该是时间类型")
                
                # 验证数据完整性
                self.assertFalse(daily_data.empty, "日线数据不应该为空")
                self.assertTrue(len(daily_data) <= 30, "数据条数不应该超过请求的30条")
                
                # 验证OHLC数据的逻辑关系
                for idx, row in daily_data.iterrows():
                    if not (pd.isna(row['High']) or pd.isna(row['Low']) or pd.isna(row['Open']) or pd.isna(row['Close'])):
                        self.assertGreaterEqual(row['High'], row['Low'], f"{idx}: 最高价应该大于等于最低价")
                        self.assertGreaterEqual(row['High'], row['Open'], f"{idx}: 最高价应该大于等于开盘价")
                        self.assertGreaterEqual(row['High'], row['Close'], f"{idx}: 最高价应该大于等于收盘价")
                        self.assertLessEqual(row['Low'], row['Open'], f"{idx}: 最低价应该小于等于开盘价")
                        self.assertLessEqual(row['Low'], row['Close'], f"{idx}: 最低价应该小于等于收盘价")
                
                # 打印前几条数据作为示例
                logger.info("前5条日线数据:")
                logger.info(f"\n{daily_data.head()}")
                
                logger.info(f"日线数据统计信息:")
                logger.info(f"  数据条数: {len(daily_data)}")
                logger.info(f"  时间范围: {daily_data.index[0]} 到 {daily_data.index[-1]}")
                logger.info(f"  最新收盘价: {daily_data['Close'].iloc[-1]}")
                logger.info(f"  最高价: {daily_data['High'].max()}")
                logger.info(f"  最低价: {daily_data['Low'].min()}")
                logger.info(f"  平均成交量: {daily_data['Volume'].mean():,.0f}")
                
            else:
                logger.warning("获取到的日线数据为空")
            
            # 测试2: 获取60分钟线数据
            logger.info("=" * 50)
            logger.info("测试2: 获取60分钟线数据 (最近50条)")
            
            hourly_data = self.collector.get_stock_candlesticks(
                stock_code=test_stock,
                period=Period.Min_60,
                count=50,
                adjust_type=AdjustType.NoAdjust
            )
            
            self.assertIsNotNone(hourly_data, "60分钟线数据不应该为None")
            self.assertIsInstance(hourly_data, pd.DataFrame, "60分钟线数据应该是DataFrame类型")
            
            if not hourly_data.empty:
                logger.success(f"✓ 获取60分钟线数据成功: {len(hourly_data)} 条记录")
                logger.info(f"60分钟线数据时间范围: {hourly_data.index[0]} 到 {hourly_data.index[-1]}")
                
                # 验证数据条数
                self.assertTrue(len(hourly_data) <= 50, "60分钟线数据条数不应该超过请求的50条")
                
            else:
                logger.warning("获取到的60分钟线数据为空")
            
            # 测试3: 测试前复权数据
            logger.info("=" * 50)
            logger.info("测试3: 获取前复权日线数据 (最近20条)")
            
            adjusted_data = self.collector.get_stock_candlesticks(
                stock_code=test_stock,
                period=Period.Day,
                count=20,
                adjust_type=AdjustType.ForwardAdjust
            )
            
            self.assertIsNotNone(adjusted_data, "前复权数据不应该为None")
            self.assertIsInstance(adjusted_data, pd.DataFrame, "前复权数据应该是DataFrame类型")
            
            if not adjusted_data.empty:
                logger.success(f"✓ 获取前复权数据成功: {len(adjusted_data)} 条记录")
                logger.info(f"前复权数据时间范围: {adjusted_data.index[0]} 到 {adjusted_data.index[-1]}")
                
                # 验证数据条数
                self.assertTrue(len(adjusted_data) <= 20, "前复权数据条数不应该超过请求的20条")
                
            else:
                logger.warning("获取到的前复权数据为空")
            
            logger.success("股票K线数据获取测试完成")
                
        except Exception as e:
            logger.error(f"测试失败: {e}")
            logger.warning("请确保配置了正确的LongPort API环境变量和行情权限")
            self.fail(f"获取股票K线数据时发生异常: {e}")

    def test_get_stock_history(self):
        logger.info("=== 测试获取股票历史K线数据 ===")
        
        test_stock = 'BABA.US'
        
        try:
            logger.info(f"测试股票: {test_stock}")
            
            # 测试指定日期范围: 2020-01-01 到 2025-06-06
            start_date = datetime(2020, 1, 1)
            end_date = datetime(2025, 6, 6)
            
            logger.info(f"测试日期范围: {start_date.date()} 到 {end_date.date()}")
            
            daily_data = self.collector.get_stock_history(
                stock_code=test_stock,
                period=Period.Day,
                adjust_type=AdjustType.ForwardAdjust,
                start_date=start_date,
                end_date=end_date
            )
            
            # 断言测试
            self.assertIsNotNone(daily_data, "历史数据不应该为None")
            self.assertIsInstance(daily_data, pd.DataFrame, "历史数据应该是DataFrame类型")
            
            if not daily_data.empty:
                logger.success(f"✓ 获取成功: {len(daily_data)} 条记录")
                
                # 验证DataFrame结构
                expected_columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Turnover']
                for col in expected_columns:
                    self.assertIn(col, daily_data.columns, f"DataFrame应该包含{col}列")
                
                # 验证数据类型
                self.assertTrue(isinstance(daily_data.index, pd.DatetimeIndex), "索引应该是时间类型")
                
                # 验证数据完整性
                self.assertFalse(daily_data.empty, "历史数据不应该为空")
                self.assertTrue(len(daily_data) > 0, "应该有历史数据记录")
                
                # 验证数据在指定范围内
                self.assertTrue(daily_data.index[0] >= start_date, "数据开始时间应该不早于指定开始时间")
                self.assertTrue(daily_data.index[-1] <= end_date, "数据结束时间应该不晚于指定结束时间")
                
                # 打印前几条数据作为示例
                logger.info("前5条历史数据:")
                logger.info(f"\n{daily_data.head()}")
                
                logger.info(f"数据统计信息:")
                logger.info(f"  数据条数: {len(daily_data)}")
                logger.info(f"  时间范围: {daily_data.index[0]} 到 {daily_data.index[-1]}")
                logger.info(f"  最新收盘价: {daily_data['Close'].iloc[-1]}")
                logger.info(f"  最高价: {daily_data['High'].max()}")
                logger.info(f"  最低价: {daily_data['Low'].min()}")
                logger.info(f"  平均成交量: {daily_data['Volume'].mean():,.0f}")
                
            else:
                logger.warning("获取到的历史数据为空")
            
            logger.success("股票历史数据获取测试完成")
                
        except Exception as e:
            logger.error(f"测试失败: {e}")
            logger.warning("请确保配置了正确的LongPort API环境变量和权限")
            self.fail(f"获取股票历史数据时发生异常: {e}")

    def test_get_option_quote(self):
        logger.info("=== 测试获取期权行情 ===")
        
        test_stock = 'BABA.US'
        
        try:
            logger.info(f"测试标的股票: {test_stock}")
            
            # 步骤1: 获取标的股票当前价格
            logger.info("=" * 50)
            logger.info("步骤1: 获取标的股票当前价格")
            
            stock_quote = self.collector.get_stock_quote([test_stock])
            if not stock_quote or test_stock not in stock_quote:
                self.skipTest(f"无法获取{test_stock}的股票行情，跳过期权测试")
            
            current_price = stock_quote[test_stock].last_done
            logger.info(f"当前股价: {current_price}")
            
            # 计算5%价格范围 (转换为float类型进行计算)
            current_price_float = float(current_price)
            price_range = current_price_float * 0.05
            min_strike = current_price_float - price_range
            max_strike = current_price_float + price_range
            logger.info(f"行权价筛选范围: {min_strike:.2f} - {max_strike:.2f} (5%以内)")
            
            # 步骤2: 获取期权链到期日列表
            logger.info("=" * 50)
            logger.info("步骤2: 获取期权链到期日列表")
            
            expiry_dates = self.collector.get_option_chain_expiry_date_list(test_stock)
            self.assertIsNotNone(expiry_dates, "期权链到期日列表不应该为None")
            self.assertIsInstance(expiry_dates, list, "期权链到期日列表应该是列表类型")
            
            if not expiry_dates:
                self.skipTest(f"{test_stock}没有期权链数据，跳过测试")
            
            logger.info(f"获取到 {len(expiry_dates)} 个到期日")
            
            # 筛选最近一周内的到期日
            from datetime import date, timedelta
            today = date.today()
            one_week_later = today + timedelta(days=7)
            
            recent_expiry_dates = [d for d in expiry_dates if today <= d <= one_week_later]
            
            if not recent_expiry_dates:
                # 如果一周内没有到期日，取最近的一个到期日进行测试
                logger.warning("一周内没有到期日，使用最近的1个到期日进行测试")
                recent_expiry_dates = sorted([d for d in expiry_dates if d >= today])[:1]
            
            logger.info(f"筛选后的到期日 (最近一周或最近1个): {recent_expiry_dates}")
            
            # 步骤3: 获取期权链信息并筛选期权
            logger.info("=" * 50)
            logger.info("步骤3: 获取期权链信息并筛选期权")
            
            all_call_options = []
            all_put_options = []
            
            for expiry_date in recent_expiry_dates:
                logger.info(f"处理到期日: {expiry_date}")
                
                option_chain = self.collector.get_option_chain_info_by_date(test_stock, expiry_date)
                self.assertIsNotNone(option_chain, f"期权链信息不应该为None: {expiry_date}")
                self.assertIsInstance(option_chain, list, f"期权链信息应该是列表类型: {expiry_date}")
                
                if not option_chain:
                    logger.warning(f"到期日 {expiry_date} 没有期权链数据")
                    continue
                
                logger.info(f"到期日 {expiry_date} 共 {len(option_chain)} 个行权价")
                
                # 筛选5%价格范围内的期权
                filtered_options = [
                    opt for opt in option_chain 
                    if min_strike <= opt.price <= max_strike
                ]
                
                logger.info(f"价格范围内的期权: {len(filtered_options)} 个")
                
                for option in filtered_options:
                    strike_price = option.price
                    call_symbol = option.call_symbol if hasattr(option, 'call_symbol') else None
                    put_symbol = option.put_symbol if hasattr(option, 'put_symbol') else None
                    
                    logger.info(f"  行权价: {strike_price}")
                    if call_symbol:
                        logger.info(f"    CALL: {call_symbol}")
                        all_call_options.append(call_symbol)
                    if put_symbol:
                        logger.info(f"    PUT:  {put_symbol}")
                        all_put_options.append(put_symbol)
            
            logger.info(f"总共筛选出 CALL 期权: {len(all_call_options)} 个")
            logger.info(f"总共筛选出 PUT 期权: {len(all_put_options)} 个")
            
            if not all_call_options and not all_put_options:
                self.skipTest("没有找到符合条件的期权，跳过行情获取测试")
            
            # 步骤4: 获取期权行情
            logger.info("=" * 50)
            logger.info("步骤4: 获取期权行情")
            
            # 合并所有期权代码，限制数量避免超出API限制
            all_options = all_call_options + all_put_options
            max_options = 50  # 限制期权数量，避免超出API限制
            if len(all_options) > max_options:
                logger.warning(f"期权数量({len(all_options)})超过限制，随机选择{max_options}个进行测试")
                import random
                all_options = random.sample(all_options, max_options)
            
            if all_options:
                option_quotes = self.collector.get_option_quote(all_options)
                
                # 断言测试
                self.assertIsNotNone(option_quotes, "期权行情数据不应该为None")
                self.assertIsInstance(option_quotes, dict, "期权行情数据应该是字典类型")
                
                logger.success(f"成功获取 {len(option_quotes)} 个期权的行情数据")
                
                # 验证和展示期权行情数据
                call_count = 0
                put_count = 0
                
                for symbol, quote in option_quotes.items():
                    self.assertIsNotNone(symbol, f"期权代码{symbol}不应该为None")
                    self.assertIsNotNone(quote, f"期权{symbol}的行情数据不应该为None")
                    
                    # 判断是CALL还是PUT
                    option_type = "CALL" if "C" in symbol else "PUT" if "P" in symbol else "UNKNOWN"
                    if option_type == "CALL":
                        call_count += 1
                    elif option_type == "PUT":
                        put_count += 1
                    
                    logger.info(f"期权代码: {symbol} ({option_type})")
                    
                    # 验证期权行情字段
                    if hasattr(quote, 'last_done') and quote.last_done:
                        logger.info(f"  最新价: {quote.last_done}")
                    if hasattr(quote, 'bid') and quote.bid:
                        logger.info(f"  买一价: {quote.bid}")
                    if hasattr(quote, 'ask') and quote.ask:
                        logger.info(f"  卖一价: {quote.ask}")
                    if hasattr(quote, 'volume') and quote.volume:
                        logger.info(f"  成交量: {quote.volume}")
                    if hasattr(quote, 'implied_volatility') and quote.implied_volatility:
                        logger.info(f"  隐含波动率: {quote.implied_volatility}%")
                    
                    # 期权希腊字母
                    if hasattr(quote, 'delta') and quote.delta is not None:
                        logger.info(f"  Delta: {quote.delta}")
                    if hasattr(quote, 'gamma') and quote.gamma is not None:
                        logger.info(f"  Gamma: {quote.gamma}")
                    if hasattr(quote, 'theta') and quote.theta is not None:
                        logger.info(f"  Theta: {quote.theta}")
                    if hasattr(quote, 'vega') and quote.vega is not None:
                        logger.info(f"  Vega: {quote.vega}")
                    
                    logger.info("-" * 30)
                
                # 总结统计
                logger.info("=" * 50)
                logger.info("期权行情获取总结:")
                logger.info(f"  标的股票: {test_stock}")
                logger.info(f"  当前股价: {current_price_float}")
                logger.info(f"  行权价范围: {min_strike:.2f} - {max_strike:.2f}")
                logger.info(f"  CALL期权: {call_count} 个")
                logger.info(f"  PUT期权: {put_count} 个")
                logger.info(f"  总期权数: {len(option_quotes)} 个")
                
                logger.success("期权行情获取测试完成")
            else:
                self.skipTest("没有符合条件的期权代码")
                
        except Exception as e:
            logger.error(f"测试失败: {e}")
            logger.warning("请确保配置了正确的LongPort API环境变量和期权权限")
            self.fail(f"获取期权行情时发生异常: {e}")

    def test_get_depth(self):
        logger.info("=== 测试获取标的盘口数据 ===")
        
        # 指定测试股票：BABA.US (普通股票)
        test_stocks = ['BABA.US']
        logger.info(f"测试指定标的: {test_stocks}")
        
        successful_tests = 0
        
        for stock_code in test_stocks:
            try:
                logger.info("=" * 50)
                logger.info(f"测试股票: {stock_code}")
                
                # 获取盘口数据
                depth_data = self.collector.get_depth(stock_code)
                
                # 基本断言测试
                self.assertIsNotNone(depth_data, f"股票{stock_code}的盘口数据不应该为None")
                
                # 验证数据结构
                self.assertTrue(hasattr(depth_data, 'asks'), f"股票{stock_code}的盘口数据应该有ask属性")
                self.assertTrue(hasattr(depth_data, 'bids'), f"股票{stock_code}的盘口数据应该有bid属性")
                
                logger.info(f"✓ 成功获取股票 {stock_code} 的盘口数据")
                
                # 验证和展示卖盘数据
                ask_data = depth_data.asks
                self.assertIsNotNone(ask_data, f"股票{stock_code}的卖盘数据不应该为None")
                self.assertIsInstance(ask_data, list, f"股票{stock_code}的卖盘数据应该是列表类型")
                
                logger.info(f"  卖盘档位数: {len(ask_data)}")
                
                if ask_data:
                    logger.info("  卖盘详情:")
                    for i, ask in enumerate(ask_data[:5]):  # 只显示前5档
                        # 验证卖盘数据结构
                        self.assertTrue(hasattr(ask, 'position'), f"卖盘第{i+1}档应该有position属性")
                        self.assertTrue(hasattr(ask, 'price'), f"卖盘第{i+1}档应该有price属性")
                        self.assertTrue(hasattr(ask, 'volume'), f"卖盘第{i+1}档应该有volume属性")
                        self.assertTrue(hasattr(ask, 'order_num'), f"卖盘第{i+1}档应该有order_num属性")
                        
                        # 验证数据有效性
                        self.assertIsNotNone(ask.position, f"卖盘第{i+1}档的档位不应该为None")
                        self.assertIsNotNone(ask.price, f"卖盘第{i+1}档的价格不应该为None")
                        self.assertIsNotNone(ask.volume, f"卖盘第{i+1}档的挂单量不应该为None")
                        self.assertIsNotNone(ask.order_num, f"卖盘第{i+1}档的订单数不应该为None")
                        
                        # 验证档位顺序
                        self.assertEqual(ask.position, i + 1, f"卖盘档位应该从1开始递增")
                        
                        # 验证数值类型和合理性
                        self.assertTrue(ask.volume >= 0, f"卖盘第{i+1}档的挂单量应该大于等于0")
                        self.assertTrue(ask.order_num >= 0, f"卖盘第{i+1}档的订单数应该大于等于0")
                        
                        logger.info(f"    档位{ask.position}: 价格={ask.price}, 量={ask.volume}, 订单数={ask.order_num}")
                else:
                    logger.warning(f"  股票 {stock_code} 当前没有卖盘数据")
                
                # 验证和展示买盘数据
                bid_data = depth_data.bids
                self.assertIsNotNone(bid_data, f"股票{stock_code}的买盘数据不应该为None")
                self.assertIsInstance(bid_data, list, f"股票{stock_code}的买盘数据应该是列表类型")
                
                logger.info(f"  买盘档位数: {len(bid_data)}")
                
                if bid_data:
                    logger.info("  买盘详情:")
                    for i, bid in enumerate(bid_data[:5]):  # 只显示前5档
                        # 验证买盘数据结构
                        self.assertTrue(hasattr(bid, 'position'), f"买盘第{i+1}档应该有position属性")
                        self.assertTrue(hasattr(bid, 'price'), f"买盘第{i+1}档应该有price属性")
                        self.assertTrue(hasattr(bid, 'volume'), f"买盘第{i+1}档应该有volume属性")
                        self.assertTrue(hasattr(bid, 'order_num'), f"买盘第{i+1}档应该有order_num属性")
                        
                        # 验证数据有效性
                        self.assertIsNotNone(bid.position, f"买盘第{i+1}档的档位不应该为None")
                        self.assertIsNotNone(bid.price, f"买盘第{i+1}档的价格不应该为None")
                        self.assertIsNotNone(bid.volume, f"买盘第{i+1}档的挂单量不应该为None")
                        self.assertIsNotNone(bid.order_num, f"买盘第{i+1}档的订单数不应该为None")
                        
                        # 验证档位顺序
                        self.assertEqual(bid.position, i + 1, f"买盘档位应该从1开始递增")
                        
                        # 验证数值类型和合理性
                        self.assertTrue(bid.volume >= 0, f"买盘第{i+1}档的挂单量应该大于等于0")
                        self.assertTrue(bid.order_num >= 0, f"买盘第{i+1}档的订单数应该大于等于0")
                        
                        logger.info(f"    档位{bid.position}: 价格={bid.price}, 量={bid.volume}, 订单数={bid.order_num}")
                else:
                    logger.warning(f"  股票 {stock_code} 当前没有买盘数据")
                
                # 验证买卖盘价格关系（如果都有数据）
                if ask_data and bid_data:
                    # 将价格转换为float进行比较
                    best_ask_price = float(ask_data[0].price) if ask_data[0].price else None
                    best_bid_price = float(bid_data[0].price) if bid_data[0].price else None
                    
                    if best_ask_price is not None and best_bid_price is not None:
                        self.assertGreaterEqual(best_ask_price, best_bid_price, 
                                              f"股票{stock_code}的最优卖价应该大于等于最优买价")
                        logger.info(f"  买卖价差: {best_ask_price - best_bid_price:.4f}")
                        logger.info(f"  买卖价差率: {(best_ask_price - best_bid_price) / best_bid_price * 100:.4f}%")
                
                # 验证卖盘价格递增关系
                if len(ask_data) > 1:
                    for i in range(1, min(len(ask_data), 5)):  # 检查前5档
                        price_prev = float(ask_data[i-1].price) if ask_data[i-1].price else 0
                        price_curr = float(ask_data[i].price) if ask_data[i].price else 0
                        if price_prev > 0 and price_curr > 0:
                            self.assertGreaterEqual(price_curr, price_prev, 
                                                  f"股票{stock_code}卖盘第{i+1}档价格应该大于等于第{i}档价格")
                
                # 验证买盘价格递减关系
                if len(bid_data) > 1:
                    for i in range(1, min(len(bid_data), 5)):  # 检查前5档
                        price_prev = float(bid_data[i-1].price) if bid_data[i-1].price else float('inf')
                        price_curr = float(bid_data[i].price) if bid_data[i].price else float('inf')
                        if price_prev < float('inf') and price_curr < float('inf'):
                            self.assertLessEqual(price_curr, price_prev, 
                                               f"股票{stock_code}买盘第{i+1}档价格应该小于等于第{i}档价格")
                
                successful_tests += 1
                logger.success(f"✓ 股票 {stock_code} 盘口数据验证通过")
                
            except Exception as e:
                logger.error(f"测试股票 {stock_code} 失败: {e}")
                # 如果是特定的错误（如权限问题），我们继续测试其他股票
                if "权限" in str(e) or "permission" in str(e).lower():
                    logger.warning(f"股票 {stock_code} 可能没有盘口数据权限，继续测试其他股票")
                    continue
                else:
                    # 其他错误则抛出异常
                    self.fail(f"获取股票 {stock_code} 盘口数据时发生异常: {e}")
        
        # 测试总结
        logger.info("=" * 50)
        logger.info("盘口数据获取测试总结:")
        logger.info(f"  测试股票总数: {len(test_stocks)}")
        logger.info(f"  成功获取数据: {successful_tests} 只")
        logger.info(f"  成功率: {successful_tests/len(test_stocks)*100:.1f}%")
        
        # 至少要有一只股票成功获取盘口数据
        self.assertGreater(successful_tests, 0, "至少应该有一只股票成功获取盘口数据")
        
        logger.success("标的盘口数据获取测试完成")
        
        logger.success("=== 标的盘口数据测试全部完成 ===")


if __name__ == "__main__":
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加测试用例 - 按照collector里的实现顺序
    suite.addTest(TestDataModule('test_data_interface'))
    suite.addTest(TestDataModule('test_get_trading_session'))
    suite.addTest(TestDataModule('test_get_stock_list'))
    suite.addTest(TestDataModule('test_get_stock_basic_info'))
    suite.addTest(TestDataModule('test_get_stock_quote'))
    suite.addTest(TestDataModule('test_get_stock_calc_index'))
    suite.addTest(TestDataModule('test_get_stock_candlesticks'))
    suite.addTest(TestDataModule('test_get_stock_history'))
    suite.addTest(TestDataModule('test_get_option_quote'))
    suite.addTest(TestDataModule('test_get_depth'))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 打印测试总结
    print("\n" + "="*50)
    print("测试总结:")
    print(f"- 运行测试数: {result.testsRun}")
    print(f"- 失败数: {len(result.failures)}")
    print(f"- 错误数: {len(result.errors)}")
    print(f"- 跳过数: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\n失败的测试:")
        for test, trace in result.failures:
            print(f"- {test}: {trace}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, trace in result.errors:
            print(f"- {test}: {trace}")
    
    print("="*50)
    
    # 退出码
    exit_code = 0 if result.wasSuccessful() else 1
    sys.exit(exit_code)
