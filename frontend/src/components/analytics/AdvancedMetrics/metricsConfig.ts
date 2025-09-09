import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Shield, 
  Clock,
  Target,
  BarChart3,
  AlertTriangle
} from 'lucide-react';
import type { MetricCardProps, PerformanceData } from './types';

export const getCoreMetrics = (performance: PerformanceData['performance']): MetricCardProps[] => [
  {
    title: "Total Return",
    value: performance.basic_metrics.total_return_pct || 0,
    subtitle: "Overall performance",
    icon: TrendingUp,
    color: "text-success-600 dark:text-success-400",
    bgColor: "bg-success-100 dark:bg-success-900/50",
    format: "percentage"
  },
  {
    title: "Sharpe Ratio",
    value: performance.basic_metrics.sharpe_ratio || 0,
    subtitle: "Risk-adjusted return",
    icon: Activity,
    color: "text-primary-600 dark:text-primary-400",
    bgColor: "bg-primary-100 dark:bg-primary-900/50",
    format: "ratio"
  },
  {
    title: "Max Drawdown",
    value: performance.basic_metrics.max_drawdown_pct || 0,
    subtitle: "Largest peak-to-trough decline",
    icon: TrendingDown,
    color: "text-danger-600 dark:text-danger-400",
    bgColor: "bg-danger-100 dark:bg-danger-900/50",
    format: "percentage"
  },
  {
    title: "Win Rate",
    value: performance.basic_metrics.win_rate || 0,
    subtitle: "Percentage of winning trades",
    icon: Target,
    color: "text-info-600 dark:text-info-400",
    bgColor: "bg-info-100 dark:bg-info-900/50",
    format: "percentage"
  },
  {
    title: "Profit Factor",
    value: performance.basic_metrics.profit_factor || 0,
    subtitle: "Gross profit / gross loss",
    icon: BarChart3,
    color: "text-warning-600 dark:text-warning-400",
    bgColor: "bg-warning-100 dark:bg-warning-900/50",
    format: "ratio"
  },
  {
    title: "Total Trades",
    value: performance.basic_metrics.total_trades || 0,
    subtitle: "Number of executed trades",
    icon: Activity,
    format: "number"
  }
];

export const getAdvancedMetrics = (performance: PerformanceData['performance']): MetricCardProps[] => [
  {
    title: "Volatility (Annualized)",
    value: performance.advanced_analytics.volatility_annualized || 0,
    subtitle: "Standard deviation of returns",
    icon: Activity,
    format: "percentage"
  },
  {
    title: "Sortino Ratio",
    value: performance.advanced_analytics.sortino_ratio || 0,
    subtitle: "Return / downside deviation",
    icon: Shield,
    format: "ratio"
  },
  {
    title: "Calmar Ratio",
    value: performance.advanced_analytics.calmar_ratio || 0,
    subtitle: "Return / max drawdown",
    icon: TrendingUp,
    format: "ratio"
  },
  {
    title: "Skewness",
    value: performance.advanced_analytics.skewness || 0,
    subtitle: "Asymmetry of returns",
    icon: BarChart3,
    format: "ratio"
  },
  {
    title: "Kurtosis",
    value: performance.advanced_analytics.kurtosis || 0,
    subtitle: "Tail risk measure",
    icon: AlertTriangle,
    format: "ratio"
  },
  {
    title: "Downside Deviation",
    value: performance.advanced_analytics.downside_deviation || 0,
    subtitle: "Volatility of negative returns",
    icon: TrendingDown,
    format: "percentage"
  }
];

export const getTradeMetrics = (performance: PerformanceData['performance']): MetricCardProps[] => {
  const ta = performance.trade_analysis || ({} as any);
  const adv = performance.advanced_analytics || ({} as any);
  return [
  {
    title: "Average Win",
    value: (ta.avg_win ?? adv.avg_win) || 0,
    subtitle: "Mean winning trade P&L",
    icon: TrendingUp,
    color: "text-success-600 dark:text-success-400",
    bgColor: "bg-success-100 dark:bg-success-900/50",
    format: "currency"
  },
  {
    title: "Average Loss",
    value: Math.abs((ta.avg_loss ?? adv.avg_loss) || 0),
    subtitle: "Mean losing trade P&L",
    icon: TrendingDown,
    color: "text-danger-600 dark:text-danger-400",
    bgColor: "bg-danger-100 dark:bg-danger-900/50",
    format: "currency"
  },
  {
    title: "Largest Win",
    value: (ta.largest_win ?? adv.largest_win) || 0,
    subtitle: "Best single trade",
    icon: Target,
    color: "text-success-600 dark:text-success-400",
    bgColor: "bg-success-100 dark:bg-success-900/50",
    format: "currency"
  },
  {
    title: "Largest Loss",
    value: Math.abs((ta.largest_loss ?? adv.largest_loss) || 0),
    subtitle: "Worst single trade",
    icon: AlertTriangle,
    color: "text-danger-600 dark:text-danger-400",
    bgColor: "bg-danger-100 dark:bg-danger-900/50",
    format: "currency"
  },
  {
    title: "Max Consecutive Wins",
    value: (ta.consecutive_wins ?? adv.consecutive_wins) || 0,
    subtitle: "Longest winning streak",
    icon: TrendingUp,
    format: "number"
  },
  {
    title: "Max Consecutive Losses",
    value: (ta.consecutive_losses ?? adv.consecutive_losses) || 0,
    subtitle: "Longest losing streak",
    icon: TrendingDown,
    format: "number"
  },
  // Directional breakdown (counts)
  {
    title: "Long Trades",
    value: (ta.total_long_trades ?? adv.total_long_trades) || 0,
    subtitle: "Total long entries",
    icon: TrendingUp,
    format: "number"
  },
  {
    title: "Short Trades",
    value: (ta.total_short_trades ?? adv.total_short_trades) || 0,
    subtitle: "Total short entries",
    icon: TrendingDown,
    format: "number"
  },
  {
    title: "Winning Longs",
    value: (ta.winning_long_trades ?? adv.winning_long_trades) || 0,
    subtitle: "Profitable longs",
    icon: TrendingUp,
    format: "number"
  },
  {
    title: "Winning Shorts",
    value: (ta.winning_short_trades ?? adv.winning_short_trades) || 0,
    subtitle: "Profitable shorts",
    icon: TrendingDown,
    format: "number"
  }
];
};

export const getRiskMetrics = (performance: PerformanceData['performance']): MetricCardProps[] => {
  const items: MetricCardProps[] = [
    {
      title: "VaR (95%)",
      value: Math.abs(performance.risk_metrics.var_95 || 0),
      subtitle: "Value at Risk",
      icon: Shield,
      color: "text-warning-600 dark:text-warning-400",
      bgColor: "bg-warning-100 dark:bg-warning-900/50",
      format: "percentage"
    },
    {
      title: "VaR (99%)",
      value: Math.abs(performance.risk_metrics.var_99 || 0),
      subtitle: "Value at Risk (extreme)",
      icon: AlertTriangle,
      color: "text-danger-600 dark:text-danger-400",
      bgColor: "bg-danger-100 dark:bg-danger-900/50",
      format: "percentage"
    },
    {
      title: "CVaR (95%)",
      value: Math.abs(performance.risk_metrics.cvar_95 || 0),
      subtitle: "Conditional Value at Risk",
      icon: Shield,
      format: "percentage"
    },
    {
      title: "CVaR (99%)",
      value: Math.abs(performance.risk_metrics.cvar_99 || 0),
      subtitle: "Expected shortfall",
      icon: AlertTriangle,
      format: "percentage"
    },
    {
      title: "Max Consecutive Loss Days",
      value: performance.risk_metrics.max_consecutive_losses || 0,
      subtitle: "Longest drawdown period",
      icon: Clock,
      format: "number"
    }
  ];
  // Add drawdown analysis details if present
  if (performance.drawdown_analysis) {
    items.push(
      {
        title: "Avg Drawdown",
        value: Math.abs(performance.drawdown_analysis.avg_drawdown || 0),
        subtitle: "Mean underwater magnitude",
        icon: TrendingDown,
        format: "percentage"
      },
      {
        title: "DD Frequency",
        value: (performance.drawdown_analysis.drawdown_frequency || 0) * 100,
        subtitle: "Share of points in drawdown",
        icon: Activity,
        format: "percentage"
      },
      {
        title: "Max DD Duration",
        value: performance.drawdown_analysis.max_drawdown_duration || 0,
        subtitle: "Longest downturn (days)",
        icon: Clock,
        format: "number"
      }
    );
  }
  return items;
};

export const getDailyTargetMetrics = (performance: PerformanceData['performance']): MetricCardProps[] => {
  const ds = performance.daily_target_stats;
  if (!ds) return [];
  return [
    {
      title: "Days Traded",
      value: ds.days_traded || 0,
      subtitle: "Total trading days",
      icon: Clock,
      format: "number"
    },
    {
      title: "Target Hit Days",
      value: ds.days_target_hit || 0,
      subtitle: "Days hit daily target",
      icon: Target,
      format: "number"
    },
    {
      title: "Hit Rate",
      value: (ds.target_hit_rate || 0) * 100,
      subtitle: "Daily target hit %",
      icon: Activity,
      format: "percentage"
    },
    {
      title: "Best Day PnL",
      value: ds.max_daily_pnl || 0,
      subtitle: "Max daily profit",
      icon: TrendingUp,
      color: "text-success-600 dark:text-success-400",
      bgColor: "bg-success-100 dark:bg-success-900/50",
      format: "currency"
    },
    {
      title: "Worst Day PnL",
      value: Math.abs(ds.min_daily_pnl || 0),
      subtitle: "Max daily loss",
      icon: TrendingDown,
      color: "text-danger-600 dark:text-danger-400",
      bgColor: "bg-danger-100 dark:bg-danger-900/50",
      format: "currency"
    },
    {
      title: "Avg Day PnL",
      value: ds.avg_daily_pnl || 0,
      subtitle: "Mean daily PnL",
      icon: Activity,
      format: "currency"
    }
  ];
};
