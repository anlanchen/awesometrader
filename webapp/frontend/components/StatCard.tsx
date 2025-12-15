import React from 'react';
import { ArrowUpRight, ArrowDownRight, Activity } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subValue?: string;
  trend?: 'up' | 'down' | 'neutral';
  icon?: React.ReactNode;
  className?: string;
}

export const StatCard: React.FC<StatCardProps> = ({ title, value, subValue, trend, icon, className }) => {
  const trendColor = trend === 'up' ? 'text-green-500' : trend === 'down' ? 'text-red-500' : 'text-gray-500';
  
  return (
    <div className={`bg-white rounded-xl p-6 shadow-sm border border-gray-100 ${className}`}>
      <div className="flex justify-between items-start">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <h3 className="text-2xl font-bold text-gray-900 mt-2">{value}</h3>
          {subValue && (
            <p className={`text-sm mt-1 flex items-center ${trendColor}`}>
              {trend === 'up' && <ArrowUpRight className="w-4 h-4 mr-1" />}
              {trend === 'down' && <ArrowDownRight className="w-4 h-4 mr-1" />}
              {subValue}
            </p>
          )}
        </div>
        <div className="p-2 bg-gray-50 rounded-lg text-gray-600">
          {icon || <Activity className="w-5 h-5" />}
        </div>
      </div>
    </div>
  );
};