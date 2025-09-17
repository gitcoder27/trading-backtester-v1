// Core data types for the Trading Backtester API

export interface Dataset {
  id: string;
  name: string;
  symbol: string;
  timeframe: string;
  file_path: string;
  file_size: number;
  record_count: number;
  start_date: string;
  end_date: string;
  created_at: string;
  updated_at: string;
  quality_score?: number;
  metadata?: Record<string, any>;
}

export interface DatasetDiscoveryItem {
  dataset_id?: number | string | null;
  file_path: string;
  name?: string;
  file_size?: number;
  rows_count?: number;
  timeframe?: string;
  start_date?: string | null;
  end_date?: string | null;
  quality_score?: number;
  registered: boolean;
  analysis?: Record<string, any>;
  error?: string;
}

export interface DatasetDiscoveryResponse {
  success: boolean;
  datasets: DatasetDiscoveryItem[];
  total: number;
  data_directory?: string;
}

export interface DatasetRegistrationResponse {
  success: boolean;
  registered: (number | string)[];
  skipped: string[];
  errors: { file_path: string; error: string }[];
  datasets?: Dataset[];
}

export interface DatasetUpload {
  name: string;
  symbol: string;
  timeframe: string;
  description?: string;
  metadata?: Record<string, any>;
}

export interface DataQuality {
  missing_data_percentage: number;
  gaps_detected: number;
  duplicate_timestamps: number;
  data_consistency_score: number;
  anomalies: {
    type: string;
    count: number;
    severity: 'low' | 'medium' | 'high';
  }[];
  recommendations: string[];
}

export interface DatasetPreview {
  columns: string[];
  data: Record<string, any>[];
  total_rows: number;
  preview_rows: number;
}

export interface BacktestConfig {
  strategy_id: string;
  dataset_id: string;
  initial_capital: number;
  position_size: number;
  commission: number;
  slippage: number;
  start_date?: string;
  end_date?: string;
  parameters?: Record<string, any>;
}

export interface BacktestResult {
  id: string;
  strategy_id: string;
  dataset_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at: string;
  completed_at?: string;
  error?: string;
  config: BacktestConfig;
  results?: {
    total_return: number;
    annualized_return: number;
    sharpe_ratio: number;
    max_drawdown: number;
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
  };
}

export interface Trade {
  id: string;
  backtest_id: string;
  entry_date: string;
  exit_date?: string;
  symbol: string;
  side: 'long' | 'short';
  entry_price: number;
  exit_price?: number;
  quantity: number;
  pnl?: number;
  commission?: number;
  tags?: string[];
}

export interface Job {
  id: string;
  type: 'backtest' | 'optimization';
  status: JobStatus;
  progress: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error?: string;
  result?: any;
  metadata?: Record<string, any>;
}

export type JobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface Strategy {
  id: string;
  name: string;
  description?: string;
  file_path: string;
  created_at: string;
  is_active: boolean;
  parameters_schema?: ParameterSchema[];
  last_backtest_at?: string;
  performance_summary?: {
    total_backtests: number;
    avg_return: number;
    best_return: number;
    worst_return: number;
  };
}

export interface ParameterSchema {
  name: string;
  type: 'int' | 'float' | 'bool' | 'str' | 'select';
  default: any;
  min?: number;
  max?: number;
  options?: any[];
  description?: string;
  required?: boolean;
}

export interface OptimizationConfig {
  strategy_id: string;
  dataset_id: string;
  parameters: {
    [key: string]: {
      min: number;
      max: number;
      step: number;
    };
  };
  optimization_metric: string;
  train_start_date?: string;
  train_end_date?: string;
  test_start_date?: string;
  test_end_date?: string;
  max_iterations?: number;
}

export interface OptimizationResult {
  id: string;
  config: OptimizationConfig;
  status: JobStatus;
  progress: number;
  best_parameters?: Record<string, any>;
  best_score?: number;
  results?: {
    parameter_combinations: Array<{
      parameters: Record<string, any>;
      score: number;
      metrics: Record<string, number>;
    }>;
    optimization_surface?: any;
  };
  created_at: string;
  completed_at?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface PaginationParams {
  page?: number;
  size?: number;
  sort?: string;
  order?: 'asc' | 'desc';
  search?: string;
}

export interface UploadResponse {
  id: string;
  message: string;
  dataset?: Dataset;
}

export interface ValidationResult {
  valid: boolean;
  errors?: string[];
  warnings?: string[];
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'down';
  components: {
    database: 'healthy' | 'error';
    file_system: 'healthy' | 'error';
    background_workers: 'healthy' | 'error';
  };
  memory_usage: number;
  cpu_usage: number;
  disk_usage: number;
  active_jobs: number;
  uptime: number;
}

export interface DashboardStats {
  total_strategies: number;
  total_datasets: number;
  total_backtests: number;
  recent_backtests: BacktestResult[];
  system_health: SystemHealth;
  performance_summary: {
    best_performing_strategy: string;
    avg_return_across_strategies: number;
    total_trades_today: number;
  };
}

// Additional types for stores
export type Theme = 'light' | 'dark' | 'system';

export interface UserPreferences {
  theme: Theme;
  notifications?: boolean;
  auto_save?: boolean;
  default_timeframe?: string;
  default_initial_capital: number;
  default_commission: number;
  default_slippage: number;
  chart_preferences: {
    show_trades: boolean;
    show_signals: boolean;
    chart_type: string;
  };
  table_preferences: {
    page_size: number;
    auto_refresh: boolean;
    refresh_interval: number;
  };
}

export interface ChartPreferences {
  theme: 'light' | 'dark';
  grid: boolean;
  crosshairs: boolean;
  volume: boolean;
  indicators: string[];
}

export interface TablePreferences {
  rows_per_page: number;
  columns_visible: string[];
  sort_order: 'asc' | 'desc';
  sort_column: string;
}
