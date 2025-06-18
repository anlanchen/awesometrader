import sys
sys.path.append('.')

import numpy as np
import pandas as pd
from datetime import datetime
import multiprocessing
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from longport.openapi import Period
from awesometrader import DataInterface

class MultiFactor(Strategy):
    # 可优化参数
    ma_fast_period = 18
    ma_slow_period = 32
    macd_fast_period = 12
    macd_slow_period = 45
    macd_signal_period = 9
    mfi_period = 16
    rsi_period = 16
    atr_period = 16
    
    def init(self):
        volume = self.data.Volume.astype(float)
        self.ma_fast = self.I(talib.SMA, self.data.Close, self.ma_fast_period)
        self.ma_slow = self.I(talib.SMA, self.data.Close, self.ma_slow_period)
        self.macd, self.macd_signal, self.macd_hist = self.I(talib.MACD, self.data.Close, self.macd_fast_period, self.macd_slow_period, self.macd_signal_period)
        self.mfi = self.I(talib.MFI, self.data.High, self.data.Low, self.data.Close, volume, self.mfi_period)
        self.rsi = self.I(talib.RSI, self.data.Close, self.rsi_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, self.atr_period)
        
        # 初始化仓位比例跟踪变量
        self.current_position_ratio = 0.0
        
        # 初始化交易记录变量
        self.pending_trade_info = None

    def next(self):
        # 如果有待记录的交易信息，先记录上次交易的结果
        # if self.pending_trade_info:
        #     self._log_trade_execution()
        
        # 使用仓位比例而不是股数
        size = self.current_position_ratio

        # MA快慢线交叉信号 - 5成仓位，每次调整0.5
        if crossover(self.ma_fast, self.ma_slow):
            size = min(size + 0.5, 0.9999)  # 增加仓位，最大不超过100%
        elif crossover(self.ma_slow, self.ma_fast):
            size = max(size - 0.5, 0.0001)  # 减少仓位，最小不低于0%
        
        # MACD信号线交叉 - 3成仓位，每次调整约0.3
        if crossover(self.macd, self.macd_signal):
            size = min(size + 0.3, 0.9999)  # 增加仓位
        elif crossover(self.macd_signal, self.macd):
            size = max(size - 0.3, 0.0001)  # 减少仓位
        
        # 如果仓位需要调整
        if self.current_position_ratio != size:
            # 记录决策信息，但不立即打印日志
            original_ratio = self.current_position_ratio
            adjustment = size - original_ratio
            decision_date = self.data.index[-1]
            decision_price = self.data.Close[-1]
            
            # 记录交易前的状态
            old_position_size = self.position.size
            
            # 显示信号来源
            signal_sources = []
            if crossover(self.ma_fast, self.ma_slow):
                signal_sources.append("MA金叉(+50%)")
            elif crossover(self.ma_slow, self.ma_fast):
                signal_sources.append("MA死叉(-50%)")
            if crossover(self.macd, self.macd_signal):
                signal_sources.append("MACD金叉(+30%)")
            elif crossover(self.macd_signal, self.macd):
                signal_sources.append("MACD死叉(-30%)")
            
            # 执行交易 - size为资金比例（0-1之间）
            if size > 0.0001:
                self.buy(size=size)
            else:
                # 如果目标仓位为0，关闭所有持仓
                if self.position:
                    self.position.close()
            
            # 更新当前仓位比例
            self.current_position_ratio = size
            
            # 保存交易信息，在下一个bar记录
            self.pending_trade_info = {
                'decision_date': decision_date,
                'decision_price': decision_price,
                'original_ratio': original_ratio,
                'new_ratio': size,
                'adjustment': adjustment,
                'old_position_size': old_position_size,
                'signal_sources': signal_sources
            }

    def _log_trade_execution(self):
        """记录交易执行后的详细信息"""
        info = self.pending_trade_info
        
        # 当前bar的信息（交易执行日）
        execution_date = self.data.index[-1]
        execution_price = self.data.Open[-1]  # 使用开盘价作为实际交易价格
        
        # 获取交易执行后的信息
        new_position_size = self.position.size
        
        # 手动计算基于开盘价的权益
        # 权益 = 初始资金 + 所有已平仓交易盈亏 + 当前持仓基于开盘价的盈亏
        initial_cash = 10000.0
        
        # 计算所有已平仓交易的净盈亏
        closed_trades_pl = sum(trade.pl for trade in self.closed_trades) if self.closed_trades else 0
        
        # 总权益 = 初始资金 + 所有盈亏
        new_equity = initial_cash + closed_trades_pl
        
        stock_value = abs(new_position_size) * execution_price
        planned_share_change = new_position_size - info['old_position_size']
        
        # 计算持仓的平均成本（加权平均买入价）
        avg_cost = 0.0
        total_position_shares = 0.0
        if self.trades and new_position_size != 0:
            # 计算所有持仓的总股数和加权成本
            for trade in self.trades:
                total_position_shares += abs(trade.size)
                avg_cost += abs(trade.size) * trade.entry_price
            
            if total_position_shares > 0:
                avg_cost = avg_cost / total_position_shares
            else:
                avg_cost = 0.0
        
        # 计算账户总盈亏（初始资金固定为10000美元）
        total_pl = new_equity - initial_cash
        total_pl_pct = (total_pl / initial_cash) * 100
        
        # 打印详细日志（交易执行后的信息）
        print(f"{'='*80}")
        print(f"决策日期: {info['decision_date']}")
        print(f"执行日期: {execution_date}")
        print(f"决策时价格: ${info['decision_price']:.2f}")
        print(f"实际执行价格: ${execution_price:.2f}")
        print(f"仓位调整: {info['original_ratio']:.1%} -> {info['new_ratio']:.1%} (调整: {info['adjustment']:+.1%})")
        print(f"实际调整股数: {planned_share_change:+.0f}股")
        print(f"执行后总市值: ${new_equity:.2f}")
        print(f"执行后股票市值: ${stock_value:.2f}")
        print(f"执行后持仓股数: {new_position_size:.0f}股")
        if new_position_size != 0 and avg_cost > 0:
            print(f"执行后持仓平均成本: ${avg_cost:.2f}")
        else:
            print(f"执行后持仓平均成本: N/A (无持仓)")
        print(f"账户总盈亏: ${total_pl:.2f} ({total_pl_pct:.2f}%)")
        
        if info['signal_sources']:
            print(f"信号来源: {', '.join(info['signal_sources'])}")
        print(f"{'='*80}")
        
        # 清除待记录信息
        self.pending_trade_info = None

Backtest.Pool = multiprocessing.Pool

if __name__ == '__main__':
    data_interface = DataInterface()
    data = data_interface.get_stock_data("NVDA.US", Period.Week, start_date=datetime(2018, 1, 1), end_date=datetime(2025, 6, 15))
    backtest = Backtest(data, MultiFactor, commission=.002, exclusive_orders=True)

    stats, heatmap = backtest.optimize(
            ma_fast_period=range(10, 16, 1),
            ma_slow_period=range(20, 30, 1),
            macd_fast_period=range(10, 20, 1),
            macd_slow_period=range(20, 50, 2),
            macd_signal_period=range(7, 12, 1),
            mfi_period=range(10, 20, 1),
            rsi_period=range(10, 20, 1),
            atr_period=range(10, 20, 1),
            constraint=lambda p: p.mfi_period == p.rsi_period == p.atr_period,
            maximize='Equity Final [$]',
            max_tries=10000,
            random_state=0,
            return_heatmap=True)

    print(stats)
    print(heatmap.sort_values().iloc[-3:])
    # hm = heatmap.groupby(['n']).mean().unstack()
    # hm = hm[::-1]
    # hm.to_csv('sma_heatmap.csv')

    # stats = backtest.run()
    # print(stats)
    # # backtest.plot()

    # stats['_trades'].to_csv('results/backtest_trades.csv', index=False)
    # stats['_equity_curve'].to_csv('results/backtest_equity_curve.csv', index=False)