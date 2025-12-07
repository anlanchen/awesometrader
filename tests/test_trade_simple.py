"""
测试LongPortTradeAPI类的交易相关功能
"""

import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from loguru import logger
from awesometrader import LongPortTradeAPI
from longport.openapi import OrderType, OrderSide, TimeInForceType, OrderStatus, Market, BalanceType

class TestTradeModule(unittest.TestCase):
    def setUp(self):
        """每个测试方法之前运行"""
        # 初始化交易接口
        self.trader = LongPortTradeAPI()
        
    def tearDown(self):
        """每个测试方法之后运行"""
        # 清理资源
        pass
    
    def test_get_account_balance(self):
        logger.info("=== 测试获取账户资金信息 ===")
        
        try:
            # 测试1: 获取所有币种的账户资金
            logger.info("=" * 50)
            logger.info("测试1: 获取所有币种的账户资金")
            
            all_balances = self.trader.get_account_balance()
            
            # 断言测试
            self.assertIsNotNone(all_balances, "账户资金信息不应该为None")
            self.assertIsInstance(all_balances, list, "账户资金信息应该是列表类型")
            self.assertTrue(len(all_balances) > 0, "应该至少有一个账户的资金信息")
            
            logger.info(f"✓ 成功获取{len(all_balances)}个账户的资金信息")
            
            # 验证账户资金数据结构
            for i, account_balance in enumerate(all_balances):
                logger.info(f"账户 {i+1}:")
                
                # 验证必要的属性
                self.assertTrue(hasattr(account_balance, 'currency'), f"第{i+1}个账户应该有currency属性")
                self.assertTrue(hasattr(account_balance, 'total_cash'), f"第{i+1}个账户应该有total_cash属性")
                self.assertTrue(hasattr(account_balance, 'buy_power'), f"第{i+1}个账户应该有buy_power属性")
                self.assertTrue(hasattr(account_balance, 'net_assets'), f"第{i+1}个账户应该有net_assets属性")
                self.assertTrue(hasattr(account_balance, 'cash_infos'), f"第{i+1}个账户应该有cash_infos属性")
                
                # 验证数据类型
                self.assertIsInstance(account_balance.currency, str, f"第{i+1}个账户的currency应该是字符串")
                self.assertIsInstance(account_balance.total_cash, Decimal, f"第{i+1}个账户的total_cash应该是Decimal类型")
                self.assertIsInstance(account_balance.buy_power, Decimal, f"第{i+1}个账户的buy_power应该是Decimal类型")
                self.assertIsInstance(account_balance.net_assets, Decimal, f"第{i+1}个账户的net_assets应该是Decimal类型")
                self.assertIsInstance(account_balance.cash_infos, list, f"第{i+1}个账户的cash_infos应该是列表")
                
                # 基础信息
                logger.info(f"  币种: {account_balance.currency}")
                logger.info(f"  总现金: {account_balance.total_cash}")
                logger.info(f"  购买力: {account_balance.buy_power}")
                logger.info(f"  净资产: {account_balance.net_assets}")
                
                # 风控信息
                if hasattr(account_balance, 'risk_level'):
                    risk_level_desc = {
                        0: "安全",
                        1: "中风险", 
                        2: "预警",
                        3: "危险"
                    }
                    risk_desc = risk_level_desc.get(account_balance.risk_level, f"未知({account_balance.risk_level})")
                    logger.info(f"  风控等级: {risk_desc}")
                
                # 融资信息
                if hasattr(account_balance, 'max_finance_amount'):
                    logger.info(f"  最大融资金额: {account_balance.max_finance_amount}")
                if hasattr(account_balance, 'remaining_finance_amount'):
                    logger.info(f"  剩余融资金额: {account_balance.remaining_finance_amount}")
                if hasattr(account_balance, 'margin_call'):
                    logger.info(f"  追缴保证金: {account_balance.margin_call}")
                
                # 保证金信息
                if hasattr(account_balance, 'init_margin'):
                    logger.info(f"  初始保证金: {account_balance.init_margin}")
                if hasattr(account_balance, 'maintenance_margin'):
                    logger.info(f"  维持保证金: {account_balance.maintenance_margin}")
                
                # 现金详情
                logger.info(f"  现金详情 ({len(account_balance.cash_infos)} 种币种):")
                for j, cash_info in enumerate(account_balance.cash_infos):
                    # 验证现金信息结构
                    self.assertTrue(hasattr(cash_info, 'currency'), f"第{j+1}个现金信息应该有currency属性")
                    self.assertTrue(hasattr(cash_info, 'available_cash'), f"第{j+1}个现金信息应该有available_cash属性")
                    self.assertTrue(hasattr(cash_info, 'withdraw_cash'), f"第{j+1}个现金信息应该有withdraw_cash属性")
                    self.assertTrue(hasattr(cash_info, 'frozen_cash'), f"第{j+1}个现金信息应该有frozen_cash属性")
                    self.assertTrue(hasattr(cash_info, 'settling_cash'), f"第{j+1}个现金信息应该有settling_cash属性")
                    
                    # 验证数据类型
                    self.assertIsInstance(cash_info.currency, str, f"第{j+1}个现金信息的currency应该是字符串")
                    self.assertIsInstance(cash_info.available_cash, Decimal, f"第{j+1}个现金信息的available_cash应该是Decimal类型")
                    self.assertIsInstance(cash_info.withdraw_cash, Decimal, f"第{j+1}个现金信息的withdraw_cash应该是Decimal类型")
                    self.assertIsInstance(cash_info.frozen_cash, Decimal, f"第{j+1}个现金信息的frozen_cash应该是Decimal类型")
                    self.assertIsInstance(cash_info.settling_cash, Decimal, f"第{j+1}个现金信息的settling_cash应该是Decimal类型")
                    
                    logger.info(f"    {cash_info.currency}:")
                    logger.info(f"      可用现金: {cash_info.available_cash}")
                    logger.info(f"      可提现金: {cash_info.withdraw_cash}")
                    logger.info(f"      冻结现金: {cash_info.frozen_cash}")
                    logger.info(f"      待结算现金: {cash_info.settling_cash}")
                
                # 冻结费用信息（如果有）
                if hasattr(account_balance, 'frozen_transaction_fees') and account_balance.frozen_transaction_fees:
                    logger.info(f"  冻结费用 ({len(account_balance.frozen_transaction_fees)} 项):")
                    for k, fee_info in enumerate(account_balance.frozen_transaction_fees):
                        if hasattr(fee_info, 'currency') and hasattr(fee_info, 'frozen_transaction_fee'):
                            logger.info(f"    {fee_info.currency}: {fee_info.frozen_transaction_fee}")
                
                logger.info("-" * 30)
            
            # 测试2: 获取指定币种的账户资金 (HKD)
            logger.info("=" * 50)
            logger.info("测试2: 获取港币(HKD)账户资金")
            
            hkd_balances = self.trader.get_account_balance(currency="HKD")
            
            self.assertIsNotNone(hkd_balances, "HKD账户资金信息不应该为None")
            self.assertIsInstance(hkd_balances, list, "HKD账户资金信息应该是列表类型")
            
            if len(hkd_balances) > 0:
                logger.info(f"✓ 成功获取{len(hkd_balances)}个HKD账户的资金信息")
                
                # 验证所有返回的账户都是HKD币种
                for account_balance in hkd_balances:
                    self.assertEqual(account_balance.currency, "HKD", "筛选的账户币种应该是HKD")
                
                # 显示HKD账户详情
                for i, account_balance in enumerate(hkd_balances):
                    logger.info(f"HKD账户 {i+1}:")
                    logger.info(f"  总现金: {account_balance.total_cash} HKD")
                    logger.info(f"  购买力: {account_balance.buy_power} HKD")
                    logger.info(f"  净资产: {account_balance.net_assets} HKD")
            else:
                logger.info("未找到HKD账户资金信息")
            
            # 测试3: 获取指定币种的账户资金 (USD)
            logger.info("=" * 50)
            logger.info("测试3: 获取美元(USD)账户资金")
            
            usd_balances = self.trader.get_account_balance(currency="USD")
            
            self.assertIsNotNone(usd_balances, "USD账户资金信息不应该为None")
            self.assertIsInstance(usd_balances, list, "USD账户资金信息应该是列表类型")
            
            if len(usd_balances) > 0:
                logger.info(f"✓ 成功获取{len(usd_balances)}个USD账户的资金信息")
                
                # 验证所有返回的账户都是USD币种
                for account_balance in usd_balances:
                    self.assertEqual(account_balance.currency, "USD", "筛选的账户币种应该是USD")
                
                # 显示USD账户详情
                for i, account_balance in enumerate(usd_balances):
                    logger.info(f"USD账户 {i+1}:")
                    logger.info(f"  总现金: {account_balance.total_cash} USD")
                    logger.info(f"  购买力: {account_balance.buy_power} USD")
                    logger.info(f"  净资产: {account_balance.net_assets} USD")
            else:
                logger.info("未找到USD账户资金信息")
            
            # 测试4: 获取指定币种的账户资金 (CNH)
            logger.info("=" * 50)
            logger.info("测试4: 获取人民币(CNH)账户资金")
            
            cnh_balances = self.trader.get_account_balance(currency="CNH")
            
            self.assertIsNotNone(cnh_balances, "CNH账户资金信息不应该为None")
            self.assertIsInstance(cnh_balances, list, "CNH账户资金信息应该是列表类型")
            
            if len(cnh_balances) > 0:
                logger.info(f"✓ 成功获取{len(cnh_balances)}个CNH账户的资金信息")
                
                # 验证所有返回的账户都是CNH币种
                for account_balance in cnh_balances:
                    self.assertEqual(account_balance.currency, "CNH", "筛选的账户币种应该是CNH")
                
                # 显示CNH账户详情
                for i, account_balance in enumerate(cnh_balances):
                    logger.info(f"CNH账户 {i+1}:")
                    logger.info(f"  总现金: {account_balance.total_cash} CNH")
                    logger.info(f"  购买力: {account_balance.buy_power} CNH")
                    logger.info(f"  净资产: {account_balance.net_assets} CNH")
            else:
                logger.info("未找到CNH账户资金信息")
            
            # 汇总测试结果
            logger.info("=" * 50)
            logger.info("账户资金汇总:")
            
            # 统计不同币种的账户数量
            currency_stats = {}
            total_net_assets = {}
            
            for account_balance in all_balances:
                currency = account_balance.currency
                currency_stats[currency] = currency_stats.get(currency, 0) + 1
                
                # 累计净资产
                if currency not in total_net_assets:
                    total_net_assets[currency] = Decimal('0')
                total_net_assets[currency] += account_balance.net_assets
            
            logger.info("币种分布:")
            for currency, count in currency_stats.items():
                logger.info(f"  {currency}: {count} 个账户")
            
            logger.info("各币种净资产总计:")
            for currency, net_assets in total_net_assets.items():
                logger.info(f"  {currency}: {net_assets}")
            
            logger.success("=== 账户资金信息获取测试完成 ===")
            
        except Exception as e:
            logger.error(f"测试失败: {e}")
            logger.warning("请确保配置了正确的LongPort API环境变量和交易权限")
            self.fail(f"获取账户资金信息时发生异常: {e}")

    def test_get_stock_positions(self):
        logger.info("=== 测试获取股票持仓信息 ===")
        
        try:
            # 测试1: 获取所有股票持仓
            logger.info("=" * 50)
            logger.info("测试1: 获取所有股票持仓")
            
            all_positions = self.trader.get_stock_positions()
            
            # 断言测试
            self.assertIsNotNone(all_positions, "股票持仓信息不应该为None")
            self.assertIsInstance(all_positions, list, "股票持仓信息应该是列表类型")
            
            if len(all_positions) > 0:
                logger.info(f"✓ 成功获取股票持仓信息，共{len(all_positions)}个账户")
                
                # 验证持仓数据结构
                for i, account_position in enumerate(all_positions):
                    logger.info(f"账户 {i+1}:")
                    
                    # 验证必要的属性
                    self.assertTrue(hasattr(account_position, 'account_channel'), f"第{i+1}个账户应该有account_channel属性")
                    self.assertTrue(hasattr(account_position, 'positions'), f"第{i+1}个账户应该有positions属性")
                    
                    # 验证数据类型
                    self.assertIsInstance(account_position.account_channel, str, f"第{i+1}个账户的account_channel应该是字符串")
                    self.assertIsInstance(account_position.positions, list, f"第{i+1}个账户的positions应该是列表")
                    
                    account_type = account_position.account_channel
                    stock_count = len(account_position.positions)
                    
                    logger.info(f"  账户类型: {account_type}")
                    logger.info(f"  持仓股票数量: {stock_count}")
                    
                    # 验证股票持仓详情
                    if account_position.positions:
                        logger.info(f"  持仓详情:")
                        
                        for j, stock_info in enumerate(account_position.positions):
                            # 验证股票信息结构
                            self.assertTrue(hasattr(stock_info, 'symbol'), f"第{j+1}只股票应该有symbol属性")
                            self.assertTrue(hasattr(stock_info, 'symbol_name'), f"第{j+1}只股票应该有symbol_name属性")
                            self.assertTrue(hasattr(stock_info, 'quantity'), f"第{j+1}只股票应该有quantity属性")
                            self.assertTrue(hasattr(stock_info, 'available_quantity'), f"第{j+1}只股票应该有available_quantity属性")
                            self.assertTrue(hasattr(stock_info, 'currency'), f"第{j+1}只股票应该有currency属性")
                            self.assertTrue(hasattr(stock_info, 'cost_price'), f"第{j+1}只股票应该有cost_price属性")
                            self.assertTrue(hasattr(stock_info, 'market'), f"第{j+1}只股票应该有market属性")
                            
                            # 验证数据类型
                            self.assertIsInstance(stock_info.symbol, str, f"第{j+1}只股票的symbol应该是字符串")
                            self.assertIsInstance(stock_info.symbol_name, str, f"第{j+1}只股票的symbol_name应该是字符串")
                            self.assertIsInstance(stock_info.quantity, Decimal, f"第{j+1}只股票的quantity应该是Decimal类型")
                            self.assertIsInstance(stock_info.available_quantity, Decimal, f"第{j+1}只股票的available_quantity应该是Decimal类型")
                            self.assertIsInstance(stock_info.currency, str, f"第{j+1}只股票的currency应该是字符串")
                            self.assertIsInstance(stock_info.cost_price, Decimal, f"第{j+1}只股票的cost_price应该是Decimal类型")
                            # market 是 Market 枚举类型，在实际使用中通常表现为字符串或对象
                            
                            logger.info(f"    {j+1}. {stock_info.symbol} ({stock_info.symbol_name})")
                            logger.info(f"       市场: {str(stock_info.market)}")
                            logger.info(f"       持仓数量: {stock_info.quantity}")
                            logger.info(f"       可用数量: {stock_info.available_quantity}")
                            logger.info(f"       币种: {stock_info.currency}")
                            logger.info(f"       成本价格: {stock_info.cost_price} {stock_info.currency}")
                            
                            # 初始持仓数量（可能不存在）
                            if hasattr(stock_info, 'init_quantity') and stock_info.init_quantity is not None:
                                self.assertIsInstance(stock_info.init_quantity, Decimal, f"第{j+1}只股票的init_quantity应该是Decimal类型")
                                logger.info(f"       开盘前初始持仓: {stock_info.init_quantity}")
                    else:
                        logger.info("  当前账户无股票持仓")
                    
                    logger.info("-" * 30)
            else:
                logger.info("当前无股票持仓")
            
            # 测试2: 获取指定股票的持仓（如果有持仓的话）
            logger.info("=" * 50)
            logger.info("测试2: 获取指定股票的持仓")
            
            # 先从全部持仓中找一些股票代码用于测试
            test_symbols = []
            if all_positions:
                for account_position in all_positions:
                    if account_position.positions:
                        for stock_info in account_position.positions[:2]:  # 最多取前2只股票
                            if stock_info.symbol not in test_symbols:
                                test_symbols.append(stock_info.symbol)
            
            if test_symbols:
                logger.info(f"测试股票代码: {test_symbols}")
                
                specific_positions = self.trader.get_stock_positions(symbols=test_symbols)
                
                self.assertIsNotNone(specific_positions, "指定股票持仓信息不应该为None")
                self.assertIsInstance(specific_positions, list, "指定股票持仓信息应该是列表类型")
                
                if len(specific_positions) > 0:
                    logger.info(f"✓ 成功获取指定股票的持仓信息")
                    
                    # 验证返回的股票是否在指定列表中
                    for account_position in specific_positions:
                        if account_position.positions:
                            for stock_info in account_position.positions:
                                self.assertIn(stock_info.symbol, test_symbols, 
                                            f"返回的股票{stock_info.symbol}应该在指定列表中")
                                logger.info(f"  ✓ {stock_info.symbol} ({stock_info.symbol_name}): "
                                          f"持仓{stock_info.quantity}股")
                else:
                    logger.info("指定的股票当前无持仓")
            else:
                logger.info("无法获取测试用的股票代码，跳过指定股票测试")
            
            # 测试3: 测试不存在的股票代码
            logger.info("=" * 50)
            logger.info("测试3: 获取不存在的股票持仓")
            
            non_exist_positions = self.trader.get_stock_positions(symbols=["TEST.XX"])
            
            self.assertIsNotNone(non_exist_positions, "不存在股票的持仓信息不应该为None")
            self.assertIsInstance(non_exist_positions, list, "不存在股票的持仓信息应该是列表类型")
            
            # 验证返回结果应该是空的或者没有相关股票
            has_test_stock = False
            if non_exist_positions:
                for account_position in non_exist_positions:
                    if account_position.positions:
                        for stock_info in account_position.positions:
                            if stock_info.symbol == "TEST.XX":
                                has_test_stock = True
                                break
            
            self.assertFalse(has_test_stock, "不应该找到不存在的股票TEST.XX")
            logger.info("✓ 正确处理了不存在的股票代码")
            
            # 汇总测试结果
            logger.info("=" * 50)
            logger.info("股票持仓汇总:")
            
            if all_positions:
                # 统计持仓信息
                total_stocks = 0
                market_stats = {}
                currency_stats = {}
                
                for account_position in all_positions:
                    if account_position.positions:
                        for stock_info in account_position.positions:
                            total_stocks += 1
                            
                            # 统计市场分布 (Market是枚举类型，转换为字符串)
                            market = str(stock_info.market)
                            market_stats[market] = market_stats.get(market, 0) + 1
                            
                            # 统计币种分布
                            currency = stock_info.currency
                            currency_stats[currency] = currency_stats.get(currency, 0) + 1
                
                logger.info(f"总持仓股票数: {total_stocks}")
                
                logger.info("市场分布:")
                for market, count in market_stats.items():
                    logger.info(f"  {market}: {count} 只股票")
                
                logger.info("币种分布:")
                for currency, count in currency_stats.items():
                    logger.info(f"  {currency}: {count} 只股票")
            else:
                logger.info("当前无股票持仓")
            
            logger.success("=== 股票持仓信息获取测试完成 ===")
            
        except Exception as e:
            logger.error(f"测试失败: {e}")
            logger.warning("请确保配置了正确的LongPort API环境变量和交易权限")
            self.fail(f"获取股票持仓信息时发生异常: {e}")

    def test_get_cash_flow(self):
        logger.info("=== 测试获取资金流水信息 ===")

        try:
            # 测试1: 获取最近7天的资金流水
            logger.info("=" * 50)
            logger.info("测试1: 获取最近7天的资金流水")

            end_time = datetime.now()
            start_time = end_time - timedelta(days=7)

            logger.info(f"查询时间范围: {start_time.strftime('%Y-%m-%d %H:%M:%S')} 至 {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

            cash_flows = self.trader.get_cash_flow(
                start_at=start_time,
                end_at=end_time
            )

            # 断言测试
            self.assertIsNotNone(cash_flows, "资金流水信息不应该为None")
            self.assertIsInstance(cash_flows, list, "资金流水信息应该是列表类型")

            if len(cash_flows) > 0:
                logger.info(f"✓ 成功获取资金流水信息，共{len(cash_flows)}条记录")

                # 验证资金流水数据结构
                for i, flow in enumerate(cash_flows[:5]):  # 只验证前5条
                    logger.info(f"流水记录 {i+1}:")

                    # 验证必要的属性
                    self.assertTrue(hasattr(flow, 'transaction_flow_name'), f"第{i+1}条流水应该有transaction_flow_name属性")
                    self.assertTrue(hasattr(flow, 'direction'), f"第{i+1}条流水应该有direction属性")
                    self.assertTrue(hasattr(flow, 'business_type'), f"第{i+1}条流水应该有business_type属性")
                    self.assertTrue(hasattr(flow, 'balance'), f"第{i+1}条流水应该有balance属性")
                    self.assertTrue(hasattr(flow, 'currency'), f"第{i+1}条流水应该有currency属性")
                    self.assertTrue(hasattr(flow, 'business_time'), f"第{i+1}条流水应该有business_time属性")

                    # 验证数据类型
                    self.assertIsInstance(flow.transaction_flow_name, str, f"第{i+1}条流水的transaction_flow_name应该是字符串")
                    self.assertIsInstance(flow.direction, int, f"第{i+1}条流水的direction应该是整数")
                    self.assertIsInstance(flow.business_type, int, f"第{i+1}条流水的business_type应该是整数")
                    self.assertIsInstance(flow.balance, Decimal, f"第{i+1}条流水的balance应该是Decimal类型")
                    self.assertIsInstance(flow.currency, str, f"第{i+1}条流水的currency应该是字符串")
                    self.assertIsInstance(flow.business_time, int, f"第{i+1}条流水的business_time应该是整数")

                    # 基础信息
                    direction_desc = "流入" if flow.direction == 2 else "流出"
                    business_type_desc = {1: "现金", 2: "股票", 3: "基金"}.get(flow.business_type, f"未知({flow.business_type})")

                    logger.info(f"  流水名称: {flow.transaction_flow_name}")
                    logger.info(f"  方向: {direction_desc} ({flow.direction})")
                    logger.info(f"  资金类别: {business_type_desc}")
                    logger.info(f"  金额: {flow.balance} {flow.currency}")
                    logger.info(f"  时间: {datetime.fromtimestamp(flow.business_time).strftime('%Y-%m-%d %H:%M:%S')}")

                    # 可选字段
                    if hasattr(flow, 'symbol') and flow.symbol:
                        logger.info(f"  关联股票: {flow.symbol}")
                    if hasattr(flow, 'description') and flow.description:
                        logger.info(f"  说明: {flow.description}")

                    logger.info("-" * 30)

                if len(cash_flows) > 5:
                    logger.info(f"... 还有 {len(cash_flows) - 5} 条流水记录")
            else:
                logger.info("最近7天无资金流水记录")

            # 测试2: 获取指定类别的资金流水（现金类）
            logger.info("=" * 50)
            logger.info("测试2: 获取现金类资金流水")

            cash_flows_cash = self.trader.get_cash_flow(
                start_at=start_time,
                end_at=end_time,
                business_type=BalanceType.Cash  # 现金类型
            )

            self.assertIsNotNone(cash_flows_cash, "现金类资金流水信息不应该为None")
            self.assertIsInstance(cash_flows_cash, list, "现金类资金流水信息应该是列表类型")

            if len(cash_flows_cash) > 0:
                logger.info(f"✓ 成功获取现金类资金流水，共{len(cash_flows_cash)}条记录")

                # 验证所有返回的流水都是现金类
                for flow in cash_flows_cash:
                    self.assertEqual(flow.business_type, 1, "筛选的资金流水类别应该是现金")

                # 显示前3条现金流水详情
                for i, flow in enumerate(cash_flows_cash[:3]):
                    direction_desc = "流入" if flow.direction == 2 else "流出"
                    logger.info(f"{i+1}. {flow.transaction_flow_name}: {flow.balance} {flow.currency} ({direction_desc})")
            else:
                logger.info("无现金类资金流水记录")

            # 测试3: 测试分页功能
            logger.info("=" * 50)
            logger.info("测试3: 测试分页功能（每页最多10条）")

            cash_flows_page1 = self.trader.get_cash_flow(
                start_at=start_time,
                end_at=end_time,
                page=1,
                size=10
            )

            self.assertIsNotNone(cash_flows_page1, "分页查询结果不应该为None")
            self.assertIsInstance(cash_flows_page1, list, "分页查询结果应该是列表类型")

            if len(cash_flows_page1) > 0:
                logger.info(f"✓ 第1页返回{len(cash_flows_page1)}条记录")
                self.assertLessEqual(len(cash_flows_page1), 10, "每页记录数应该不超过10条")
            else:
                logger.info("第1页无记录")

            # 汇总测试结果
            logger.info("=" * 50)
            logger.info("资金流水汇总:")

            if cash_flows:
                # 统计流水信息
                inflow_count = sum(1 for flow in cash_flows if flow.direction == 2)
                outflow_count = sum(1 for flow in cash_flows if flow.direction == 1)

                logger.info(f"总流水记录数: {len(cash_flows)}")
                logger.info(f"资金流入记录: {inflow_count} 条")
                logger.info(f"资金流出记录: {outflow_count} 条")

                # 统计币种分布
                currency_stats = {}
                for flow in cash_flows:
                    currency = flow.currency
                    currency_stats[currency] = currency_stats.get(currency, 0) + 1

                logger.info("币种分布:")
                for currency, count in currency_stats.items():
                    logger.info(f"  {currency}: {count} 条流水")

                # 统计资金类别分布
                business_type_stats = {}
                business_type_desc = {1: "现金", 2: "股票", 3: "基金"}
                for flow in cash_flows:
                    business_type = business_type_desc.get(flow.business_type, f"其他({flow.business_type})")
                    business_type_stats[business_type] = business_type_stats.get(business_type, 0) + 1

                logger.info("资金类别分布:")
                for business_type, count in business_type_stats.items():
                    logger.info(f"  {business_type}: {count} 条流水")
            else:
                logger.info("查询时间范围内无资金流水记录")

            logger.success("=== 资金流水信息获取测试完成 ===")

        except Exception as e:
            logger.error(f"测试失败: {e}")
            logger.warning("请确保配置了正确的LongPort API环境变量和交易权限")
            self.fail(f"获取资金流水信息时发生异常: {e}")

    def test_order_operations(self):
        """测试订单操作的完整生命周期"""
        logger.info("=== 测试订单操作生命周期 ===")
        
        # 测试用的股票代码和订单参数（使用一个不太可能成交的价格）
        test_symbol = "BABA.US"  # 阿里巴巴美股
        test_quantity = Decimal('100')  # 100股
        test_price = Decimal('1.00')  # 设置一个很低的价格，不太可能成交
        modified_quantity = Decimal('200')  # 修改后的数量
        modified_price = Decimal('2.00')  # 修改后的价格
        
        order_id = None
        
        try:
            # 第1步：提交订单
            logger.info("=" * 50)
            logger.info("第1步: 提交测试订单")
            logger.info(f"股票: {test_symbol}")
            logger.info(f"方向: 买入")
            logger.info(f"数量: {test_quantity}股")
            logger.info(f"价格: {test_price} USD")
            
            order_id = self.trader.submit_order(
                symbol=test_symbol,
                order_type=OrderType.LO,  # 限价单
                side=OrderSide.Buy,  # 买入
                submitted_quantity=test_quantity,
                time_in_force=TimeInForceType.Day,  # 当日有效
                submitted_price=test_price,
                remark="测试订单 - 请勿执行"
            )
            
            self.assertIsNotNone(order_id, "订单ID不应该为None")
            self.assertIsInstance(order_id, str, "订单ID应该是字符串类型")
            self.assertTrue(len(order_id) > 0, "订单ID不应该为空")
            
            logger.info(f"✓ 订单提交成功，订单ID: {order_id}")
            
            # 第2步：获取订单详情
            logger.info("=" * 50)
            logger.info("第2步: 获取订单详情")
            
            order_detail = self.trader.get_order_detail(order_id)
            
            self.assertIsNotNone(order_detail, "订单详情不应该为None")
            self.assertEqual(order_detail.order_id, order_id, "订单ID应该匹配")
            self.assertEqual(order_detail.symbol, test_symbol, "股票代码应该匹配")
            self.assertEqual(order_detail.side, OrderSide.Buy, "买卖方向应该匹配")
            self.assertEqual(order_detail.quantity, test_quantity, "订单数量应该匹配")
            self.assertEqual(Decimal(order_detail.price), test_price, "订单价格应该匹配")
            
            logger.info(f"✓ 订单详情获取成功")
            logger.info(f"  订单ID: {order_detail.order_id}")
            logger.info(f"  股票: {order_detail.symbol} ({order_detail.stock_name})")
            logger.info(f"  状态: {order_detail.status}")
            logger.info(f"  方向: {order_detail.side}")
            logger.info(f"  数量: {order_detail.quantity}")
            logger.info(f"  价格: {order_detail.price}")
            logger.info(f"  订单类型: {order_detail.order_type}")
            logger.info(f"  提交时间: {order_detail.submitted_at}")
            
            # 第3步：获取当日订单（应该包含刚才提交的订单）
            logger.info("=" * 50)
            logger.info("第3步: 获取当日订单")
            
            # 获取所有当日订单
            all_today_orders = self.trader.get_today_orders()
            self.assertIsNotNone(all_today_orders, "当日订单列表不应该为None")
            self.assertIsInstance(all_today_orders, list, "当日订单应该是列表类型")
            
            # 验证我们的订单在列表中
            found_order = False
            for order in all_today_orders:
                if order.order_id == order_id:
                    found_order = True
                    logger.info(f"✓ 在当日订单中找到测试订单: {order.order_id}")
                    break
            
            self.assertTrue(found_order, "应该在当日订单中找到刚提交的订单")
            
            # 测试按股票代码筛选
            symbol_orders = self.trader.get_today_orders(symbol=test_symbol)
            self.assertIsNotNone(symbol_orders, "按股票筛选的订单列表不应该为None")
            
            found_in_symbol_orders = False
            for order in symbol_orders:
                if order.order_id == order_id:
                    found_in_symbol_orders = True
                    break
            
            self.assertTrue(found_in_symbol_orders, "应该在按股票筛选的订单中找到测试订单")
            logger.info(f"✓ 按股票代码筛选测试通过")
            
            # 测试按订单ID筛选
            id_orders = self.trader.get_today_orders(order_id=order_id)
            self.assertIsNotNone(id_orders, "按订单ID筛选的结果不应该为None")
            self.assertTrue(len(id_orders) > 0, "按订单ID筛选应该有结果")
            self.assertEqual(id_orders[0].order_id, order_id, "筛选结果的订单ID应该匹配")
            
            logger.info(f"✓ 按订单ID筛选测试通过")
            
            # 第4步：修改订单
            logger.info("=" * 50)
            logger.info("第4步: 修改订单")
            logger.info(f"将数量从 {test_quantity} 修改为 {modified_quantity}")
            logger.info(f"将价格从 {test_price} 修改为 {modified_price}")
            
            self.trader.replace_order(
                order_id=order_id,
                quantity=modified_quantity,
                price=modified_price,
                remark="修改后的测试订单"
            )
            
            logger.info(f"✓ 订单修改成功")
            
            # 验证修改结果
            import time
            time.sleep(1)  # 等待1秒让修改生效
            
            modified_order_detail = self.trader.get_order_detail(order_id)
            
            # 注意：修改订单后，数量和价格可能会更新
            logger.info(f"修改后的订单详情:")
            logger.info(f"  数量: {modified_order_detail.quantity}")
            logger.info(f"  价格: {modified_order_detail.price}")
            logger.info(f"  状态: {modified_order_detail.status}")
            
            # 第5步：取消订单
            logger.info("=" * 50)
            logger.info("第5步: 取消订单")
            
            self.trader.cancel_order(order_id)
            logger.info(f"✓ 订单取消成功，订单ID: {order_id}")
            
            # 验证取消结果
            time.sleep(1)  # 等待1秒让取消生效
            
            cancelled_order_detail = self.trader.get_order_detail(order_id)
            logger.info(f"取消后的订单状态: {cancelled_order_detail.status}")
            
            # 测试总结
            logger.info("=" * 50)
            logger.info("订单操作测试总结:")
            logger.info(f"✓ 订单提交: 成功 (ID: {order_id})")
            logger.info(f"✓ 订单详情获取: 成功")
            logger.info(f"✓ 当日订单查询: 成功")
            logger.info(f"✓ 订单修改: 成功")
            logger.info(f"✓ 订单取消: 成功")
            
            logger.success("=== 订单操作生命周期测试完成 ===")
            
        except Exception as e:
            logger.error(f"订单操作测试失败: {e}")
            
            # 如果出现异常且订单已创建，尝试取消订单
            if order_id:
                try:
                    logger.warning(f"尝试清理测试订单: {order_id}")
                    self.trader.cancel_order(order_id)
                    logger.info(f"✓ 测试订单已清理: {order_id}")
                except Exception as cleanup_e:
                    logger.error(f"清理测试订单失败: {cleanup_e}")
            
            logger.warning("请确保配置了正确的LongPort API环境变量和交易权限")
            logger.warning("注意：此测试涉及真实的订单操作，请在模拟环境中进行")
            self.fail(f"订单操作测试时发生异常: {e}")


if __name__ == "__main__":
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加测试用例
    suite.addTest(TestTradeModule('test_get_account_balance'))
    suite.addTest(TestTradeModule('test_get_stock_positions'))
    suite.addTest(TestTradeModule('test_get_cash_flow'))
    suite.addTest(TestTradeModule('test_order_operations'))
    
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
