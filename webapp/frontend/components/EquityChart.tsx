import React from 'react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { EquityCurveResponse } from '../types';

interface EquityChartProps {
  data: EquityCurveResponse | null;
  benchmarkName: string;
  className?: string;
}

const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`;

export const EquityChart: React.FC<EquityChartProps> = ({ data, benchmarkName, className }) => {
  if (!data || !data.portfolio) return (
      <div className={`bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center justify-center text-gray-400 ${className}`}>
        Loading Chart...
      </div>
  );

  // Process data: Merge portfolio and benchmark
  // 后端返回格式为 {"date": "2025-07-02", "value": 1.0}
  const portfolioMap = new Map();
  data.portfolio.forEach(item => {
    const date = (item as any).date || Object.keys(item)[0];
    const value = (item as any).value !== undefined ? (item as any).value : item[date];
    // Backend returns Total Return Factor (e.g. 1.0 start, 1.45 for +45% gain).
    // We subtract 1 to show percentage on chart.
    portfolioMap.set(date, value - 1); 
  });

  const benchmarkMap = new Map();
  if (data.benchmark) {
    data.benchmark.forEach(item => {
      const date = (item as any).date || Object.keys(item)[0];
      const value = (item as any).value !== undefined ? (item as any).value : item[date];
      benchmarkMap.set(date, value - 1);
    });
  }

  const chartData = Array.from(portfolioMap.keys()).map(date => ({
    date,
    Portfolio: portfolioMap.get(date),
    Benchmark: benchmarkMap.get(date) ?? null
  })).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

  return (
    <div className={`bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col ${className}`}>
      <h3 className="text-lg font-bold text-gray-800 mb-4">Cumulative Returns vs Benchmark</h3>
      <div className="flex-grow w-full min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorPortfolio" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorBenchmark" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#94a3b8" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#94a3b8" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
            <XAxis 
              dataKey="date" 
              tick={{fontSize: 12, fill: '#64748b'}} 
              tickFormatter={(val) => new Date(val).toLocaleDateString(undefined, {month:'short', day:'numeric'})}
              minTickGap={30}
            />
            <YAxis 
              tick={{fontSize: 12, fill: '#64748b'}} 
              tickFormatter={formatPercent}
            />
            <Tooltip 
              contentStyle={{backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0'}}
              formatter={(val: number) => [(val * 100).toFixed(2) + '%', '']}
              labelFormatter={(label) => new Date(label).toLocaleDateString()}
            />
            <Legend verticalAlign="top" height={36}/>
            <Area 
              type="monotone" 
              dataKey="Portfolio" 
              stroke="#3b82f6" 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorPortfolio)" 
            />
            <Area 
              type="monotone" 
              dataKey="Benchmark" 
              stroke="#94a3b8" 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorBenchmark)" 
              name={benchmarkName}
              strokeDasharray="5 5"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};