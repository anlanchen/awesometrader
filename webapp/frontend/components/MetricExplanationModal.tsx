import React from 'react';
import { Info } from 'lucide-react';

interface MetricExplanation {
  name: string;
  definition: string;
  calculation: string;
  interpretation: string;
}

const explanations: Record<string, MetricExplanation> = {
  // Returns Summary
  'Cumulative Return': {
    name: '累计收益率 (Cumulative Return)',
    definition: '投资期内资产净值的总增长率。',
    calculation: '(期末价值 - 期初价值) / 期初价值',
    interpretation: '衡量投资期间的绝对盈利能力。'
  },
  'CAGR%': {
    name: '复合年化增长率 (CAGR)',
    definition: '将投资收益简化为一个固定的年度收益率。',
    calculation: '[(期末价值 / 期初价值) ^ (1 / 年数)] - 1',
    interpretation: '用于比较不同周期的表现，消除了时间长度的影响。'
  },
  'Geometric Mean': {
    name: '几何平均值 (Geometric Mean)',
    definition: '考虑复利效应后的平均日收益。',
    calculation: 'n次根号下(所有(1+Ri)的乘积) - 1',
    interpretation: '比算术平均值更准确地反映资金实际增长速度。'
  },
  'Expected Daily Return': {
    name: '期望日收益 (Expected Daily Return)',
    definition: '基于历史数据的平均每日预期回报。',
    calculation: '所有日收益之和 / 交易天数',
    interpretation: '代表策略每日的平均表现水平。'
  },
  'Expected Monthly Return': {
    name: '期望月收益 (Expected Monthly Return)',
    definition: '基于历史数据的平均每月预期回报。',
    calculation: '期望日收益 * 21 (典型交易日)',
    interpretation: '提供中期的表现预期。'
  },
  'Expected Yearly Return': {
    name: '期望年收益 (Expected Yearly Return)',
    definition: '基于历史数据的平均每年预期回报。',
    calculation: '期望日收益 * 252 (典型交易日)',
    interpretation: '长期的回报基准预期。'
  },

  // Performance Metrics
  'Avg Win': {
    name: '平均盈利 (Avg Win)',
    definition: '所有盈利交易日的平均收益率。',
    calculation: '所有正收益之和 / 盈利天数',
    interpretation: '反映在赚钱时的平均获利强度。'
  },
  'Avg Loss': {
    name: '平均亏损 (Avg Loss)',
    definition: '所有亏损交易日的平均跌幅。',
    calculation: '所有负收益之和 / 亏损天数',
    interpretation: '反映在亏损时的平均受损程度。'
  },
  'Avg Return': {
    name: '平均收益 (Avg Return)',
    definition: '所有交易日的简单算术平均收益。',
    calculation: '所有收益之和 / 总天数',
    interpretation: '衡量策略的基本盈利能力。'
  },
  'Win Rate': {
    name: '胜率 (Win Rate)',
    definition: '盈利天数占总交易天数的比例。',
    calculation: '盈利天数 / 总交易天数',
    interpretation: '衡量策略盈利的频率。'
  },
  'Profit Factor': {
    name: '利润因子 (Profit Factor)',
    definition: '总盈利与总亏损的比值。',
    calculation: '总盈利额 / 总亏损额的绝对值',
    interpretation: '值大于1表示盈利，1.5以上被认为具有较好的健壮性。'
  },
  'Payoff Ratio': {
    name: '盈亏比 (Payoff Ratio)',
    definition: '平均盈利与平均亏损的比值。',
    calculation: '平均盈利 / 平均亏损的绝对值',
    interpretation: '反映获利规模与风险规模的关系。'
  },
  'Best Day': {
    name: '最高单日涨幅 (Best Day)',
    definition: '统计周期内收益率最高的一天。',
    calculation: 'max(Daily Returns)',
    interpretation: '揭示策略在最佳市场情况下的爆发力。'
  },
  'Worst Day': {
    name: '最大单日跌幅 (Worst Day)',
    definition: '统计周期内收益率最低的一天。',
    calculation: 'min(Daily Returns)',
    interpretation: '揭示策略在极端不利情况下的瞬时风险。'
  },
  'Consecutive Wins': {
    name: '最大连续盈利天数 (Consecutive Wins)',
    definition: '历史上最长的连续上涨天数。',
    calculation: '最大连续正收益天数',
    interpretation: '反映策略的连贯顺境能力。'
  },
  'Consecutive Losses': {
    name: '最大连续亏损天数 (Consecutive Losses)',
    definition: '历史上最长的连续下跌天数。',
    calculation: '最大连续负收益天数',
    interpretation: '揭示策略可能面临的最长低迷期。'
  },
  'Outlier Win Ratio': {
    name: '离群盈利比 (Outlier Win Ratio)',
    definition: '极端盈利日相对于普通盈利日的倍数。',
    calculation: '最大盈利 / 中位数盈利',
    interpretation: '衡量盈利是否过度依赖少数几个幸运日。'
  },
  'Outlier Loss Ratio': {
    name: '离群亏损比 (Outlier Loss Ratio)',
    definition: '极端亏损日相对于普通亏损日的倍数。',
    calculation: '最大亏损 / 中位数亏损',
    interpretation: '衡量风险是否表现为突发的黑天鹅事件。'
  },

  // Risk & Volatility
  'Max Drawdown': {
    name: '最大回撤 (Max Drawdown)',
    definition: '资产净值从最高点到最低点的最大跌幅。',
    calculation: '(谷值 - 峰值) / 峰值',
    interpretation: '衡量最糟糕情况下的资产风险，通常越小越好。'
  },
  'Volatility (ann.)': {
    name: '年化波动率 (Volatility)',
    definition: '资产收益率的波动程度。',
    calculation: '日收益率标准差 * sqrt(252)',
    interpretation: '波动率越高，代表资产价格的不确定性和风险越大。'
  },
  'Implied Volatility': {
    name: '隐含波动率 (Implied Volatility)',
    definition: '市场对未来波动率的预期（通常来自期权定价）。',
    calculation: '期权模型反推得到的波动率参数',
    interpretation: '反映了市场对未来风险的担忧程度。'
  },
  'Ulcer Index': {
    name: '溃疡指数 (Ulcer Index)',
    definition: '衡量价格回撤的深度和持续时间带来的心理压力。',
    calculation: 'sqrt(所有回撤平方的平均值)',
    interpretation: '数值越低，代表投资过程越平稳，“心累”程度越低。'
  },
  'Skew': {
    name: '偏度 (Skewness)',
    definition: '收益分布的不对称程度。',
    calculation: '三阶标准矩',
    interpretation: '负偏表示极端亏损的可能性大于极端盈利。'
  },
  'Kurtosis': {
    name: '峰度 (Kurtosis)',
    definition: '收益分布的尖锐程度和“肥尾”效应。',
    calculation: '四阶标准矩',
    interpretation: '高峰度意味着发生极端（黑天鹅）事件的频率更高。'
  },
  'Risk of Ruin': {
    name: '破产风险 (Risk of Ruin)',
    definition: '账户资金减少到无法继续交易的概率。',
    calculation: '基于胜率和赔率的概率模型',
    interpretation: '必须极力避免破产风险。'
  },
  'Value at Risk (95%)': {
    name: '在险价值 (VaR 95%)',
    definition: '在正常市场波动下，95%的概率下最大单日损失不会超过该值。',
    calculation: '收益率分布的第5百分位数',
    interpretation: '常用的风险控制指标。'
  },
  'cVaR / Expected Shortfall': {
    name: '条件在险价值 (cVaR)',
    definition: '如果发生了超出VaR的极端损失，那这些损失的平均值是多少。',
    calculation: '低于VaR阈值的所有收益的平均值',
    interpretation: '比VaR更关注“尾部极端风险”。'
  },
  'Tail Ratio': {
    name: '尾部比率 (Tail Ratio)',
    definition: '衡量极端盈利相对于极端亏损的能力。',
    calculation: '95分位收益 / |5分位收益|',
    interpretation: '大于1表示盈利分布比亏损分布更具优势。'
  },
  'Exposure': {
    name: '敞口 (Exposure)',
    definition: '资金在市场中面临波动的百分比。',
    calculation: '持仓市值 / 总资产',
    interpretation: '反映了策略的仓位进取程度。'
  },

  // Risk Adjusted
  'Sharpe Ratio': {
    name: '夏普比率 (Sharpe Ratio)',
    definition: '每承担一单位总风险所获得的超额收益。',
    calculation: '(年化收益 - 无风险利率) / 年化波动率',
    interpretation: '衡量风险调整后的收益，通常>1较好。'
  },
  'Sortino Ratio': {
    name: '索提诺比率 (Sortino Ratio)',
    definition: '每承担一单位下行风险所获得的超额收益。',
    calculation: '(年化收益 - 无风险利率) / 下行标准差',
    interpretation: '对投资者更有意义，因为它不惩罚向上的波动。'
  },
  'Adjusted Sortino': {
    name: '修正索提诺比率 (Adjusted Sortino)',
    definition: '对标准索提诺比率进行的修正，以更好地处理分布不均。',
    calculation: 'Sortino / sqrt(2)',
    interpretation: '更保守的风险评估。'
  },
  'Calmar Ratio': {
    name: '卡玛比率 (Calmar Ratio)',
    definition: '年化收益率与最大回撤的比值。',
    calculation: '年化收益率 / 最大回撤的绝对值',
    interpretation: '衡量用多少回撤换取了多少收益，适合评估长期策略。'
  },
  'Omega Ratio': {
    name: '欧米伽比率 (Omega Ratio)',
    definition: '超过目标收益的概率权重与低于目标收益的概率权重的比。',
    calculation: '积分(收益分布中高于阈值部分) / 积分(低于阈值部分)',
    interpretation: '全面考虑了收益分布的所有信息。'
  },
  'Gain to Pain Ratio': {
    name: '增益/痛苦比 (Gain to Pain)',
    definition: '累计收益与累计亏损绝对值的比。',
    calculation: '总收益 / |总亏损|',
    interpretation: '杰克·施瓦格提出的指标，衡量投资过程的舒适度。'
  },
  'Risk Return Ratio': {
    name: '风险收益比 (Risk Return Ratio)',
    definition: '简单的单位风险回报衡量。',
    calculation: '年化收益 / 年化波动',
    interpretation: '基础的效率评估。'
  },
  'Common Sense Ratio': {
    name: '常识比率 (Common Sense Ratio)',
    definition: '利润因子与尾部比率的乘积。',
    calculation: 'Profit Factor * Tail Ratio',
    interpretation: '综合了盈亏能力和极端抗压能力。'
  },
  'CPC Index': {
    name: 'CPC指数 (CPC Index)',
    definition: 'Profit Factor * Win Rate * Payoff Ratio',
    calculation: '利润因子 * 胜率 * 盈亏比',
    interpretation: '衡量交易系统综合竞争力的复合指标。'
  },
  'Kelly Criterion': {
    name: '凯利公式 (Kelly Criterion)',
    definition: '在已知胜率和赔率下，理论上的最优投资比例。',
    calculation: '胜率 - (1 - 胜率) / 盈亏比',
    interpretation: '防止过度交易和过快破产。'
  },
  'Recovery Factor': {
    name: '恢复因子 (Recovery Factor)',
    definition: '累计利润与最大回撤的比。',
    calculation: '净利润 / 最大回撤',
    interpretation: '反映策略从亏损中恢复的能力。'
  },
  'Ulcer Performance Index (UPI)': {
    name: '溃疡表现指数 (UPI)',
    definition: '年化收益除以溃疡指数。',
    calculation: '年化收益 / Ulcer Index',
    interpretation: '类似夏普比率，但分母是体现“痛苦感”的溃疡指数。'
  },

  // Benchmark Greeks
  'Alpha': {
    name: '阿尔法 (Alpha)',
    definition: '超额收益，即战胜市场基准的部分。',
    calculation: '策略收益 - [无风险利率 + Beta * (基准收益 - 无风险利率)]',
    interpretation: '反映了投资经理的主动管理水平。'
  },
  'Beta': {
    name: '贝塔 (Beta)',
    definition: '系统性风险，衡量策略对市场波动的敏感度。',
    calculation: 'Cov(策略, 基准) / Var(基准)',
    interpretation: 'Beta=1意味着与市场同步波动，>1波动更剧烈。'
  },
  'Correlation': {
    name: '相关性 (Correlation)',
    definition: '策略与基准波动的线性相关程度。',
    calculation: '相关系数 (Pearson)',
    interpretation: '1代表完全正相关，0代表不相关，-1代表完全负相关。'
  },
  'R-Squared (R2)': {
    name: 'R平方 (R-Squared)',
    definition: '策略波动中可以由基准波动解释的比例。',
    calculation: '相关系数的平方',
    interpretation: '反映了贝塔系数的可靠性。'
  },
  'Information Ratio': {
    name: '信息比率 (Information Ratio)',
    definition: '超额收益与跟踪误差的比。',
    calculation: '(策略收益 - 基准收益) / 跟踪误差',
    interpretation: '衡量主动投资相对于风险的效率。'
  },
  'Tracking Error': {
    name: '跟踪误差 (Tracking Error)',
    definition: '策略收益与基准收益之差的标准差。',
    calculation: 'std(策略日收益 - 基准日收益) * sqrt(252)',
    interpretation: '反映了偏离基准的程度。'
  }
};

interface TooltipProps {
  metricKey: string;
  isOpen: boolean;
  mousePos: { x: number; y: number };
}

export const MetricExplanationModal: React.FC<TooltipProps> = ({ metricKey, isOpen, mousePos }) => {
  if (!isOpen) return null;

  const info = explanations[metricKey] || {
    name: metricKey,
    definition: '暂无详细说明。',
    calculation: '-',
    interpretation: '-'
  };

  // Adjust positioning to avoid edge overflow
  const tooltipWidth = 320;
  const tooltipHeight = 250;
  let left = mousePos.x + 20;
  let top = mousePos.y - 100;

  if (left + tooltipWidth > window.innerWidth) {
    left = mousePos.x - tooltipWidth - 20;
  }
  if (top + tooltipHeight > window.innerHeight) {
    top = window.innerHeight - tooltipHeight - 20;
  }
  if (top < 20) {
    top = 20;
  }

  return (
    <div 
      className="fixed z-[999] pointer-events-none animate-fade-in"
      style={{ left, top, width: tooltipWidth }}
    >
      <div className="bg-white rounded-xl shadow-2xl border border-gray-100 overflow-hidden ring-1 ring-black/5">
        <div className="flex items-center gap-2 p-3 border-b border-gray-50 bg-gray-50/80">
          <Info className="w-4 h-4 text-blue-600" />
          <h3 className="font-bold text-gray-900 text-[11px]">{info.name}</h3>
        </div>
        
        <div className="p-4 space-y-4">
          <div>
            <h4 className="text-[9px] font-extrabold text-gray-400 uppercase mb-1">定义</h4>
            <p className="text-gray-700 leading-snug text-[11px]">{info.definition}</p>
          </div>
          <div>
            <h4 className="text-[9px] font-extrabold text-gray-400 uppercase mb-1">计算方式</h4>
            <code className="block bg-blue-50/50 p-2 rounded-lg text-[10px] font-mono text-blue-700 border border-blue-100/50 break-words">
              {info.calculation}
            </code>
          </div>
          <div>
            <h4 className="text-[9px] font-extrabold text-gray-400 uppercase mb-1">解读</h4>
            <p className="text-gray-700 text-[11px] leading-snug">{info.interpretation}</p>
          </div>
        </div>
      </div>
    </div>
  );
};