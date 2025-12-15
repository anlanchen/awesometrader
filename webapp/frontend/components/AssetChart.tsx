import React from 'react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { EquityCurveResponse } from '../types';

interface AssetChartProps {
  data: EquityCurveResponse | null;
  initialValue: number;
  className?: string;
}

const formatCurrencyK = (value: number) => {
  const inK = value / 1000;
  return `¥${inK.toFixed(2)}k`;
};

export const AssetChart: React.FC<AssetChartProps> = ({ data, initialValue, className }) => {
  if (!data || !data.portfolio) return null;

  // Calculate Asset Value: Initial Value * (1 + Cumulative Return)
  // Assuming the portfolio series in EquityCurveResponse is normalized (starts at ~1.0 or represents growth)
  
  const chartData = data.portfolio.map(item => {
    const date = Object.keys(item)[0];
    const growthFactor = item[date]; // e.g., 1.05
    return {
      date,
      value: initialValue * growthFactor
    };
  }).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

  return (
    <div className={`bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col ${className}`}>
      <h3 className="text-lg font-bold text-gray-800 mb-4">Asset Trend</h3>
      <div className="flex-grow w-full min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorAsset" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
            <XAxis 
              dataKey="date" 
              tick={{fontSize: 12, fill: '#64748b'}} 
              tickFormatter={(val) => new Date(val).toLocaleDateString(undefined, {month:'short', day:'numeric'})}
              minTickGap={40}
            />
            <YAxis 
              tick={{fontSize: 12, fill: '#64748b'}} 
              tickFormatter={formatCurrencyK}
              domain={['auto', 'auto']} 
            />
            <Tooltip 
              contentStyle={{backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0'}}
              formatter={(val: number) => [formatCurrencyK(val), 'Total Assets']}
              labelFormatter={(label) => new Date(label).toLocaleDateString()}
            />
            <Area 
              type="monotone" 
              dataKey="value" 
              stroke="#10b981" 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorAsset)" 
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};