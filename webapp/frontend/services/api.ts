import { API_BASE_URL } from '../constants';
import { 
  OverviewResponse, 
  EquityCurveResponse, 
  DrawdownResponse, 
  MonthlyResponse,
  ReturnsResponse,
  DailyReturn
} from '../types';

// 后端返回的原始格式
interface BackendEquityCurveResponse {
  period: string;
  portfolio: { date: string; value: number }[];
  benchmark: { date: string; value: number }[] | null;
}

interface BackendDrawdownResponse {
  period: string;
  current_drawdown: number;
  max_drawdown: number;
  drawdown_series: { date: string; drawdown: number }[];
  worst_drawdowns: {
    start_date: string;
    end_date: string | null;
    recovery_date: string | null;
    drawdown: number;
    duration: number;
    recovery_days: number | null;
  }[];
}

interface BackendReturnsResponse {
  period: string;
  metrics: any;
  daily_returns: { date: string; return: number }[];
}

async function fetchJson<T>(endpoint: string, params: Record<string, string> = {}): Promise<T> {
  const url = new URL(`${API_BASE_URL}${endpoint}`);
  Object.keys(params).forEach(key => {
    if (params[key]) {
      url.searchParams.append(key, params[key]);
    }
  });

  try {
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Failed to fetch ${endpoint}:`, error);
    throw error;
  }
}

// 转换 equity curve 数据格式：{ date, value }[] -> { [date]: value }[]
function transformEquityCurve(data: BackendEquityCurveResponse): EquityCurveResponse {
  return {
    period: data.period,
    portfolio: data.portfolio.map(p => ({ [p.date]: p.value })),
    benchmark: data.benchmark ? data.benchmark.map(b => ({ [b.date]: b.value })) : null,
  };
}

// 转换 drawdown 数据格式：{ date, drawdown }[] -> { [date]: drawdown }[]
function transformDrawdown(data: BackendDrawdownResponse): DrawdownResponse {
  return {
    period: data.period,
    current_drawdown: data.current_drawdown,
    max_drawdown: data.max_drawdown,
    drawdown_series: data.drawdown_series.map(d => ({ [d.date]: d.drawdown })),
    worst_drawdowns: data.worst_drawdowns,
  };
}

// 转换 returns 数据格式
function transformReturns(data: BackendReturnsResponse): ReturnsResponse {
  return {
    period: data.period,
    metrics: data.metrics,
    daily_returns: data.daily_returns.map(r => ({ date: r.date, return: r.return })),
  };
}

export const api = {
  getOverview: (period: string, benchmark: string): Promise<OverviewResponse> => 
    fetchJson<OverviewResponse>('/analytics/overview', { period, benchmark }),
    
  getEquityCurve: async (period: string, benchmark: string): Promise<EquityCurveResponse> => {
    const data = await fetchJson<BackendEquityCurveResponse>('/analytics/equity-curve', { period, benchmark });
    return transformEquityCurve(data);
  },
    
  getDrawdown: async (period: string): Promise<DrawdownResponse> => {
    const data = await fetchJson<BackendDrawdownResponse>('/analytics/drawdown', { period });
    return transformDrawdown(data);
  },
    
  getMonthly: (period: string): Promise<MonthlyResponse> => 
    fetchJson<MonthlyResponse>('/analytics/monthly', { period }),

  getReturns: async (period: string): Promise<ReturnsResponse> => {
    const data = await fetchJson<BackendReturnsResponse>('/analytics/returns', { period });
    return transformReturns(data);
  },
};
