
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
  benchmark: BenchmarkMetrics | null;
  advanced_metrics?: Record<string, number>; // Flexible map for the extended metrics list
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
  avg_win: number;
  avg_loss: number;
  profit_factor: number;
  payoff_ratio: number;
  expectancy: number;
  geometric_mean: number;
  expected_monthly: number;
  expected_yearly: number;
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
  ulcer_index: number;
  tail_ratio: number;
  kelly_criterion: number;
  omega_ratio: number;
  gain_to_pain_ratio: number;
  common_sense_ratio: number;
  recovery_factor: number;
  risk_return_ratio: number;
  ulcer_performance_index: number;
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
  r2?: number; // 后端不返回此字段
}

// 完整的基准指标（包含收益、风险和对比指标）
export interface BenchmarkMetrics {
  benchmark_name: string;
  // 收益指标
  benchmark_return: number;
  benchmark_cagr: number;
  benchmark_daily_mean: number;
  benchmark_daily_std: number;
  benchmark_best_day: number;
  benchmark_worst_day: number;
  benchmark_win_rate: number;
  benchmark_avg_win: number;
  benchmark_avg_loss: number;
  benchmark_profit_factor: number;
  benchmark_payoff_ratio: number;
  benchmark_expectancy: number;
  benchmark_geometric_mean: number;
  benchmark_expected_monthly: number;
  benchmark_expected_yearly: number;
  // 风险指标
  benchmark_volatility: number;
  benchmark_max_drawdown: number;
  benchmark_sharpe: number;
  benchmark_sortino: number;
  benchmark_calmar: number;
  benchmark_var_95: number;
  benchmark_cvar_95: number;
  benchmark_skewness: number;
  benchmark_kurtosis: number;
  benchmark_ulcer_index: number;
  benchmark_tail_ratio: number;
  benchmark_kelly_criterion: number;
  benchmark_omega_ratio: number;
  benchmark_gain_to_pain_ratio: number;
  benchmark_common_sense_ratio: number;
  benchmark_recovery_factor: number;
  benchmark_risk_return_ratio: number;
  benchmark_ulcer_performance_index: number;
  // 对比指标
  alpha: number;
  beta: number;
  correlation: number;
  information_ratio: number;
  tracking_error: number;
  up_capture: number;
  down_capture: number;
}

export interface EquityCurvePoint {
  date?: string; 
  [key: string]: any; 
}

export interface EquityCurveResponse {
  period: string;
  portfolio: Record<string, number>[];
  benchmark: Record<string, number>[] | null;
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

export interface SelectOption {
  label: string;
  value: string;
}

// 每日收益率数据点
export interface DailyReturn {
  date: string;
  return: number;
}

// 收益分析响应
export interface ReturnsResponse {
  period: string;
  metrics: ReturnMetrics;
  daily_returns: DailyReturn[];
}

// 图表使用的时间序列数据
export interface ChartSeriesData {
  date: string;
  portfolio: number;        // 组合日收益率
  benchmark: number;        // 基准日收益率
  drawdown: number;         // 组合回撤
  benchmarkDrawdown: number; // 基准回撤
  beta: number;             // 滚动 Beta
  benchmarkBeta: number;    // 基准 Beta (=1)
  vol: number;              // 滚动波动率
  benchmarkVol: number;     // 基准滚动波动率
  sharpe: number;           // 滚动夏普
  benchmarkSharpe: number;  // 基准滚动夏普
  sortino: number;          // 滚动索提诺
  benchmarkSortino: number; // 基准滚动索提诺
  b_ret: number;            // 基准日收益（用于Beta散点图）
  p_ret: number;            // 组合日收益（用于Beta散点图）
}
