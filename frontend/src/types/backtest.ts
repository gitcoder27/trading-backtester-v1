export interface Job {
  id: string;
  type: 'backtest' | 'optimization' | 'upload';
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error?: string;
  result?: any;
  metadata?: Record<string, any>;
}

export interface JobStatus {
  id: string;
  status: Job['status'];
  progress: number;
  eta_seconds?: number;
  current_step?: string;
  total_steps?: number;
  error?: string;
}

export interface OptimizationConfig {
  strategy_id: string;
  dataset_id: string;
  parameters: Record<string, {
    min: number;
    max: number;
    step: number;
  }>;
  objective: 'total_return' | 'sharpe_ratio' | 'profit_factor';
  max_iterations?: number;
  validation_split?: number;
}

export interface OptimizationResult {
  id: string;
  config: OptimizationConfig;
  best_parameters: Record<string, any>;
  best_score: number;
  results: Array<{
    parameters: Record<string, any>;
    score: number;
    metrics: any;
  }>;
  validation_results?: {
    in_sample: any;
    out_of_sample: any;
  };
}

export interface ChartData {
  equity_curve: {
    dates: string[];
    values: number[];
  };
  drawdown: {
    dates: string[];
    values: number[];
  };
  returns: {
    dates: string[];
    values: number[];
  };
  trades: Array<{
    date: string;
    type: 'entry' | 'exit';
    price: number;
    side: 'long' | 'short';
    pnl?: number;
  }>;
}

export interface ComparisonResult {
  strategies: Array<{
    id: string;
    name: string;
    metrics: any;
  }>;
  correlation_matrix: number[][];
  combined_equity: {
    dates: string[];
    series: Record<string, number[]>;
  };
}

export interface PerformanceMetrics {
  total_return: number;
  annualized_return: number;
  volatility: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown: number;
  max_drawdown_duration: number;
  calmar_ratio: number;
  omega_ratio: number;
  tail_ratio: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  profit_factor: number;
  avg_trade: number;
  avg_win: number;
  avg_loss: number;
  largest_win: number;
  largest_loss: number;
  consecutive_wins: number;
  consecutive_losses: number;
  kelly_criterion: number;
}

// Lightweight display model for Backtests list page
export interface BacktestDisplay {
  id: string;
  jobId?: string;
  strategy: string;
  dataset: string;
  status: 'completed' | 'running' | 'failed' | 'pending';
  totalReturn: string;
  sharpeRatio: number;
  maxDrawdown: string;
  totalTrades: number;
  winRate: string;
  createdAt: string;
  createdAtTs: number;
  duration: string;
}
