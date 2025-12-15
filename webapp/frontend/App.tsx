import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  AlertTriangle, 
  RefreshCw,
  Activity, 
  JapaneseYen,
  Wallet
} from 'lucide-react';

import { 
  OverviewResponse, 
  EquityCurveResponse, 
  DrawdownResponse, 
  MonthlyResponse 
} from './types';
import { PERIOD_OPTIONS, BENCHMARK_OPTIONS } from './constants';
import { api } from './services/api';

import { StatCard } from './components/StatCard';
import { EquityChart } from './components/EquityChart';
import { RiskMetrics } from './components/RiskMetrics';
import { AssetChart } from './components/AssetChart';
import { MonthlyHeatmap } from './components/MonthlyHeatmap';

// Transform equity curve data from backend format {date, value} to component format {[date]: value}
const transformEquityData = (data: EquityCurveResponse | null): { period: string; portfolio: Record<string, number>[]; benchmark: Record<string, number>[] | null } | null => {
  if (!data) return null;
  
  const transformPoints = (points: { date: string; value: number }[] | null): Record<string, number>[] | null => {
    if (!points || points.length === 0) return null;
    return points.map(p => ({ [p.date]: p.value }));
  };
  
  return {
    period: data.period,
    portfolio: transformPoints(data.portfolio) || [],
    benchmark: transformPoints(data.benchmark)
  };
};

export default function App() {
  const [period, setPeriod] = useState<string>('all');
  const [benchmark, setBenchmark] = useState<string>('sp500');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Data States for Main Dashboard (Filtered by Period)
  const [overview, setOverview] = useState<OverviewResponse | null>(null);
  const [equityData, setEquityData] = useState<{ period: string; portfolio: Record<string, number>[]; benchmark: Record<string, number>[] | null } | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [drawdownData, setDrawdownData] = useState<DrawdownResponse | null>(null);
  const [monthlyData, setMonthlyData] = useState<MonthlyResponse | null>(null);

  // Data States for Heatmap (Always Full History)
  const [fullEquityData, setFullEquityData] = useState<{ period: string; portfolio: Record<string, number>[]; benchmark: Record<string, number>[] | null } | null>(null);
  const [fullMonthlyData, setFullMonthlyData] = useState<MonthlyResponse | null>(null);
  const [fullInitialValue, setFullInitialValue] = useState<number>(0);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch data from backend API
      const [overviewRes, equityRes, drawdownRes, monthlyRes] = await Promise.all([
        api.getOverview(period, benchmark),
        api.getEquityCurve(period, benchmark),
        api.getDrawdown(period),
        api.getMonthly(period)
      ]);

      // Transform equity data for components
      const transformedEquity = transformEquityData(equityRes);

      // Set states for the filtered dashboard view
      setOverview(overviewRes);
      setEquityData(transformedEquity);
      setDrawdownData(drawdownRes);
      setMonthlyData(monthlyRes);

      // Fetch full data for Heatmap (always use 'all' period)
      if (period !== 'all') {
        const [fullEquityRes, fullMonthlyRes, fullOverviewRes] = await Promise.all([
          api.getEquityCurve('all', benchmark),
          api.getMonthly('all'),
          api.getOverview('all', benchmark)
        ]);
        setFullEquityData(transformEquityData(fullEquityRes));
        setFullMonthlyData(fullMonthlyRes);
        setFullInitialValue(fullOverviewRes.initial_value);
      } else {
        setFullEquityData(transformedEquity);
        setFullMonthlyData(monthlyRes);
        setFullInitialValue(overviewRes.initial_value);
      }

    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch analytics data';
      setError(errorMessage);
      console.error('Fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [period, benchmark]);

  const formatProfit = (val: number) => {
    const inK = val / 1000;
    return `¥${inK.toFixed(2)}k`;
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 pb-12">
      {/* Navbar */}
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center gap-2">
              <div className="bg-blue-600 p-2 rounded-lg">
                <BarChart3 className="h-6 w-6 text-white" />
              </div>
              <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">
                Portfolio Analytics
              </h1>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="hidden md:flex items-center text-sm text-gray-500">
                <span className={`w-2 h-2 rounded-full mr-2 ${loading ? 'bg-yellow-400 animate-pulse' : 'bg-green-500'}`}></span>
                {loading ? 'Updating...' : 'Live'}
              </div>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Unified Control Bar */}
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 mb-8 flex flex-col lg:flex-row justify-between items-center gap-4">
          
          {/* Left: Time Period Segmented Control */}
          <div className="w-full lg:w-auto overflow-x-auto">
            <div className="bg-gray-100 p-1 rounded-lg inline-flex">
              {PERIOD_OPTIONS.map((opt) => {
                const isSelected = period === opt.value;
                return (
                  <button
                    key={opt.value}
                    onClick={() => setPeriod(opt.value)}
                    className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all duration-200 whitespace-nowrap ${
                      isSelected 
                        ? 'bg-white text-gray-900 shadow-sm' 
                        : 'text-gray-500 hover:text-gray-900'
                    }`}
                  >
                    {opt.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Right: Benchmark & Meta Actions */}
          <div className="flex flex-col sm:flex-row items-center gap-4 w-full lg:w-auto">
            <div className="flex items-center gap-3 w-full sm:w-auto">
              <label className="text-sm font-medium text-gray-500 whitespace-nowrap">Benchmark:</label>
              <div className="relative flex-grow sm:flex-grow-0">
                <select 
                  value={benchmark}
                  onChange={(e) => setBenchmark(e.target.value)}
                  className="bg-gray-50 border border-gray-200 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full sm:w-48 p-2.5"
                >
                  {BENCHMARK_OPTIONS.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
            </div>
              
            <div className="hidden sm:block w-px h-6 bg-gray-200"></div>
            
            <div className="flex items-center justify-between w-full sm:w-auto gap-4">
              <div className="text-sm text-gray-400 whitespace-nowrap">
                Updated: {overview?.end_date || '...'}
              </div>

              <button 
                onClick={fetchData}
                className="flex items-center px-4 py-2 text-sm font-medium text-gray-600 bg-gray-50 hover:bg-gray-100 hover:text-blue-600 rounded-lg transition-colors border border-gray-200 ml-auto sm:ml-0"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl mb-8 flex items-center">
            <AlertTriangle className="w-5 h-5 mr-2" />
            {error}
          </div>
        )}

        {/* Dashboard Content */}
        {overview && (
          <div className="space-y-8 animate-fade-in">
            
            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
              <StatCard 
                title="Total Return" 
                value={`${(overview.returns.cumulative_return * 100).toFixed(2)}%`} 
                trend={overview.returns.cumulative_return > 0 ? 'up' : 'down'}
                subValue="Selected Period"
                icon={<TrendingUp className="w-5 h-5 text-blue-600" />}
              />
              <StatCard 
                title="Total Assets" 
                value={formatProfit(overview.final_value)} 
                trend={(overview.final_value - overview.initial_value) >= 0 ? 'up' : 'down'}
                subValue="Current Value"
                icon={<Wallet className="w-5 h-5 text-indigo-600" />}
              />
              <StatCard 
                title="Total Profit" 
                value={formatProfit(overview.final_value - overview.initial_value)} 
                trend={(overview.final_value - overview.initial_value) >= 0 ? 'up' : 'down'}
                subValue="Absolute P&L"
                icon={<JapaneseYen className="w-5 h-5 text-purple-600" />}
              />
              <StatCard 
                title="Sharpe Ratio" 
                value={overview.risk.sharpe_ratio.toFixed(2)} 
                subValue="Risk Adjusted"
                icon={<Activity className="w-5 h-5 text-green-600" />}
              />
              <StatCard 
                title="Max Drawdown" 
                value={`${(overview.risk.max_drawdown * 100).toFixed(2)}%`}
                trend="down" // Always bad
                className="border-red-100 bg-red-50/10"
                icon={<AlertTriangle className="w-5 h-5 text-red-600" />}
              />
            </div>

            {/* Charts Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 items-start">
              
              {/* Left Column: Charts (60% width) */}
              <div className="lg:col-span-3 flex flex-col gap-6">
                 {/* 1. Asset Trend (Top) - Decreased height */}
                 <div className="h-[380px]">
                   <AssetChart 
                     data={equityData as any} 
                     initialValue={overview.initial_value} 
                     className="h-full"
                   />
                 </div>

                 {/* 2. Equity Curve (Bottom) - Decreased height */}
                 <div className="h-[450px]">
                    <EquityChart 
                      data={equityData as any} 
                      benchmarkName={BENCHMARK_OPTIONS.find(b => b.value === benchmark)?.label || 'Benchmark'} 
                      className="h-full"
                    />
                 </div>
              </div>

              {/* Right Column: Heatmap (40% width) */}
              <div className="lg:col-span-2">
                <MonthlyHeatmap 
                  data={fullMonthlyData} 
                  equityData={fullEquityData as any} 
                  initialValue={fullInitialValue}
                />
              </div>

            </div>

            {/* Divider */}
            <div className="relative py-4">
              <div className="absolute inset-0 flex items-center" aria-hidden="true">
                <div className="w-full border-t border-gray-300"></div>
              </div>
            </div>

            {/* Key Risk & Performance Metrics Table */}
            <div>
              <h3 className="text-xl font-bold text-gray-800 mb-6">Key Risk & Performance Metrics</h3>
              <RiskMetrics data={overview} />
            </div>

          </div>
        )}

        {!overview && !loading && !error && (
            <div className="text-center py-20 text-gray-400">
                No data available. Please check the backend connection.
            </div>
        )}
      </main>
    </div>
  );
}
