import sys
sys.path.append('.')

import numpy as np
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from longport.openapi import Period
from awesometrader import DataInterface

class Test(Strategy):
    # 可优化参数
    macd_fast = 12
    macd_slow = 26
    macd_signal = 9
    boll_period = 20
    boll_std = 2
    mfi_period = 14
    atr_period = 14

    def init(self):
        self.volume = self.data.Volume.astype(float)
        self.volume_ma = self.I(talib.SMA, self.volume, 14)
        self.macd, self.macd_signal, self.macd_hist = self.I(talib.MACD, self.data.Close, self.macd_fast, self.macd_slow, self.macd_signal)
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(talib.BBANDS, self.data.Close, self.boll_period, self.boll_std, self.boll_std)
        self.mfi = self.I(talib.MFI, self.data.High, self.data.Low, self.data.Close, self.volume, self.mfi_period)
        self.atr = self.I(talib.ATR, self. data.High, self.data.Low, self.data.Close, self.atr_period)

    def next(self):
        # 如果没有持仓，检查入场条件
        if self.position.size > 0:
            # 明确空头信号
            short_cond1 = self.macd > 3 and self.macd_signal > 3 and self.macd_hist[-1] < -1 # MACD高位死叉
            # short_cond2 = self.mfi[-1] > 80  # MFI显示资金超买
            short_cond3 = self.data.Close[-1] < self.bb_middle[-1] - self.atr[-1]  # 价格下穿中轨 并跌破ATR
            if short_cond1 or short_cond3:
                self.position.close()
        else:
            # 明确多头信号
            long_cond1 = self.macd < 0 and self.macd_signal < 0 and self.macd_hist[-1] > 0 # MACD低位金叉
            long_cond2 = self.data.Close[-1] > self.bb_middle[-1] # 价格上穿中轨
            if long_cond1 or long_cond2:
                self.buy()
        
        # if self.volume[-1] > self.volume_ma[-2] * 2:  # 成交量大涨，可能是反转的信号
        #     long_cond1 = self.macd_hist[-1] < -1
        #     long_cond2 = self.mfi[-1] < 40
        #     if long_cond1 and long_cond2:
        #         if self.position.size < 0.5:
        #             self.buy(0.5)

        #     short_cond1 = self.macd_hist[-1] > 1
        #     short_cond2 = self.mfi[-1] > 60
        #     if short_cond1 and short_cond2:
        #         if self.position.size > 0.5:
        #             self.sell(0.5)

data_interface = DataInterface()
AAPL = data_interface.get_stock_data("AAPL.US", Period.Day)
bt = Backtest(AAPL, Test, commission=.002, exclusive_orders=True)
stats = bt.run()
bt.plot()

print(stats)
# 输出所有订单
stats['_trades'].to_csv('backtest_trades.csv', index=False)
stats['_equity_curve'].to_csv('backtest_equity_curve.csv', index=False)