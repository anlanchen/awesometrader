from loguru import logger
from datetime import date, datetime
from typing import Optional, List, Any
from decimal import Decimal
from longport.openapi import (
    TradeContext,
    Config,
    OrderType,
    OrderSide,
    TimeInForceType,
    OutsideRTH,
    OrderDetail,
    OrderStatus,
    Market,
    BalanceType
)

class LongPortTradeAPI:
    def __init__(self):
        """初始化LongPortTradeAPI类"""
        config = Config.from_env()
        self.trade_ctx = TradeContext(config)

    def get_account_balance(self, currency: Optional[str] = None) -> List[Any]:
        """
        获取账户资金信息
        
        Args:
            currency: 可选，指定币种筛选（HKD、USD、CNH）
            
        Returns:
            List[Any]: 账户资金列表，包含现金总额、可用现金、冻结现金等信息
        """
        try:
            logger.info(f"开始获取账户资金信息，币种筛选: {currency if currency else '全部'}")
            
            # 调用LongPort API获取账户余额
            resp = self.trade_ctx.account_balance(currency=currency)
            logger.info(f"成功获取账户资金信息，共{len(resp)}个账户")
            
            # 打印账户信息摘要
            for account in resp:
                logger.info(f"币种: {account.currency}, 总现金: {account.total_cash}, 净资产: {account.net_assets}")
            
            return resp
            
        except Exception as e:
            logger.error(f"获取账户资金信息失败: {str(e)}")
            return []
        
    def get_stock_positions(self, symbols: Optional[List[str]] = None) -> List[Any]:
        """
        获取股票持仓信息
        
        Args:
            symbols: 可选，股票代码列表，使用 ticker.region 格式，例如：["AAPL.US", "700.HK"]
                    如果不指定，则返回所有持仓股票
            
        Returns:
            List[Any]: 账户持仓列表，每个账户包含account_channel和positions信息
        """
        try:
            logger.info(f"开始获取股票持仓信息，筛选股票: {symbols if symbols else '全部'}")
            
            # 调用LongPort API获取股票持仓
            resp = self.trade_ctx.stock_positions(symbols=symbols)
            logger.info(f"成功获取股票持仓信息")
            
            # 打印持仓摘要
            if resp and resp.channels:
                for account in resp.channels:
                    account_type = account.account_channel
                    stock_count = len(account.positions) if account.positions else 0
                    logger.info(f"账户类型: {account_type}, 持仓股票数量: {stock_count}")
                    
                    # 打印每只股票的持仓详情
                    if account.positions:
                        for stock in account.positions:
                            logger.info(f"  {stock.symbol} ({stock.symbol_name}): "
                                      f"持仓{stock.quantity}股, 可用{stock.available_quantity}股, "
                                      f"成本价{stock.cost_price} {stock.currency}")
            else:
                logger.info("当前无股票持仓")
            
            # 返回账户持仓列表
            return resp.channels if resp and resp.channels else []
            
        except Exception as e:
            logger.error(f"获取股票持仓信息失败: {str(e)}")
            return []

    def get_cash_flow(self,
                     start_at: datetime,
                     end_at: datetime,
                     business_type: Optional[BalanceType] = None,
                     symbol: Optional[str] = None,
                     page: Optional[int] = None,
                     size: Optional[int] = None) -> List[Any]:
        """
        获取资金流水信息

        Args:
            start_at: 开始时间
            end_at: 结束时间
            business_type: 可选，资金类别，BalanceType.Cash-现金，BalanceType.Stock-股票，BalanceType.Fund-基金
            symbol: 可选，股票代码，使用 ticker.region 格式，例如：AAPL.US
            page: 可选，起始页，默认1，最小值1
            size: 可选，每页数量，默认50，范围1-10000

        Returns:
            List[Any]: 资金流水列表，包含交易流水名称、方向、金额、币种、时间等信息
        """
        try:
            logger.info(f"开始获取资金流水信息，时间范围: {start_at} 至 {end_at}")
            if business_type:
                logger.info(f"资金类别筛选: {business_type}")
            if symbol:
                logger.info(f"股票代码筛选: {symbol}")

            # 调用LongPort API获取资金流水
            resp = self.trade_ctx.cash_flow(
                start_at=start_at,
                end_at=end_at,
                business_type=business_type,
                symbol=symbol,
                page=page,
                size=size
            )

            # 返回的是CashFlow对象，包含list字段
            cash_flows = resp.list if resp and hasattr(resp, 'list') else []
            logger.info(f"成功获取资金流水信息，共{len(cash_flows)}条记录")

            # 打印资金流水摘要
            if cash_flows:
                inflow_count = sum(1 for flow in cash_flows if hasattr(flow, 'direction') and flow.direction == 2)
                outflow_count = sum(1 for flow in cash_flows if hasattr(flow, 'direction') and flow.direction == 1)
                logger.info(f"资金流入: {inflow_count}条, 资金流出: {outflow_count}条")

            return cash_flows

        except Exception as e:
            logger.error(f"获取资金流水信息失败: {str(e)}")
            return []

    def submit_order(self,
                    symbol: str,
                    order_type: OrderType,
                    side: OrderSide,
                    submitted_quantity: Decimal,
                    time_in_force: TimeInForceType,
                    submitted_price: Optional[Decimal] = None,
                    trigger_price: Optional[Decimal] = None,
                    limit_offset: Optional[Decimal] = None,
                    trailing_amount: Optional[Decimal] = None,
                    trailing_percent: Optional[Decimal] = None,
                    expire_date: Optional[date] = None,
                    outside_rth: Optional[OutsideRTH] = None,
                    remark: Optional[str] = None) -> str:
        """
        委托下单
        
        Args:
            symbol: 股票代码，使用 ticker.region 格式，例如：AAPL.US
            order_type: 订单类型
            side: 买卖方向
            submitted_quantity: 下单数量
            time_in_force: 订单有效期类型
            submitted_price: 下单价格，LO / ELO / ALO / ODD / LIT 订单必填
            trigger_price: 触发价格，LIT / MIT 订单必填
            limit_offset: 指定价差，TSLPAMT / TSLPPCT 订单必填
            trailing_amount: 跟踪金额，TSLPAMT 订单必填
            trailing_percent: 跟踪涨跌幅，TSLPPCT 订单必填
            expire_date: 长期单过期时间，time_in_force 为 GTD 时必填
            outside_rth: 是否允许盘前盘后
            remark: 备注（最大64字符）
            
        Returns:
            str: 订单ID
        """
        try:
            logger.info(f"开始提交订单: {symbol} {side} {submitted_quantity}股 {order_type}")
            
            # 调用LongPort API提交订单
            resp = self.trade_ctx.submit_order(
                symbol=symbol,
                order_type=order_type,
                side=side,
                submitted_quantity=submitted_quantity,
                time_in_force=time_in_force,
                submitted_price=submitted_price,
                trigger_price=trigger_price,
                limit_offset=limit_offset,
                trailing_amount=trailing_amount,
                trailing_percent=trailing_percent,
                expire_date=expire_date,
                outside_rth=outside_rth,
                remark=remark
            )
            
            logger.info(f"订单提交成功，订单ID: {resp.order_id}")
            return resp.order_id
            
        except Exception as e:
            logger.error(f"提交订单失败: {str(e)}")
            raise
    
    def cancel_order(self, order_id: str) -> None:
        """
        取消订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            None: 取消成功时不返回值，失败时抛出异常
        """
        try:
            logger.info(f"开始取消订单: {order_id}")
            
            # 调用LongPort API取消订单
            self.trade_ctx.cancel_order(order_id=order_id)
            logger.info(f"订单取消成功，订单ID: {order_id}")
            
        except Exception as e:
            logger.error(f"取消订单失败: {str(e)}")
            raise
            
    def replace_order(self,
                     order_id: str,
                     quantity: Decimal,
                     price: Optional[Decimal] = None,
                     trigger_price: Optional[Decimal] = None,
                     limit_offset: Optional[Decimal] = None,
                     trailing_amount: Optional[Decimal] = None,
                     trailing_percent: Optional[Decimal] = None,
                     remark: Optional[str] = None) -> None:
        """
        修改订单
        
        Args:
            order_id: 订单ID
            quantity: 改单数量，例如：200
            price: 改单价格，例如：388.5 LO / ELO / ALO / ODD / LIT 订单必填
            trigger_price: 触发价格，例如：388.5 LIT / MIT 订单必填
            limit_offset: 指定价差 TSLPAMT / TSLPPCT 订单必填
            trailing_amount: 跟踪金额 TSLPAMT 订单必填
            trailing_percent: 跟踪涨跌幅 TSLPPCT 订单必填
            remark: 备注（最大64字符）
        """
        try:
            logger.info(f"开始修改订单: {order_id}, 数量: {quantity}")
            if price is not None:
                logger.info(f"修改价格为: {price}")
            
            # 调用LongPort API修改订单
            self.trade_ctx.replace_order(
                order_id=order_id,
                quantity=quantity,
                price=price,
                trigger_price=trigger_price,
                limit_offset=limit_offset,
                trailing_amount=trailing_amount,
                trailing_percent=trailing_percent,
                remark=remark
            )
            
            logger.info(f"订单修改成功，订单ID: {order_id}")
            
        except Exception as e:
            logger.error(f"修改订单失败: {str(e)}")
            raise

    def get_order_detail(self, order_id: str) -> OrderDetail:
        """
        获取订单详情
        
        Args:
            order_id: 订单ID，例如：701276261045858304
            
        Returns:
            OrderDetail: 订单详情对象，包含订单状态、成交信息、费用明细等
            
        Raises:
            Exception: 当订单ID不存在或其他API错误时抛出异常
        """
        try:
            logger.info(f"开始获取订单详情: {order_id}")
            
            # 调用LongPort API获取订单详情
            resp = self.trade_ctx.order_detail(order_id=order_id)
            logger.info(f"订单详情获取成功，订单ID: {order_id}, 状态: {resp.status}")
            return resp
            
        except Exception as e:
            logger.error(f"获取订单详情失败: {str(e)}")
            raise

    def get_today_orders(self,
                        symbol: Optional[str] = None,
                        status: Optional[List[OrderStatus]] = None,
                        side: Optional[OrderSide] = None,
                        market: Optional[Market] = None,
                        order_id: Optional[str] = None) -> List[Any]:
        """
        获取当日订单
        
        Args:
            symbol: 可选，股票代码，使用 ticker.region 格式，例如：AAPL.US
            status: 可选，订单状态列表，例如：[OrderStatus.Filled, OrderStatus.New]
            side: 可选，买卖方向，Buy-买入，Sell-卖出
            market: 可选，市场，US-美股，HK-港股
            order_id: 可选，订单ID，用于指定订单ID查询
            
        Returns:
            List[Any]: 当日订单列表，每个订单包含订单ID、状态、股票名称、数量、价格等信息
        """
        try:
            logger.info("开始获取当日订单")
            
            # 调用LongPort API获取当日订单
            resp = self.trade_ctx.today_orders(
                symbol=symbol,
                status=status,
                side=side,
                market=market,
                order_id=order_id
            )
            return resp
            
        except Exception as e:
            logger.error(f"获取当日订单失败: {str(e)}")
            raise

