import React from 'react';
import { 
  ResponsiveContainer, BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, 
  Tooltip, AreaChart, Area, ScatterChart, Scatter, Label, Legend 
} from 'recharts';

const chartStyles = {
  axis: { fontSize: 10, fill: '#94a3b8' },
  grid: { stroke: '#f1f5f9', strokeDasharray: '3 3' },
  tooltip: { backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px' },
  label: { fontSize: 10, fill: '#64748b', fontWeight: 600 }
};

const formatDate = (val: string) => {
  const d = new Date(val);
  return `${d.getMonth() + 1}/${d.getFullYear().toString().slice(-2)}`;
};

interface ChartProps {
  data: any[];
  title: string;
}

export const DailyReturnsChart: React.FC<ChartProps> = ({ data, title }) => {
  // 自定义 Tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const date = new Date(label).toLocaleDateString();
      return (
        <div style={chartStyles.tooltip} className="p-2 shadow-lg">
          <p className="text-xs font-semibold text-gray-700 mb-1">{date}</p>
          {payload.map((p: any, i: number) => (
            <p key={i} className="text-xs" style={{ color: p.color }}>
              {p.name}: {(p.value * 100).toFixed(2)}%
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="flex flex-col h-full bg-white border border-gray-100 rounded-xl p-5">
      <h4 className="text-sm font-bold text-gray-700 mb-4 text-center">{title}</h4>
      <div className="flex-grow">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart 
            data={data} 
            margin={{ top: 10, right: 10, left: 10, bottom: 20 }}
            barGap={-14}
            barCategoryGap="25%"
          >
            <CartesianGrid vertical={false} {...chartStyles.grid} />
            <XAxis 
              dataKey="date" 
              tick={chartStyles.axis} 
              tickFormatter={formatDate} 
              minTickGap={30}
            />
            <YAxis {...chartStyles.axis} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}>
              <Label value="Daily Return (%)" angle={-90} position="insideLeft" style={chartStyles.label} offset={0} />
            </YAxis>
            <Tooltip content={<CustomTooltip />} />
            <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '10px' }} />
            {/* Benchmark 宽柱子在后 */}
            <Bar dataKey="benchmark" fill="#94a3b8" fillOpacity={0.5} name="Benchmark" barSize={14} radius={[2, 2, 0, 0]} />
            {/* Strategy 窄柱子在前，居中重叠 */}
            <Bar dataKey="portfolio" fill="#3b82f6" fillOpacity={0.9} name="Strategy" barSize={8} radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export const UnderwaterChart: React.FC<ChartProps> = ({ data, title }) => {
  // 自定义 Tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const date = new Date(label).toLocaleDateString();
      return (
        <div style={chartStyles.tooltip} className="p-2 shadow-lg">
          <p className="text-xs font-semibold text-gray-700 mb-1">{date}</p>
          {payload.map((p: any, i: number) => (
            <p key={i} className="text-xs" style={{ color: p.stroke }}>
              {p.name}: {(p.value * 100).toFixed(2)}%
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="flex flex-col h-full bg-white border border-gray-100 rounded-xl p-5">
      <h4 className="text-sm font-bold text-gray-700 mb-4 text-center">{title}</h4>
      <div className="flex-grow">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
            <CartesianGrid vertical={false} {...chartStyles.grid} />
            <XAxis 
              dataKey="date" 
              tick={chartStyles.axis} 
              tickFormatter={formatDate} 
              minTickGap={30}
            />
            <YAxis {...chartStyles.axis} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}>
              <Label value="Drawdown Depth (%)" angle={-90} position="insideLeft" style={chartStyles.label} offset={0} />
            </YAxis>
            <Tooltip content={<CustomTooltip />} />
            <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '10px' }} />
            {/* Benchmark 回撤 - 灰色虚线边框 */}
            <Area 
              type="step" 
              dataKey="benchmarkDrawdown" 
              stroke="#64748b" 
              strokeWidth={1.5}
              strokeDasharray="4 2"
              fill="#e2e8f0" 
              fillOpacity={0.3} 
              name="Benchmark" 
            />
            {/* Strategy 回撤 - 红色实线，更明显 */}
            <Area 
              type="step" 
              dataKey="drawdown" 
              stroke="#ef4444" 
              strokeWidth={2}
              fill="#fecaca" 
              fillOpacity={0.5} 
              name="Strategy" 
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export const RollingMetricChart: React.FC<ChartProps & { dataKey: string; benchmarkKey?: string; color: string; baseline?: number; yAxisLabel: string }> = ({ 
  data, title, dataKey, benchmarkKey, color, baseline, yAxisLabel 
}) => (
  <div className="flex flex-col h-full bg-white border border-gray-100 rounded-xl p-5">
    <h4 className="text-sm font-bold text-gray-700 mb-4 text-center">{title}</h4>
    <div className="flex-grow">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
          <CartesianGrid vertical={false} {...chartStyles.grid} />
          <XAxis 
            dataKey="date" 
            tick={chartStyles.axis} 
            tickFormatter={formatDate} 
            minTickGap={30}
          />
          <YAxis {...chartStyles.axis}>
            <Label value={yAxisLabel} angle={-90} position="insideLeft" style={chartStyles.label} offset={0} />
          </YAxis>
          <Tooltip contentStyle={chartStyles.tooltip} labelFormatter={(l) => new Date(l).toLocaleDateString()} />
          <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '10px' }} />
          {baseline !== undefined && <Line type="monotone" dataKey={() => baseline} stroke="#cbd5e1" strokeDasharray="5 5" dot={false} strokeWidth={1} name="Baseline" />}
          {benchmarkKey && <Line type="monotone" dataKey={benchmarkKey} stroke="#94a3b8" strokeWidth={1.5} strokeDasharray="3 3" dot={false} name="Benchmark" />}
          <Line type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2} dot={false} name="Strategy" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  </div>
);

export const BetaAnalysisChart: React.FC<ChartProps> = ({ data, title }) => {
  const points = data.filter(d => d.b_ret !== undefined && d.p_ret !== undefined);
  const xValues = points.map(d => d.b_ret);
  const yValues = points.map(d => d.p_ret);
  const n = points.length;
  const sumX = xValues.reduce((a, b) => a + b, 0);
  const sumY = yValues.reduce((a, b) => a + b, 0);
  const sumXY = points.reduce((a, b) => a + b.b_ret * b.p_ret, 0);
  const sumX2 = xValues.reduce((a, b) => a + b * b, 0);
  const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
  
  const minX = Math.min(...xValues);
  const maxX = Math.max(...xValues);
  const lineData = [
    { x: minX, y: slope * minX },
    { x: maxX, y: slope * maxX }
  ];

  return (
    <div className="flex flex-col h-full bg-white border border-gray-100 rounded-xl p-5">
      <h4 className="text-sm font-bold text-gray-700 mb-1 text-center">{title}</h4>
      <p className="text-[10px] text-blue-500 font-bold mb-3 text-center">Calculated Beta = {slope.toFixed(4)}</p>
      <div className="flex-grow relative">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 10, right: 20, bottom: 30, left: 20 }}>
            <CartesianGrid {...chartStyles.grid} />
            <XAxis type="number" dataKey="x" name="Benchmark" unit="%" {...chartStyles.axis}>
               <Label value="Benchmark (%)" position="insideBottom" offset={-15} style={chartStyles.label} />
            </XAxis>
            <YAxis type="number" dataKey="y" name="Returns" unit="%" {...chartStyles.axis}>
               <Label value="Returns (%)" angle={-90} position="insideLeft" style={chartStyles.label} offset={0} />
            </YAxis>
            <Tooltip contentStyle={chartStyles.tooltip} cursor={{ strokeDasharray: '3 3' }} />
            <Scatter name="Returns" data={points.map(d => ({ x: d.b_ret * 100, y: d.p_ret * 100 }))} fill="#3b82f6" fillOpacity={0.4} />
            <Line data={lineData.map(d => ({ x: d.x * 100, y: d.y * 100 }))} type="monotone" dataKey="y" stroke="#ef4444" strokeWidth={2} dot={false} />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};