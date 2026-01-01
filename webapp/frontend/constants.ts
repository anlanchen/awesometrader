import { SelectOption } from './types';

// API Configuration
// 使用相对路径，自动适配当前域名（内网穿透等场景）
// 开发环境需要配置 vite proxy，或者前后端同源部署
export const API_BASE_URL = '/api';

export const PERIOD_OPTIONS: SelectOption[] = [
  { label: '7D', value: '7d' },
  { label: '1M', value: '1m' },
  { label: '6M', value: '6m' },
  { label: '1Y', value: '1y' },
  { label: 'MTD', value: 'mtd' },
  { label: 'YTD', value: 'ytd' },
  { label: 'All', value: 'all' },
];

export const BENCHMARK_OPTIONS: SelectOption[] = [
  { label: '标普500', value: 'sp500' },
  { label: '纳斯达克100', value: 'nasdaq100' },
  { label: '沪深300', value: 'csi300' },
  { label: '中证A500', value: 'a500' },
  { label: '恒生科技', value: 'hstech' },
];