import React, { useState, useEffect, useMemo } from 'react';
import { MonthlyResponse, EquityCurveResponse } from '../types';
import { Calendar } from 'lucide-react';

interface MonthlyHeatmapProps {
  data: MonthlyResponse | null;
  equityData: EquityCurveResponse | null;
  initialValue: number; // Added to calculate absolute P&L
}

const formatCurrencyCompact = (value: number) => {
  // Requirement: Use RMB symbol, unit in 'k' (thousands), 2 decimal places
  const inK = value / 1000;
  return `¥${inK.toFixed(2)}k`;
};

export const MonthlyHeatmap: React.FC<MonthlyHeatmapProps> = ({ data, equityData, initialValue }) => {
  const [selectedYear, setSelectedYear] = useState<number | null>(null);
  const [selectedMonth, setSelectedMonth] = useState<number | null>(null);

  // --- Data Processing: Calculate P&L for Years and Months ---
  const pnlData = useMemo(() => {
    if (!data) return { yearly: {}, monthly: {} };

    const sortedReturns = [...data.monthly_returns].sort((a, b) => 
      (a.year - b.year) || (a.month - b.month)
    );

    let currentValue = initialValue;
    const monthlyPnLs: Record<string, number> = {}; 
    const yearlyPnLs: Record<string, number> = {}; 

    sortedReturns.forEach(m => {
      const startVal = currentValue;
      const endVal = startVal * (1 + m.return_value);
      const pnl = endVal - startVal;
      
      currentValue = endVal;
      monthlyPnLs[`${m.year}-${m.month}`] = pnl;

      if (!yearlyPnLs[m.year]) yearlyPnLs[m.year] = 0;
      yearlyPnLs[m.year] += pnl;
    });

    return { yearly: yearlyPnLs, monthly: monthlyPnLs };
  }, [data, initialValue]);

  // Initialize selection
  useEffect(() => {
    if (data && data.monthly_returns.length > 0) {
      const years = Array.from(new Set(data.monthly_returns.map(m => m.year))).sort((a: number, b: number) => b - a);
      const latestYear = years[0];
      
      if (!selectedYear || !years.includes(selectedYear)) {
        setSelectedYear(latestYear);
        const monthsInYear = data.monthly_returns
          .filter(m => m.year === latestYear)
          .map(m => m.month)
          .sort((a, b) => b - a);
          
        if (monthsInYear.length > 0) setSelectedMonth(monthsInYear[0]);
        else setSelectedMonth(1); 
      }
    }
  }, [data, selectedYear]);

  const getColor = (value: number | undefined, isSelected: boolean = false) => {
    if (value === undefined || value === null) return isSelected ? 'bg-gray-50 ring-2 ring-blue-500' : 'bg-gray-50 text-gray-300';
    
    let baseColor = '';
    if (value === 0) baseColor = 'bg-gray-100 text-gray-500';
    else if (value > 0) {
      if (value >= 0.05) baseColor = 'bg-green-600 text-white';
      else if (value >= 0.02) baseColor = 'bg-green-500 text-white';
      else baseColor = 'bg-green-100 text-green-800';
    } else {
      if (value <= -0.05) baseColor = 'bg-red-600 text-white';
      else if (value <= -0.02) baseColor = 'bg-red-500 text-white';
      else baseColor = 'bg-red-100 text-red-800';
    }

    if (isSelected) {
        return `${baseColor} ring-2 ring-offset-1 ring-blue-500 shadow-md transform scale-105 z-10`;
    }
    return `${baseColor} hover:opacity-90`;
  };

  if (!data) return null;

  const years = Array.from(new Set(data.monthly_returns.map(m => m.year))).sort((a: number, b: number) => b - a);
  const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const getMonthlyReturn = (y: number, m: number) => 
    data.monthly_returns.find(item => item.year === y && item.month === m)?.return_value;

  const renderDailyCalendar = () => {
    if (!equityData || !equityData.portfolio || !selectedYear || !selectedMonth) return null;

    const allPoints = equityData.portfolio.flatMap(p => {
        const date = Object.keys(p)[0];
        return { date, value: p[date] };
    }).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

    const dailyData = allPoints.map((pt, i) => {
        if (i === 0) return { ...pt, pct: 0, pnl: 0 };
        const prev = allPoints[i-1];
        const pct = (pt.value / prev.value) - 1;
        const pnl = (pt.value - prev.value) * initialValue; 
        return { ...pt, pct, pnl };
    });

    const monthDailyData = dailyData.filter(pt => {
        const d = new Date(pt.date);
        return d.getFullYear() === selectedYear && d.getMonth() === (selectedMonth - 1); 
    });

    const daysInMonth = new Date(selectedYear, selectedMonth, 0).getDate();
    const firstDayOfWeek = new Date(selectedYear, selectedMonth - 1, 1).getDay(); // 0=Sun
    
    const blanks = Array(firstDayOfWeek).fill(null);
    const days = Array.from({ length: daysInMonth }, (_, i) => i + 1);
    const totalSlots = [...blanks, ...days];
    const weekDays = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];

    return (
      <div className="flex flex-col h-full animate-fade-in">
         <div className="flex-none flex items-center gap-2 mb-3 text-sm text-gray-500 font-medium">
            <Calendar className="w-4 h-4" />
            <span>Daily Returns: {monthNames[selectedMonth - 1]} {selectedYear}</span>
         </div>
         
         {/* Grid Container - No fixed height/scroll */}
         <div className="grid grid-cols-7 gap-1.5 auto-rows-min">
            {weekDays.map(d => (
                <div key={d} className="text-[10px] text-center text-gray-400 font-semibold uppercase mb-1">{d}</div>
            ))}
            {totalSlots.map((day, idx) => {
                if (!day) return <div key={`blank-${idx}`} className="h-[70px]"></div>;
                
                const dayItem = monthDailyData.find(d => new Date(d.date).getDate() === day);
                const val = dayItem?.pct;
                const pnl = dayItem?.pnl || 0;
                const hasData = val !== undefined;

                return (
                    <div 
                        key={day}
                        className={`h-[70px] rounded-md flex flex-col items-center justify-center p-1 text-[10px] transition-all cursor-default group relative ${getColor(val)}`}
                    >
                        <span className={`font-bold text-[9px] ${hasData ? 'opacity-60' : 'opacity-40'}`}>{day}</span>
                        {hasData && (
                            <>
                                <span className="font-bold tracking-tighter leading-none scale-95 mt-1">
                                    {val! > 0 ? '+' : ''}{(val! * 100).toFixed(2)}%
                                </span>
                                <span className="font-mono text-[9px] leading-none mt-1 opacity-90">
                                    {pnl >= 0 ? '+' : ''}{formatCurrencyCompact(pnl)}
                                </span>
                            </>
                        )}
                        
                        {hasData && (
                            <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 hidden group-hover:block z-50 whitespace-nowrap bg-gray-900 text-white text-xs rounded px-2 py-1 pointer-events-none shadow-lg">
                                <div className="font-bold">{new Date(dayItem!.date).toLocaleDateString()}</div>
                                <div className={`${val! >= 0 ? 'text-green-300' : 'text-red-300'}`}>
                                    {(val! * 100).toFixed(2)}%
                                </div>
                                <div className="text-gray-300 font-mono">
                                    {pnl >= 0 ? '+' : ''}{formatCurrencyCompact(pnl)}
                                </div>
                            </div>
                        )}
                    </div>
                );
            })}
         </div>
      </div>
    );
  };

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col min-h-full">
      <div className="flex-none flex justify-between items-center mb-4">
        <h3 className="text-lg font-bold text-gray-800">Performance Heatmap</h3>
      </div>

      {/* 1. Year Selector */}
      <div className="flex-none mb-4">
        <div className="flex-none flex items-center gap-2 mb-3 text-sm text-gray-500 font-medium">
            <Calendar className="w-4 h-4" />
            <span>Yearly Returns</span>
        </div>
        <div className="grid grid-cols-3 gap-2">
            {years.map(year => {
                const ytdObj = data.yearly_returns.find(item => Object.keys(item)[0] === year.toString());
                const ytd = ytdObj ? ytdObj[year.toString()] : 0;
                const pnl = pnlData.yearly[year] || 0;
                const isSelected = selectedYear === year;

                return (
                    <button
                        key={year}
                        onClick={() => { setSelectedYear(year); setSelectedMonth(null); }}
                        className={`
                            px-2 py-2 rounded-lg border transition-all flex flex-col h-14
                            ${isSelected 
                                ? 'border-blue-500 bg-blue-50 ring-1 ring-blue-500' 
                                : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'}
                        `}
                    >
                        <div className="flex items-center justify-between w-full">
                             <span className={`text-xs font-bold ${isSelected ? 'text-blue-700' : 'text-gray-600'}`}>{year}</span>
                             <span className={`text-xs font-bold ${ytd >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {ytd > 0 ? '+' : ''}{(ytd * 100).toFixed(2)}%
                             </span>
                        </div>
                        <div className={`w-full text-right text-[10px] font-mono mt-auto ${pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                             {pnl > 0 ? '+' : ''}{formatCurrencyCompact(pnl)}
                        </div>
                    </button>
                );
            })}
        </div>
      </div>

      {/* 2. Monthly Grid - 3 Columns */}
      {selectedYear && (
          <div className="flex-none mb-4 border-b border-gray-100 pb-4">
            <div className="flex-none flex items-center gap-2 mb-3 text-sm text-gray-500 font-medium">
                <Calendar className="w-4 h-4" />
                <span>Monthly Returns</span>
            </div>
            <div className="grid grid-cols-3 gap-2">
                {monthNames.map((name, idx) => {
                    const monthNum = idx + 1;
                    const val = getMonthlyReturn(selectedYear, monthNum);
                    const pnl = pnlData.monthly[`${selectedYear}-${monthNum}`] || 0;
                    const isSelected = selectedMonth === monthNum;
                    
                    return (
                        <button 
                            key={monthNum}
                            onClick={() => setSelectedMonth(monthNum)}
                            className={`
                                h-12 rounded-lg flex flex-col px-2 transition-all relative
                                ${getColor(val, isSelected)}
                            `}
                        >
                            <div className="flex justify-between w-full items-baseline mt-1">
                                <span className={`text-[10px] font-bold uppercase ${val !== undefined ? (Math.abs(val) > 0.02 ? 'text-white/90' : 'text-gray-600') : ''}`}>
                                    {name}
                                </span>
                                <span className={`text-[10px] font-bold ${val !== undefined ? 'opacity-100' : 'opacity-0'}`}>
                                    {val !== undefined ? `${(val * 100).toFixed(2)}%` : '-'}
                                </span>
                            </div>
                            {val !== undefined && (
                                <div className={`w-full text-right text-[9px] font-mono leading-none mt-auto mb-1 ${Math.abs(val) > 0.02 ? 'text-white/90' : 'text-gray-500'}`}>
                                     {pnl > 0 ? '+' : ''}{formatCurrencyCompact(pnl)}
                                </div>
                            )}
                        </button>
                    );
                })}
            </div>
          </div>
      )}

      {/* 3. Daily Calendar - Grows to fill space */}
      <div className="flex-grow">
        {renderDailyCalendar()}
      </div>
    </div>
  );
};