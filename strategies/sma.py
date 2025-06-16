import sys
sys.path.append('.')

from backtesting import Backtest, Strategy
from backtesting.lib import crossover

import talib
from longport.openapi import Period
from awesometrader import DataInterface

class SmaCross(Strategy):
    def init(self):
        price = self.data.Close
        self.ma1 = self.I(talib.SMA, price, 10)
        self.ma2 = self.I(talib.SMA, price, 20)

    def next(self):
        if crossover(self.ma1, self.ma2):
            self.buy()
        elif crossover(self.ma2, self.ma1):
            self.sell()

data_interface = DataInterface()
AAPL = data_interface.get_stock_data("AAPL.US", Period.Day)
bt = Backtest(AAPL, SmaCross, commission=.002, exclusive_orders=True)
stats = bt.run()
bt.plot()

print(stats)