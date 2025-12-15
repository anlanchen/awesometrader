import React from 'react';
import { OverviewResponse } from '../types';

interface RiskMetricsProps {
  data: OverviewResponse | null;
}

const TableRow = ({ 
  label, 
  value, 
  isPercent = false, 
  inverse = false, 
  format = 'number'
}: { 
  label: string, 
  value: number | string | null | undefined, 
  isPercent?: boolean, 
  inverse?: boolean,
  format?: 'number' | 'string'
}) => {
  if (value === undefined || value === null) return null;
  
  let formattedValue: React.ReactNode = value;
  let colorClass = "text-gray-900";

  if (format === 'number' && typeof value === 'number') {
      const numVal = value as number;
      formattedValue = isPercent ? `${(numVal * 100).toFixed(2)}%` : numVal.toFixed(2);
      
      // Coloring Logic
      // Positive is usually Green, Negative is Red
      // Inverse: Positive is Red (e.g. Drawdown if represented as positive number, but usually it's negative)
      // Here Drawdown is negative in data (-0.14), so < 0 is Bad (Red). 
      
      if (numVal > 0) colorClass = inverse ? "text-red-600" : "text-green-600";
      if (numVal < 0) colorClass = inverse ? "text-green-600" : "text-red-600";
      
      // Neutral Stats
      if (label.includes("Duration") || label.includes("Error") || label.includes("Vol")) {
         // Volatility is often neutral or bad if high, but let's keep it neutral for now or use logic
         colorClass = "text-gray-900";
      }

      // Specific overrides
      if (label === 'Max Drawdown') colorClass = "text-red-600"; // Always red
      if (label.includes('VaR')) colorClass = "text-red-600";
  }

  return (
    <tr className="border-b border-gray-100 hover:bg-gray-50 transition-colors last:border-0 group">
      <td className="py-3 pl-4 pr-3 text-sm font-medium text-gray-500 w-1/2 group-hover:text-gray-700">{label}</td>
      <td className={`py-3 pl-3 pr-4 text-sm font-bold font-mono text-right ${colorClass}`}>
        {formattedValue}
      </td>
    </tr>
  );
};

export const RiskMetrics: React.FC<RiskMetricsProps> = ({ data }) => {
  if (!data) return <div className="h-64 animate-pulse bg-gray-100 rounded-xl"></div>;

  // Split metrics into two columns
  const leftColumnData = [
    { label: 'Start Period', value: data.start_date, format: 'string' },
    { label: 'End Period', value: data.end_date, format: 'string' },
    { label: 'Risk-Free Rate', value: '0.0%', format: 'string' },
    { label: 'Time in Market', value: '100%', format: 'string' },
    { label: 'Cumulative Return', value: data.returns.cumulative_return, isPercent: true },
    { label: 'CAGR%', value: data.returns.annualized_return, isPercent: true },
    { label: 'Sharpe', value: data.risk.sharpe_ratio },
    { label: 'Sortino', value: data.risk.sortino_ratio },
    { label: 'Calmar', value: data.risk.calmar_ratio },
    { label: 'Max Drawdown', value: data.risk.max_drawdown, isPercent: true, inverse: true },
    { label: 'Longest DD Days', value: data.risk.max_drawdown_duration, format: 'number' },
    { label: 'Volatility (ann.)', value: data.risk.volatility, isPercent: true },
    { label: 'Skew', value: data.risk.skewness },
    { label: 'Kurtosis', value: data.risk.kurtosis },
  ];

  const rightColumnData = [
    { label: 'Daily VaR (95%)', value: data.risk.var_95, isPercent: true, inverse: true },
    { label: 'Daily cVaR (95%)', value: data.risk.cvar_95, isPercent: true, inverse: true },
    { label: 'Best Day', value: data.returns.best_day, isPercent: true },
    { label: 'Worst Day', value: data.returns.worst_day, isPercent: true, inverse: true },
    { label: 'Win Rate', value: data.returns.win_rate, isPercent: true },
    { label: 'MTD', value: data.returns.mtd_return, isPercent: true },
    { label: 'YTD', value: data.returns.ytd_return, isPercent: true },
    { label: 'Alpha', value: data.benchmark?.alpha },
    { label: 'Beta', value: data.benchmark?.beta },
    { label: 'Correlation', value: data.benchmark?.correlation },
    { label: 'Tracking Error', value: data.benchmark?.tracking_error, isPercent: true },
    { label: 'Information Ratio', value: data.benchmark?.information_ratio },
    { label: 'Up Capture', value: data.benchmark?.up_capture },
    { label: 'Down Capture', value: data.benchmark?.down_capture },
  ];

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
       {/* Responsive Grid: 1 col on mobile, 2 cols on md+ */}
      <div className="grid grid-cols-1 md:grid-cols-2">
        {/* Left Column */}
        <div className="border-r border-gray-100">
           <table className="w-full">
            <tbody>
                {leftColumnData.map((item, idx) => (
                    // @ts-ignore
                    <TableRow key={`l-${idx}`} {...item} />
                ))}
            </tbody>
           </table>
        </div>
        
        {/* Right Column */}
        <div>
           <table className="w-full border-t md:border-t-0 border-gray-100">
            <tbody>
                {rightColumnData.map((item, idx) => (
                    // @ts-ignore
                    <TableRow key={`r-${idx}`} {...item} />
                ))}
            </tbody>
           </table>
        </div>
      </div>
    </div>
  );
};