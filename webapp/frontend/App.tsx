import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  AlertTriangle, 
  RefreshCw,
  Activity, 
  JapaneseYen,
  Wallet,
  CalendarDays
} from 'lucide-react';

import { 
  OverviewResponse, 
  EquityCurveResponse, 
  MonthlyResponse,
  ReturnsResponse,
  DrawdownResponse
} from './types';
import { PERIOD_OPTIONS, BENCHMARK_OPTIONS } from './constants';
import { api } from './services/api';

import { StatCard } from './components/StatCard';
import { EquityChart } from './components/EquityChart';
import { RiskMetrics } from './components/RiskMetrics';
import { AssetChart } from './components/AssetChart';
import { MonthlyHeatmap } from './components/MonthlyHeatmap';

export default function App() {
  const [period, setPeriod] = useState<string>('all');
  const [benchmark, setBenchmark] = useState<string>('sp500');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [overview, setOverview] = useState<OverviewResponse | null>(null);
  const [equityData, setEquityData] = useState<EquityCurveResponse | null>(null);
  const [monthlyData, setMonthlyData] = useState<MonthlyResponse | null>(null);

  const [fullEquityData, setFullEquityData] = useState<EquityCurveResponse | null>(null);
  const [fullMonthlyData, setFullMonthlyData] = useState<MonthlyResponse | null>(null);
  const [fullInitialValue, setFullInitialValue] = useState<number>(0);
  
  // 图表数据
  const [returnsData, setReturnsData] = useState<ReturnsResponse | null>(null);
  const [drawdownData, setDrawdownData] = useState<DrawdownResponse | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      // 并行请求所有数据
      const [overviewData, equityData, monthlyData, fullEquity, fullMonthly, returns, drawdown] = await Promise.all([
        api.getOverview(period, benchmark),
        api.getEquityCurve(period, benchmark),
        api.getMonthly(period),
        api.getEquityCurve('all', benchmark),
        api.getMonthly('all'),
        api.getReturns(period),
        api.getDrawdown(period),
      ]);

      setOverview(overviewData);
      setEquityData(equityData);
      setMonthlyData(monthlyData);

      setFullEquityData(fullEquity);
      setFullMonthlyData(fullMonthly);
      setFullInitialValue(overviewData.initial_value);
      
      setReturnsData(returns);
      setDrawdownData(drawdown);

    } catch (err: any) {
      console.error('Failed to fetch analytics data:', err);
      setError(err.message || 'Failed to fetch analytics data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [period, benchmark]);

  const formatProfit = (val: number) => {
    const inK = val / 1000;
    return `¥${inK.toFixed(2)}k`;
  };

  return (
    <div className="min-h-screen bg-[#fcfdfe] text-slate-900 pb-12 font-sans">
      <nav className="bg-white border-b border-gray-100 sticky top-0 z-50">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center gap-3">
              <div className="bg-blue-600 p-2 rounded-xl shadow-blue-200 shadow-lg">
                <BarChart3 className="h-5 w-5 text-white" />
              </div>
              <h1 className="text-xl font-extrabold tracking-tight text-gray-900">
                Portfolio Analytics
              </h1>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="hidden md:flex items-center text-sm font-medium text-gray-500 bg-gray-100/50 px-3 py-1.5 rounded-full border border-gray-100">
                <span className={`w-2 h-2 rounded-full mr-2 ${loading ? 'bg-yellow-400 animate-pulse' : 'bg-green-500'}`}></span>
                {loading ? 'Refreshing...' : 'System Active'}
              </div>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Simplified Header Control Bar */}
        <div className="bg-white px-6 py-4 rounded-2xl shadow-sm border border-gray-100 mb-8 flex flex-col lg:flex-row justify-between items-center gap-6">
          <div className="w-full lg:w-auto overflow-x-auto scrollbar-hide">
            <div className="bg-gray-50 p-1.5 rounded-xl inline-flex border border-gray-100/50">
              {PERIOD_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setPeriod(opt.value)}
                  className={`px-5 py-2 text-sm font-bold rounded-lg transition-all duration-300 whitespace-nowrap ${
                    period === opt.value 
                      ? 'bg-white text-gray-900 shadow-md border border-gray-100' 
                      : 'text-gray-400 hover:text-gray-600'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-6 w-full lg:w-auto">
            <div className="flex items-center gap-3">
              <span className="text-sm font-bold text-gray-500">Benchmark:</span>
              <select 
                value={benchmark}
                onChange={(e) => setBenchmark(e.target.value)}
                className="bg-white border border-gray-200 text-gray-900 text-sm font-bold rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none px-4 py-2.5 transition-all w-full sm:w-44 shadow-sm"
              >
                {BENCHMARK_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
              
            <div className="hidden sm:block w-px h-8 bg-gray-100"></div>
            
            <div className="flex items-center gap-6 text-sm">
              <div className="flex items-center gap-2 text-gray-400 font-medium">
                <CalendarDays className="w-4 h-4" />
                <span>Updated: {overview?.end_date || '...'}</span>
              </div>

              <button 
                onClick={fetchData}
                className="flex items-center px-5 py-2.5 text-sm font-bold text-gray-700 bg-white hover:bg-gray-50 border border-gray-200 rounded-xl transition-all shadow-sm active:scale-95"
              >
                <RefreshCw className={`w-4 h-4 mr-2 text-gray-500 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-2xl mb-8 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-500" />
            <div>
              <p className="font-bold">Failed to load data</p>
              <p className="text-sm">{error}</p>
            </div>
            <button 
              onClick={fetchData}
              className="ml-auto px-4 py-2 bg-red-100 hover:bg-red-200 text-red-700 font-bold rounded-lg transition-all text-sm"
            >
              Retry
            </button>
          </div>
        )}

        {overview && (
          <div className="space-y-8">
            {/* KPI Cards with Title Case */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
              <StatCard 
                title="Total Assets" 
                value={formatProfit(overview.final_value)} 
                trend={(overview.final_value - overview.initial_value) >= 0 ? 'up' : 'down'}
                subValue="Current Value"
                icon={<Wallet className="w-7 h-7 text-blue-600" />}
                iconBgColor="bg-blue-50/80"
              />
              <StatCard 
                title="Total Profit" 
                value={formatProfit(overview.final_value - overview.initial_value)} 
                trend={(overview.final_value - overview.initial_value) >= 0 ? 'up' : 'down'}
                subValue="Absolute P&L"
                icon={<JapaneseYen className="w-7 h-7 text-purple-600" />}
                iconBgColor="bg-purple-50/60"
              />
              <StatCard 
                title="Total Return" 
                value={`${(overview.returns.cumulative_return * 100).toFixed(2)}%`} 
                trend={overview.returns.cumulative_return > 0 ? 'up' : 'down'}
                subValue="Selected Period"
                icon={<TrendingUp className="w-7 h-7 text-indigo-600" />}
                iconBgColor="bg-indigo-50/80"
              />
              <StatCard 
                title="Sharpe Ratio" 
                value={overview.risk.sharpe_ratio.toFixed(2)} 
                subValue="Risk Adjusted"
                trend="neutral"
                icon={<Activity className="w-7 h-7 text-emerald-600" />}
                iconBgColor="bg-emerald-50/80"
              />
              <StatCard 
                title="Max Drawdown" 
                value={`${(overview.risk.max_drawdown * 100).toFixed(2)}%`}
                trend="down"
                subValue="Risk Metric"
                icon={<AlertTriangle className="w-7 h-7 text-orange-600" />}
                iconBgColor="bg-orange-50/80"
              />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
              <div className="lg:col-span-3 flex flex-col gap-8">
                 <div className="h-[500px]">
                   <AssetChart 
                     data={equityData} 
                     initialValue={overview.initial_value} 
                     className="h-full rounded-2xl border border-gray-100 shadow-sm"
                   />
                 </div>
                 <div className="h-[540px]">
                    <EquityChart 
                      data={equityData} 
                      benchmarkName={BENCHMARK_OPTIONS.find(b => b.value === benchmark)?.label || 'Benchmark'} 
                      className="h-full rounded-2xl border border-gray-100 shadow-sm"
                    />
                 </div>
              </div>

              <div className="lg:col-span-2">
                <MonthlyHeatmap 
                  data={fullMonthlyData} 
                  equityData={fullEquityData} 
                  initialValue={fullInitialValue}
                />
              </div>
            </div>

            <div className="pt-8">
              <h3 className="text-xl font-extrabold text-gray-900 mb-6 flex items-center gap-2">
                <Activity className="w-6 h-6 text-blue-600" />
                Key Risk & Performance Metrics
              </h3>
              <RiskMetrics 
                data={overview} 
                benchmarkName={BENCHMARK_OPTIONS.find(b => b.value === benchmark)?.label || 'Benchmark'}
                returnsData={returnsData}
                drawdownData={drawdownData}
                equityData={equityData}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}