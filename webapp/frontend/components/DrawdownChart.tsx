import React from 'react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { DrawdownResponse } from '../types';

interface DrawdownChartProps {
  data: DrawdownResponse | null;
}

export const DrawdownChart: React.FC<DrawdownChartProps> = ({ data }) => {
  if (!data || !data.drawdown_series) return null;

  const chartData = data.drawdown_series.map(item => {
    const date = Object.keys(item)[0];
    return {
      date,
      drawdown: item[date]
    };
  });

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-bold text-gray-800">Drawdown Analysis</h3>
        <div className="text-sm text-gray-500">
          Max: <span className="font-bold text-red-600">{(data.max_drawdown * 100).toFixed(2)}%</span>
        </div>
      </div>
      <div className="h-[250px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 0, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorDrawdown" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
            <XAxis 
              dataKey="date" 
              hide
            />
            <YAxis 
              tick={{fontSize: 12, fill: '#64748b'}} 
              tickFormatter={(val) => `${(val * 100).toFixed(0)}%`}
            />
            <Tooltip 
              contentStyle={{backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0'}}
              formatter={(val: number) => [(val * 100).toFixed(2) + '%', 'Drawdown']}
              labelFormatter={(label) => new Date(label).toLocaleDateString()}
            />
            <Area 
              type="monotone" 
              dataKey="drawdown" 
              stroke="#ef4444" 
              strokeWidth={1}
              fillOpacity={1} 
              fill="url(#colorDrawdown)" 
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      
      {/* Top Drawdowns List */}
      <div className="mt-6">
        <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Worst Drawdowns</h4>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left text-gray-500">
            <thead className="text-xs text-gray-700 uppercase bg-gray-50">
              <tr>
                <th className="px-3 py-2">Depth</th>
                <th className="px-3 py-2">Start</th>
                <th className="px-3 py-2">Bottom</th>
                <th className="px-3 py-2">End</th>
                <th className="px-3 py-2">Recovery (Days)</th>
              </tr>
            </thead>
            <tbody>
              {data.worst_drawdowns.slice(0, 5).map((dd, idx) => (
                <tr key={idx} className="bg-white border-b hover:bg-gray-50">
                  <td className="px-3 py-2 font-medium text-red-600">{(dd.drawdown * 100).toFixed(2)}%</td>
                  <td className="px-3 py-2">{dd.start_date}</td>
                  {/* Note: API structure might need adjustment to include valley date if needed, usually inferred */}
                  <td className="px-3 py-2">-</td> 
                  <td className="px-3 py-2">{dd.end_date || 'Active'}</td>
                  <td className="px-3 py-2">{dd.recovery_days || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};