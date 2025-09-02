export interface AdvancedMetricsProps {
  backtestId: string;
  className?: string;
}

export interface PerformanceData {
  success: boolean;
  backtest_id: number;
  performance: {
    basic_metrics: {
      total_return_pct: number;
      sharpe_ratio: number;
      max_drawdown_pct: number;
      win_rate: number;
      profit_factor: number;
      total_trades: number;
      calmar_ratio?: number;
    };
    advanced_analytics: {
      volatility_annualized: number;
      skewness: number;
      kurtosis: number;
      downside_deviation: number;
      sortino_ratio: number;
      calmar_ratio: number;
    };
    trade_analysis: {
      avg_win: number;
      avg_loss: number;
      largest_win: number;
      largest_loss: number;
      consecutive_wins: number;
      consecutive_losses: number;
    };
    risk_metrics: {
      var_95: number;
      var_99: number;
      cvar_95: number;
      cvar_99: number;
      max_consecutive_losses: number;
    };
    time_analysis: {
      performance_by_hour?: Record<string, number>;
      performance_by_weekday?: Record<string, number>;
    };
  };
}

export interface MetricCardProps {
  title: string;
  value: number;
  subtitle?: string;
  icon: React.ComponentType<{ className?: string }>;
  color?: string;
  bgColor?: string;
  format?: 'percentage' | 'currency' | 'ratio' | 'number';
}

export interface MetricsSectionProps {
  title: string;
  badgeText: string;
  badgeVariant: 'primary' | 'info' | 'success' | 'warning' | 'danger';
  metrics: MetricCardProps[];
  className?: string;
}
