import { SelectOption } from './types';

// API Configuration
// Assuming the backend is running on localhost:8000. 
// In production, this would be an environment variable.
export const API_BASE_URL = 'http://localhost:8000/api';

export const PERIOD_OPTIONS: SelectOption[] = [
  { label: '7D', value: '7d' },
  { label: '1M', value: '1m' },
  { label: '6M', value: '6m' },
  { label: '1Y', value: '1y' },
  { label: 'YTD', value: 'ytd' },
  { label: 'MTD', value: 'mtd' },
  { label: 'All', value: 'all' },
];

export const BENCHMARK_OPTIONS: SelectOption[] = [
  { label: '标普500', value: 'sp500' },
  { label: '纳斯达克100', value: 'nasdaq100' },
  { label: '沪深300', value: 'csi300' },
  { label: '中证500ETF', value: 'a500' },
  { label: '恒生科技ETF', value: 'hstech' },
];