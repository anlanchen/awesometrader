import sys
sys.path.append('.')

from datetime import datetime
import multiprocessing
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from longport.openapi import Period
from awesometrader import DataInterface

class MACD(Strategy):
    fastperiod = 12
    slowperiod = 38
    signalperiod = 10

    def init(self):
        self.macd, self.macd_signal, self.macd_hist = self.I(talib.MACD, self.data.Close, self.fastperiod, self.slowperiod, self.signalperiod)

    def next(self):
        if crossover(self.macd, self.macd_signal):
            self.buy()
        elif crossover(self.macd_signal, self.macd):
            self.position.close()

if __name__ == '__main__':
    data_interface = DataInterface()
    data = data_interface.get_stock_data("PDD.US", Period.Week, start_date=datetime(2018, 1, 1), end_date=datetime(2025, 1, 1))
    backtest = Backtest(data, MACD, commission=.002)
    backtest.Pool = multiprocessing.Pool

    stats, heatmap = backtest.optimize(
        fastperiod=range(5, 15, 1),
        slowperiod=range(20, 200, 5),
        signalperiod=range(5, 20, 1),
        constraint=lambda p: p.fastperiod < p.slowperiod,
        maximize='Equity Final [$]',
        max_tries=10000,
        random_state=0,
        return_heatmap=True)

    print(stats)
    print(heatmap.sort_values().iloc[-10:])
    # hm = heatmap.groupby(['n']).mean().unstack()
    # hm = hm[::-1]
    # hm.to_csv('strategies/results/macd_heatmap.csv')

    # stats = backtest.run()
    # print(stats)
    
    # 输出所有订单
    # stats['_trades'].to_csv('strategies/results/macd_trades.csv', index=False)
    # stats['_equity_curve'].to_csv('strategies/results/macd_equity_curve.csv', index=False)