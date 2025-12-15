import { API_BASE_URL } from '../constants';

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

export const api = {
  getOverview: (period: string, benchmark: string) => 
    fetchJson<any>('/analytics/overview', { period, benchmark }),
    
  getEquityCurve: (period: string, benchmark: string) => 
    fetchJson<any>('/analytics/equity-curve', { period, benchmark }),
    
  getDrawdown: (period: string) => 
    fetchJson<any>('/analytics/drawdown', { period }),
    
  getMonthly: (period: string) => 
    fetchJson<any>('/analytics/monthly', { period }),
};
