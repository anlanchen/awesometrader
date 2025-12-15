// API Response Types based on JSON Schema

export interface OverviewResponse {
  period: string;
  start_date: string;
  end_date: string;
  trading_days: number;
  initial_value: number;
  final_value: number;
  returns: ReturnMetrics;
  risk: RiskMetrics;
  benchmark: BenchmarkComparison | null;
}

export interface ReturnMetrics {
  cumulative_return: number;
  annualized_return: number;
  ytd_return: number | null;
  mtd_return: number | null;
  daily_return_mean: number;
  daily_return_std: number;
  best_day: number;
  worst_day: number;
  win_rate: number;
}

export interface RiskMetrics {
  volatility: number;
  max_drawdown: number;
  max_drawdown_duration: number | null;
  sharpe_ratio: number;
  sortino_ratio: number;
  calmar_ratio: number;
  var_95: number;
  cvar_95: number;
  skewness: number;
  kurtosis: number;
}

export interface BenchmarkComparison {
  benchmark_name: string;
  benchmark_return: number;
  alpha: number;
  beta: number;
  correlation: number;
  information_ratio: number;
  tracking_error: number;
  up_capture: number;
  down_capture: number;
}

export interface EquityCurvePoint {
  date: string;
  value: number;
}

export interface EquityCurveResponse {
  period: string;
  portfolio: EquityCurvePoint[];
  benchmark: EquityCurvePoint[] | null;
}

export interface DrawdownInfo {
  start_date: string;
  end_date: string | null;
  recovery_date: string | null;
  drawdown: number;
  duration: number;
  recovery_days: number | null;
}

export interface DrawdownResponse {
  period: string;
  current_drawdown: number;
  max_drawdown: number;
  drawdown_series: Record<string, number>[];
  worst_drawdowns: DrawdownInfo[];
}

export interface MonthlyReturn {
  year: number;
  month: number;
  return_value: number;
}

export interface MonthlyResponse {
  period: string;
  monthly_returns: MonthlyReturn[];
  yearly_returns: Record<string, number>[];
}

// Frontend Constants Types
export interface SelectOption {
  label: string;
  value: string;
}
