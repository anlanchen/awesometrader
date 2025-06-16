import pandas as pd
from typing import List, Dict, Type
from loguru import logger
from datetime import datetime
from longport.openapi import Period, AdjustType, TradeSessions, CalcIndex
from longport.openapi import QuoteContext, Config, MarketTradingSession, SecurityStaticInfo, SecurityQuote, SecurityCalcIndex

class Collector:
    def __init__(self):
        """初始化Collector类"""
        config = Config.from_env()
        self.quote_ctx = QuoteContext(config)

    def get_trading_session(self) -> List[MarketTradingSession]:
        """
        获取各市场当日交易时段
        根据LongPort API文档: https://open.longportapp.com/zh-CN/docs/quote/pull/trade-session
        
        :return: MarketTradingSession对象，包含各市场的交易时段信息
        """
        try:
            logger.info("正在获取各市场当日交易时段")
            
            # 调用LongPort API获取交易时段信息
            response = self.quote_ctx.trading_session()
            
            logger.success(f"成功获取交易时段信息")
            
            # 打印各市场的交易时段信息
            for market_session in response:
                logger.info(f"市场: {market_session.market}")
                for session in market_session.trade_sessions:
                    logger.info(f"  交易时段: {session.begin_time} - {session.end_time} ({session.trade_session})")
        
            return response
            
        except Exception as e:
            logger.error(f"获取交易时段信息失败: {e}")
            raise e

    def get_stock_basic_info(self, stock_code_list: List[str]) -> Dict[str, SecurityStaticInfo]:
        """
        获取股票基础信息
        根据LongPort API文档: https://open.longportapp.com/zh-CN/docs/quote/pull/static
        
        :param stock_code_list: 股票代码列表，使用 ticker.region 格式，例如：['700.HK', 'AAPL.US']
        :return: 包含股票基础信息的列表
        """
        if not stock_code_list:
            logger.warning("股票代码列表为空")
            return {}
        
        try:
            logger.info(f"正在获取{len(stock_code_list)}只股票的基础信息")
            
            # 调用LongPort API获取股票基础信息
            response = self.quote_ctx.static_info(stock_code_list)
            
            stock_info_dict = {}
            # response是一个包含SecurityStaticInfo对象的列表
            for stock_info in response:
                stock_info_dict[stock_info.symbol] = stock_info
            
            logger.success(f"成功获取{len(stock_info_dict)}只股票的基础信息")
            return stock_info_dict
            
        except Exception as e:
            logger.error(f"获取股票基础信息失败: {e}")
            return {}

    def get_stock_quote(self, stock_code_list: List[str]) -> Dict[str, SecurityQuote]:
        """
        获取股票实时行情
        根据LongPort API文档: https://open.longportapp.com/zh-CN/docs/quote/pull/quote
        
        :param stock_code_list: 股票代码列表，使用 ticker.region 格式，例如：['700.HK', 'AAPL.US', 'TSLA.US']
        :return: 包含股票实时行情信息的字典，键为股票代码，值为行情数据字典
        """
        if not stock_code_list:
            logger.warning("股票代码列表为空")
            return {}
        
        try:
            logger.info(f"正在获取{len(stock_code_list)}只股票的实时行情")
            
            # 调用LongPort API获取股票实时行情
            response = self.quote_ctx.quote(stock_code_list)
            
            quote_dict = {}
            # response是一个包含SecurityQuote对象的列表
            for quote in response:
                quote_dict[quote.symbol] = quote
            
            logger.success(f"成功获取{len(quote_dict)}只股票的实时行情")
            return quote_dict
            
        except Exception as e:
            logger.error(f"获取股票实时行情失败: {e}")
            return {}
    
    def get_stock_calc_index(self, stock_code_list: List[str], calc_index_list: List[Type[CalcIndex]] = None) -> Dict[str, SecurityCalcIndex]:
        """
        获取股票计算指标数据
        根据LongPort API文档: https://open.longportapp.com/zh-CN/docs/quote/pull/calc-index
        
        :param stock_code_list: 股票代码列表，使用 ticker.region 格式，例如：['700.HK', 'AAPL.US']
        :param calc_index_list: 计算指标列表，例如：[CalcIndex.LastDone, CalcIndex.ChangeRate]，如果为None则获取常用指标
        :return: 包含股票计算指标信息的字典，键为股票代码，值为SecurityCalcIndex对象
        """
        if not stock_code_list:
            logger.warning("股票代码列表为空")
            return {}
        
        try:
            logger.info(f"正在获取{len(stock_code_list)}只股票的计算指标")
            
            # 如果没有指定计算指标，使用默认的全部指标
            if calc_index_list is None:
                calc_index_list = [
                    CalcIndex.LastDone,               # 1. 最新价
                    CalcIndex.ChangeValue,            # 2. 涨跌额  
                    CalcIndex.ChangeRate,             # 3. 涨跌幅
                    CalcIndex.Volume,                 # 4. 成交量
                    CalcIndex.Turnover,               # 5. 成交额
                    CalcIndex.YtdChangeRate,          # 6. 年初至今涨幅
                    CalcIndex.TurnoverRate,           # 7. 换手率
                    CalcIndex.TotalMarketValue,       # 8. 总市值
                    CalcIndex.CapitalFlow,            # 9. 资金流向
                    CalcIndex.Amplitude,              # 10. 振幅
                    CalcIndex.VolumeRatio,            # 11. 量比
                    CalcIndex.PeTtmRatio,             # 12. 市盈率(TTM)
                    CalcIndex.PbRatio,                # 13. 市净率
                    CalcIndex.DividendRatioTtm,       # 14. 股息率(TTM)
                    CalcIndex.FiveDayChangeRate,      # 15. 五日涨幅
                    CalcIndex.TenDayChangeRate,       # 16. 十日涨幅
                    CalcIndex.HalfYearChangeRate,     # 17. 半年涨幅
                    CalcIndex.FiveMinutesChangeRate,  # 18. 五分钟涨幅
                ]
                logger.info("未指定计算指标，将获取默认的全部18个指标")
            else:
                logger.info(f"指定计算指标: {calc_index_list}")
            
            # 调用LongPort API获取股票计算指标
            response = self.quote_ctx.calc_indexes(stock_code_list, calc_index_list)
            
            calc_index_dict = {}
            # response是一个包含SecurityCalcIndex对象的列表
            for calc_index in response:
                calc_index_dict[calc_index.symbol] = calc_index
            
            logger.success(f"成功获取{len(calc_index_dict)}只股票的计算指标")
            return calc_index_dict
            
        except Exception as e:
            logger.error(f"获取股票计算指标失败: {e}")
            return {}

    def get_stock_candlesticks(self, stock_code: str, period: Period, count: int, adjust_type: AdjustType) -> pd.DataFrame:
        """
        获取股票K线数据
        根据LongPort API文档: https://open.longportapp.com/zh-CN/docs/quote/pull/candlestick
        
        :param stock_code: 股票代码，使用 ticker.region 格式，例如：'700.HK'
        :param period: K线周期，使用Period枚举，例如：Period.Day, Period.Min_5等
        :param count: 数据数量，最大为1000
        :param adjust_type: 复权类型，使用AdjustType枚举，例如：AdjustType.NoAdjust
        :return: K线数据DataFrame，包含Open, High, Low, Close, Volume, Turnover列
        """
        try:
            logger.info(f"正在获取股票K线数据: {stock_code}, period={period}, count={count}, adjust_type={adjust_type}")
            
            # 验证参数
            if count <= 0 or count > 1000:
                raise ValueError("count参数必须在1-1000之间")
            
            # 调用LongPort API获取K线数据
            response = self.quote_ctx.candlesticks(
                symbol=stock_code,
                period=period,
                count=count,
                adjust_type=adjust_type,
                trade_sessions=TradeSessions.All
            )
            
            if len(response) == 0:
                logger.warning(f"未获取到股票 {stock_code} 的K线数据")
                return pd.DataFrame()
            
            # 转换为DataFrame
            data_list = []
            for candle in response:
                data_list.append({
                        'timestamp': candle.timestamp,
                        'Open': candle.open,
                        'High': candle.high,
                        'Low': candle.low,
                        'Close': candle.close,
                        'Volume': candle.volume,
                        'Turnover': candle.turnover
                    })
            
            # 创建DataFrame
            df = pd.DataFrame(data_list)
            
            if df.empty:
                logger.warning(f"转换后的DataFrame为空: {stock_code}")
                return pd.DataFrame()
            
            # 设置时间戳为索引并排序
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            logger.success(f"成功获取股票 {stock_code} K线数据: {len(df)} 条记录")
            if len(df) > 0:
                logger.info(f"数据时间范围: {df.index[0]} 到 {df.index[-1]}")
            
            return df
            
        except Exception as e:
            logger.error(f"获取股票K线数据失败 {stock_code}: {e}")
            return pd.DataFrame()

    def get_stock_history(self, stock_code: str, period: Period, adjust_type: AdjustType, 
                         start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        获取股票历史K线数据
        根据LongPort API文档: https://open.longportapp.com/zh-CN/docs/quote/pull/history-candlestick
        
        :param stock_code: 股票代码，使用 ticker.region 格式，例如：'700.HK'
        :param period: K线周期，使用Period枚举，例如：Period.Day, Period.Min_5等
        :param adjust_type: 复权类型，使用AdjustType枚举，例如：AdjustType.NoAdjust
        :param start_date: 开始日期，必填
        :param end_date: 结束日期，必填
        :return: 历史数据DataFrame，包含Open, High, Low, Close, Volume, Turnover列
        """
        try:
            logger.info(f"正在获取股票历史数据: {stock_code}, period={period}, adjust_type={adjust_type}")
            logger.info(f"日期范围: {start_date.date()} 到 {end_date.date()}")
            
            # 存储所有分片的数据
            all_data_frames = []
            current_end_date = end_date
            
            while True:
                # 调用API获取历史数据
                response = self.quote_ctx.history_candlesticks_by_date(
                    symbol=stock_code,
                    period=period,
                    adjust_type=adjust_type,
                    start=start_date.date(),
                    end=current_end_date.date(),
                    trade_sessions=TradeSessions.All
                )

                num_candles = len(response)
                if num_candles== 0:
                    break
                
                # 转换为DataFrame
                data_list = []
                for candle in response:
                    data_list.append({
                        'timestamp': candle.timestamp,
                        'Open': candle.open,
                        'High': candle.high,
                        'Low': candle.low,
                        'Close': candle.close,
                        'Volume': candle.volume,
                        'Turnover': candle.turnover
                    })
                
                # 创建DataFrame
                df_chunk = pd.DataFrame(data_list)
                df_chunk.set_index('timestamp', inplace=True)
                df_chunk.sort_index(inplace=True)
                all_data_frames.append(df_chunk)

                logger.info(f"获取数据块: {len(df_chunk)} 条记录，时间范围: {df_chunk.index[0]} 到 {df_chunk.index[-1]}")
                
                # 如果已经覆盖了请求的开始时间，说明已经获取完毕
                earliest_timestamp = df_chunk.index[0]
                if earliest_timestamp <= start_date or earliest_timestamp >= current_end_date:
                    logger.info(f"已到达请求的开始时间，停止继续请求")
                    break
                
                # 更新下次请求的结束时间为当前数据块的最早时间
                current_end_date = earliest_timestamp
                logger.info(f"需要继续获取更早的数据，下次请求截止时间: {current_end_date}")
            
            # 合并所有数据块
            if not all_data_frames:
                logger.warning(f"未获取到任何股票 {stock_code} 的历史数据")
                return pd.DataFrame()
            
            # 合并所有DataFrame
            final_df = pd.concat(all_data_frames, axis=0)
            
            # 去重并排序（按时间戳去重，保留最后一条记录）
            final_df = final_df[~final_df.index.duplicated(keep='last')]
            final_df.sort_index(inplace=True)
            
            # 最终过滤确保在指定的时间范围内
            final_df = final_df[(final_df.index >= start_date) & (final_df.index <= end_date)]
            
            logger.success(f"成功获取股票 {stock_code} 历史数据: {len(final_df)} 条记录")
            if len(final_df) > 0:
                logger.info(f"最终数据时间范围: {final_df.index[0]} 到 {final_df.index[-1]}")
            else:
                logger.warning(f"最终合并后的数据为空")
            
            return final_df
            
        except Exception as e:
            logger.error(f"获取股票历史数据失败 {stock_code}: {e}")
            return pd.DataFrame()

        
