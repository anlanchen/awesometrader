import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subValue?: string;
  trend?: 'up' | 'down' | 'neutral';
  icon?: React.ReactNode;
  className?: string;
  iconBgColor?: string;
}

export const StatCard: React.FC<StatCardProps> = ({ 
  title, 
  value, 
  subValue, 
  trend, 
  icon, 
  className,
  iconBgColor = 'bg-blue-50'
}) => {
  const isUp = trend === 'up';
  const isDown = trend === 'down';
  const isNeutral = trend === 'neutral';
  
  // Colors based on the screenshot provided
  const trendColor = isUp ? 'text-emerald-500' : isDown ? 'text-rose-500' : 'text-slate-400';
  
  return (
    <div className={`bg-white rounded-2xl p-6 shadow-sm border border-gray-100 flex justify-between items-center transition-all hover:shadow-md ${className}`}>
      <div className="flex flex-col gap-1">
        {/* Title Case requested: removed 'uppercase' */}
        <p className="text-[13px] font-bold text-gray-400 tracking-tight">{title}</p>
        <h3 className="text-3xl font-extrabold text-slate-900 tracking-tight my-1">{value}</h3>
        {subValue && (
          <div className={`flex items-center gap-1.5 text-sm font-bold ${trendColor}`}>
            {isUp && <TrendingUp className="w-4 h-4 stroke-[3]" />}
            {isDown && <TrendingDown className="w-4 h-4 stroke-[3]" />}
            {isNeutral && <Minus className="w-4 h-4 stroke-[3]" />}
            <span>{subValue}</span>
          </div>
        )}
      </div>
      
      <div className={`flex-shrink-0 w-14 h-14 flex items-center justify-center rounded-2xl ${iconBgColor}`}>
        {icon}
      </div>
    </div>
  );
};