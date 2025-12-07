import sys
sys.path.append('.')

from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from datetime import datetime
import talib
from longport.openapi import Period
from awesometrader import DataInterface

class SMA_CROSS(Strategy):
    n1 = 18
    n2 = 32

    def init(self):
        price = self.data.Close
        self.ma1 = self.I(talib.SMA, price, self.n1)
        self.ma2 = self.I(talib.SMA, price, self.n2)

    def next(self):
        if crossover(self.ma1, self.ma2):
            self.buy()
        elif crossover(self.ma2, self.ma1):
            self.position.close()

data_interface = DataInterface()
data = data_interface.get_stock_data("PDD.US", Period.Week, start_date=datetime(2018, 1, 1), end_date=datetime(2025, 6, 15))
backtest = Backtest(data, SMA_CROSS, commission=.002, exclusive_orders=True)

stats, heatmap = backtest.optimize(
    n1=range(5, 30, 1),
    n2=range(10, 100, 2),
    constraint=lambda p: p.n1 < p.n2,
    maximize='Equity Final [$]',
    max_tries=10000,
    random_state=0,
    return_heatmap=True)

print(stats)
print(heatmap.sort_values().iloc[-5:])
hm = heatmap.groupby(['n1', 'n2']).mean().unstack()
hm = hm[::-1]
hm.to_csv('strategies/results/sma_cross_heatmap.csv')


# stats = backtest.run()
# backtest.plot()
# print(stats)

# stats['_trades'].to_csv('strategies/results/sma_cross_trades.csv', index=False)
# stats['_equity_curve'].to_csv('strategies/results/sma_cross_equity_curve.csv', index=False)