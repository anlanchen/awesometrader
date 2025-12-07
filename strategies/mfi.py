import sys
sys.path.append('.')

from datetime import datetime
import multiprocessing
import talib
from backtesting import Backtest, Strategy
from longport.openapi import Period
from awesometrader import DataInterface

class MFI(Strategy):
    period = 14

    def init(self):
        self.mfi = self.I(talib.MFI, self.data.High, self.data.Low, self.data.Close, self.data.Volume.astype(float), self.period)

    def next(self):
        if not self.position and self.mfi[-1] < 20:
            self.buy()
        elif self.position and self.mfi[-1] > 80:
            self.position.close()

if __name__ == '__main__':
    data_interface = DataInterface()
    data = data_interface.get_stock_data("PDD.US", Period.Week, start_date=datetime(2018, 1, 1), end_date=datetime(2025, 1, 1))
    backtest = Backtest(data, MFI, commission=.002)
    backtest.Pool = multiprocessing.Pool

    stats, heatmap = backtest.optimize(
        period=range(2, 20, 1),
        maximize='Equity Final [$]',
        max_tries=10000,
        random_state=0,
        return_heatmap=True)

    print(stats)
    print(heatmap.sort_values().iloc[-10:])
    # hm = heatmap.groupby(['n']).mean().unstack()
    # hm = hm[::-1]
    # hm.to_csv('strategies/results/mfi_heatmap.csv')

    # stats = backtest.run()
    # print(stats)
    
    # 输出所有订单
    # stats['_trades'].to_csv('strategies/results/mfi_trades.csv', index=False)
    # stats['_equity_curve'].to_csv('strategies/results/mfi_equity_curve.csv', index=False)