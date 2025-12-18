import React, { useState, useMemo } from 'react';
import { OverviewResponse, ReturnsResponse, DrawdownResponse, EquityCurveResponse, ChartSeriesData } from '../types';
import { HelpCircle, Info } from 'lucide-react';
import { MetricExplanationModal } from './MetricExplanationModal';
import { 
  DailyReturnsChart, 
  UnderwaterChart, 
  RollingMetricChart, 
  BetaAnalysisChart 
} from './MetricsCharts';

interface RiskMetricsProps {
  data: OverviewResponse | null;
  benchmarkName?: string;
  returnsData?: ReturnsResponse | null;
  drawdownData?: DrawdownResponse | null;
  equityData?: EquityCurveResponse | null;
}

const TableCell = ({ label, spy, strategy, onHover, onLeave }: any) => (
  <tr className="border-b border-gray-50 hover:bg-blue-50/30 transition-colors group">
    <td className="py-2.5 pl-4 flex items-center gap-2">
      <div 
        onMouseEnter={(e) => onHover(label, e)}
        onMouseLeave={onLeave}
        className="text-gray-300 hover:text-blue-500 transition-colors cursor-help p-0.5"
      >
        <HelpCircle className="w-3.5 h-3.5" />
      </div>
      <span className="text-[11px] font-bold text-gray-500 group-hover:text-gray-700 truncate">{label}</span>
    </td>
    <td className="py-2.5 px-2 text-right text-[11px] font-mono text-gray-400">{spy}</td>
    <td className={`py-2.5 pr-4 text-right text-[11px] font-bold font-mono ${strategy.toString().includes('-') ? 'text-rose-500' : 'text-emerald-600'}`}>
      {strategy}
    </td>
  </tr>
);

const SectionHeader = ({ title }: { title: string }) => (
  <tr className="bg-gray-100/50">
    <td colSpan={3} className="py-2 px-4 text-[10px] font-extrabold text-gray-500 tracking-tight border-y border-gray-100">
      {title}
    </td>
  </tr>
);

export const RiskMetrics: React.FC<RiskMetricsProps> = ({ 
  data, 
  benchmarkName = 'Benchmark',
  returnsData,
  drawdownData,
  equityData
}) => {
  const [hoveredMetric, setHoveredMetric] = useState<string | null>(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  const handleHover = (key: string, e: React.MouseEvent) => {
    setHoveredMetric(key);
    setMousePos({ x: e.clientX, y: e.clientY });
  };

  const handleLeave = () => {
    setHoveredMetric(null);
  };

  // 使用真实数据计算图表序列
  const chartSeries = useMemo((): ChartSeriesData[] => {
    if (!returnsData || !drawdownData || !equityData) return [];

    const minWindow = 5; // 最小滚动窗口
    const preferredWindow = 20; // 首选滚动窗口大小

    // 构建日期到数据的映射
    const portfolioReturns = new Map<string, number>();
    returnsData.daily_returns.forEach(r => {
      portfolioReturns.set(r.date, r.return);
    });

    // 解析 drawdown_series - 后端格式: {date: string, drawdown: number}
    const drawdownMap = new Map<string, number>();
    drawdownData.drawdown_series.forEach((d: any) => {
      const date = d.date || Object.keys(d)[0];
      const drawdown = d.drawdown !== undefined ? d.drawdown : d[date];
      drawdownMap.set(date, drawdown);
    });

    // 基准收益率（从 equityData 计算日收益率）
    // 后端格式: {date: string, value: number}
    const benchmarkReturns = new Map<string, number>();
    const benchmarkCurve = new Map<string, number>(); // 保存基准曲线值用于回撤计算
    if (equityData.benchmark && equityData.benchmark.length > 1) {
      // 解析并排序
      const parsed = equityData.benchmark.map((item: any) => ({
        date: item.date || Object.keys(item)[0],
        value: item.value !== undefined ? item.value : item[item.date || Object.keys(item)[0]]
      }));
      const sorted = parsed.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
      
      // 计算日收益率
      for (let i = 0; i < sorted.length; i++) {
        benchmarkCurve.set(sorted[i].date, sorted[i].value);
        if (i > 0) {
          const prevVal = sorted[i - 1].value;
          const currVal = sorted[i].value;
          benchmarkReturns.set(sorted[i].date, (currVal / prevVal) - 1);
        }
      }
    }

    // 获取所有日期并排序
    const allDates = Array.from(portfolioReturns.keys()).sort(
      (a, b) => new Date(a).getTime() - new Date(b).getTime()
    );

    // 数据不足时返回空
    if (allDates.length < minWindow) return [];

    // 自适应窗口大小：数据充足时使用首选窗口，否则使用较小窗口
    const window = Math.min(preferredWindow, Math.floor(allDates.length / 2));
    const actualWindow = Math.max(window, minWindow);

    const result: ChartSeriesData[] = [];

    // 滑动窗口计算滚动指标
    for (let i = actualWindow; i < allDates.length; i++) {
      const date = allDates[i];
      const windowDates = allDates.slice(i - actualWindow, i);

      // 获取窗口内的收益率
      const pReturns = windowDates.map(d => portfolioReturns.get(d) || 0);
      const bReturns = windowDates.map(d => benchmarkReturns.get(d) || 0);

      // 计算统计量
      const meanP = pReturns.reduce((a, b) => a + b, 0) / actualWindow;
      const meanB = bReturns.reduce((a, b) => a + b, 0) / actualWindow;
      const stdP = Math.sqrt(pReturns.reduce((a, b) => a + Math.pow(b - meanP, 2), 0) / actualWindow);
      const stdB = Math.sqrt(bReturns.reduce((a, b) => a + Math.pow(b - meanB, 2), 0) / actualWindow);

      // 协方差和Beta（策略相对于基准的Beta）
      const covariance = windowDates.reduce((sum, d, idx) => {
        return sum + (pReturns[idx] - meanP) * (bReturns[idx] - meanB);
      }, 0) / actualWindow;
      const varianceB = bReturns.reduce((a, b) => a + Math.pow(b - meanB, 2), 0) / actualWindow;
      const rollingBeta = varianceB === 0 ? 0 : covariance / varianceB;

      // 下行风险
      const downsideP = Math.sqrt(pReturns.reduce((a, b) => a + Math.pow(Math.min(0, b), 2), 0) / actualWindow);
      const downsideB = Math.sqrt(bReturns.reduce((a, b) => a + Math.pow(Math.min(0, b), 2), 0) / actualWindow);

      // 基准回撤计算（从基准曲线计算）
      let benchmarkDrawdown = 0;
      const benchmarkDatesUpToNow = allDates.slice(0, i + 1).filter(d => benchmarkCurve.has(d));
      if (benchmarkDatesUpToNow.length > 0) {
        const benchmarkValues = benchmarkDatesUpToNow.map(d => benchmarkCurve.get(d)!);
        const peak = Math.max(...benchmarkValues);
        const current = benchmarkCurve.get(date) || benchmarkValues[benchmarkValues.length - 1];
        benchmarkDrawdown = (current - peak) / peak;
      }

      result.push({
        date,
        portfolio: portfolioReturns.get(date) || 0,
        benchmark: benchmarkReturns.get(date) || 0,
        drawdown: drawdownMap.get(date) || 0,
        benchmarkDrawdown,
        beta: rollingBeta,
        benchmarkBeta: 1.0, // Benchmark 相对于自身的 Beta 始终为 1（这是定义）
        vol: stdP * Math.sqrt(252),
        benchmarkVol: stdB * Math.sqrt(252),
        sharpe: stdP === 0 ? 0 : (meanP / stdP) * Math.sqrt(252),
        benchmarkSharpe: stdB === 0 ? 0 : (meanB / stdB) * Math.sqrt(252),
        sortino: downsideP === 0 ? 0 : (meanP / downsideP) * Math.sqrt(252),
        benchmarkSortino: downsideB === 0 ? 0 : (meanB / downsideB) * Math.sqrt(252),
        b_ret: benchmarkReturns.get(date) || 0,
        p_ret: portfolioReturns.get(date) || 0,
      });
    }

    return result;
  }, [returnsData, drawdownData, equityData]);

  if (!data) return <div className="h-96 bg-gray-50 rounded-2xl animate-pulse"></div>;

  const formatP = (v: number | undefined) => v !== undefined ? `${(v * 100).toFixed(2)}%` : '-';
  const formatN = (v: number | undefined, d = 2) => v !== undefined ? v.toFixed(d) : '-';

  const hasChartData = chartSeries.length > 0;

  return (
    <div className="flex flex-col lg:flex-row gap-8 items-start w-full">
      {/* Left Column: Charts (60%) */}
      <div className="lg:w-[60%] flex flex-col gap-8 w-full">
        {hasChartData ? (
          <>
            <div className="h-96"><DailyReturnsChart data={chartSeries} title="Daily Returns" /></div>
            <div className="h-96"><UnderwaterChart data={chartSeries} title="Drawdown" /></div>
            <div className="h-96"><BetaAnalysisChart data={chartSeries} title="Beta Analysis" /></div>
            <div className="h-96">
              <RollingMetricChart 
                data={chartSeries} 
                title="Rolling Beta (1-Mo)" 
                dataKey="beta" 
                benchmarkKey="benchmarkBeta"
                color="#3b82f6" 
                yAxisLabel="Beta Value" 
              />
            </div>
            <div className="h-96">
              <RollingMetricChart 
                data={chartSeries} 
                title="Rolling Volatility (1-Mo)" 
                dataKey="vol" 
                benchmarkKey="benchmarkVol"
                color="#10b981" 
                yAxisLabel="Volatility" 
              />
            </div>
            <div className="h-96">
              <RollingMetricChart 
                data={chartSeries} 
                title="Rolling Sharpe Ratio (1-Mo)" 
                dataKey="sharpe" 
                benchmarkKey="benchmarkSharpe"
                color="#8b5cf6" 
                yAxisLabel="Sharpe" 
              />
            </div>
            <div className="h-96">
              <RollingMetricChart 
                data={chartSeries} 
                title="Rolling Sortino Ratio (1-Mo)" 
                dataKey="sortino" 
                benchmarkKey="benchmarkSortino"
                color="#ec4899" 
                yAxisLabel="Sortino" 
              />
            </div>
          </>
        ) : (
          <div className="h-96 bg-gray-50 rounded-2xl flex items-center justify-center text-gray-400">
            Loading chart data...
          </div>
        )}
      </div>

      {/* Right Column: Full Metrics Table (40%) */}
      <div className="lg:w-[40%] w-full">
        <div className="bg-white border border-gray-100 rounded-2xl shadow-sm overflow-hidden">
          <div className="w-full">
            <table className="w-full table-fixed">
              <thead className="bg-white text-[10px] font-bold text-gray-400 tracking-wider border-b border-gray-50">
                <tr>
                  <th className="py-2.5 pl-4 text-left w-[55%]">Metric</th>
                  <th className="py-2.5 px-2 text-right truncate max-w-[80px]" title={benchmarkName}>{benchmarkName}</th>
                  <th className="py-2.5 pr-4 text-right">Strategy</th>
                </tr>
              </thead>
              <tbody>
                <SectionHeader title="Returns Summary" />
                <TableCell label="Cumulative Return" spy={formatP(data.benchmark?.benchmark_return)} strategy={formatP(data.returns.cumulative_return)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="CAGR%" spy={formatP(data.benchmark?.benchmark_cagr)} strategy={formatP(data.returns.annualized_return)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Geometric Mean" spy={formatP(data.benchmark?.benchmark_geometric_mean)} strategy={formatP(data.returns.geometric_mean)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Expected Daily Return" spy={formatP(data.benchmark?.benchmark_daily_mean)} strategy={formatP(data.returns.daily_return_mean)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Expected Monthly Return" spy={formatP(data.benchmark?.benchmark_expected_monthly)} strategy={formatP(data.returns.expected_monthly)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Expected Yearly Return" spy={formatP(data.benchmark?.benchmark_expected_yearly)} strategy={formatP(data.returns.expected_yearly)} onHover={handleHover} onLeave={handleLeave} />
                
                <SectionHeader title="Performance Metrics" />
                <TableCell label="Avg Win" spy={formatP(data.benchmark?.benchmark_avg_win)} strategy={formatP(data.returns.avg_win)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Avg Loss" spy={formatP(data.benchmark?.benchmark_avg_loss)} strategy={formatP(data.returns.avg_loss)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Avg Return" spy={formatP(data.benchmark?.benchmark_daily_mean)} strategy={formatP(data.returns.daily_return_mean)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Win Rate" spy={formatP(data.benchmark?.benchmark_win_rate)} strategy={formatP(data.returns.win_rate)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Profit Factor" spy={formatN(data.benchmark?.benchmark_profit_factor)} strategy={formatN(data.returns.profit_factor)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Payoff Ratio" spy={formatN(data.benchmark?.benchmark_payoff_ratio)} strategy={formatN(data.returns.payoff_ratio)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Best Day" spy={formatP(data.benchmark?.benchmark_best_day)} strategy={formatP(data.returns.best_day)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Worst Day" spy={formatP(data.benchmark?.benchmark_worst_day)} strategy={formatP(data.returns.worst_day)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Expectancy" spy={formatP(data.benchmark?.benchmark_expectancy)} strategy={formatP(data.returns.expectancy)} onHover={handleHover} onLeave={handleLeave} />

                <SectionHeader title="Risk & Volatility" />
                <TableCell label="Max Drawdown" spy={formatP(data.benchmark?.benchmark_max_drawdown)} strategy={formatP(data.risk.max_drawdown)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Volatility (ann.)" spy={formatP(data.benchmark?.benchmark_volatility)} strategy={formatP(data.risk.volatility)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Ulcer Index" spy={formatN(data.benchmark?.benchmark_ulcer_index, 4)} strategy={formatN(data.risk.ulcer_index, 4)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Skew" spy={formatN(data.benchmark?.benchmark_skewness)} strategy={formatN(data.risk.skewness)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Kurtosis" spy={formatN(data.benchmark?.benchmark_kurtosis)} strategy={formatN(data.risk.kurtosis)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Value at Risk (95%)" spy={formatP(data.benchmark?.benchmark_var_95)} strategy={formatP(data.risk.var_95)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="cVaR / Expected Shortfall" spy={formatP(data.benchmark?.benchmark_cvar_95)} strategy={formatP(data.risk.cvar_95)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Tail Ratio" spy={formatN(data.benchmark?.benchmark_tail_ratio)} strategy={formatN(data.risk.tail_ratio)} onHover={handleHover} onLeave={handleLeave} />

                <SectionHeader title="Risk Adjusted" />
                <TableCell label="Sharpe Ratio" spy={formatN(data.benchmark?.benchmark_sharpe)} strategy={formatN(data.risk.sharpe_ratio)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Sortino Ratio" spy={formatN(data.benchmark?.benchmark_sortino)} strategy={formatN(data.risk.sortino_ratio)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Calmar Ratio" spy={formatN(data.benchmark?.benchmark_calmar)} strategy={formatN(data.risk.calmar_ratio)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Omega Ratio" spy={formatN(data.benchmark?.benchmark_omega_ratio)} strategy={formatN(data.risk.omega_ratio)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Gain to Pain Ratio" spy={formatN(data.benchmark?.benchmark_gain_to_pain_ratio)} strategy={formatN(data.risk.gain_to_pain_ratio)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Risk Return Ratio" spy={formatN(data.benchmark?.benchmark_risk_return_ratio)} strategy={formatN(data.risk.risk_return_ratio)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Common Sense Ratio" spy={formatN(data.benchmark?.benchmark_common_sense_ratio)} strategy={formatN(data.risk.common_sense_ratio)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Kelly Criterion" spy={formatP(data.benchmark?.benchmark_kelly_criterion)} strategy={formatP(data.risk.kelly_criterion)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Recovery Factor" spy={formatN(data.benchmark?.benchmark_recovery_factor)} strategy={formatN(data.risk.recovery_factor)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Ulcer Performance Index (UPI)" spy={formatN(data.benchmark?.benchmark_ulcer_performance_index)} strategy={formatN(data.risk.ulcer_performance_index)} onHover={handleHover} onLeave={handleLeave} />

                <SectionHeader title="Benchmark Comparison" />
                <TableCell label="Benchmark Return" spy={formatP(data.benchmark?.benchmark_return)} strategy={formatP(data.returns.cumulative_return)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Alpha" spy="-" strategy={formatN(data.benchmark?.alpha, 4)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Beta" spy="1.00" strategy={formatN(data.benchmark?.beta)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Correlation" spy="1.00" strategy={formatN(data.benchmark?.correlation)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Information Ratio" spy="-" strategy={formatN(data.benchmark?.information_ratio)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Tracking Error" spy="-" strategy={formatP(data.benchmark?.tracking_error)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Up Capture" spy="100%" strategy={formatP(data.benchmark?.up_capture)} onHover={handleHover} onLeave={handleLeave} />
                <TableCell label="Down Capture" spy="100%" strategy={formatP(data.benchmark?.down_capture)} onHover={handleHover} onLeave={handleLeave} />
              </tbody>
            </table>
          </div>
          <div className="p-4 bg-gray-50 border-t border-gray-100">
            <div className="flex items-start gap-2">
                <Info className="w-3.5 h-3.5 text-blue-500 mt-0.5 flex-shrink-0" />
                <p className="text-[10px] text-gray-500 leading-normal font-medium">
                  Analysis follows QuantStats methodology. Benchmark: {benchmarkName}.
                </p>
            </div>
          </div>
        </div>
      </div>

      <MetricExplanationModal 
        isOpen={!!hoveredMetric} 
        metricKey={hoveredMetric || ''} 
        mousePos={mousePos}
      />
    </div>
  );
};