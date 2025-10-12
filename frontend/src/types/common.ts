export interface PaginationParams {
  page?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface UploadResponse {
  dataset_id: string;
  filename: string;
  size: number;
  rows: number;
  preview: any[];
}

export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'down';
  database: boolean;
  api: boolean;
  jobs: {
    running: number;
    queued: number;
    failed: number;
  };
  memory_usage: number;
  disk_usage: number;
  uptime: number;
}

export type Theme = 'light' | 'dark' | 'auto';

export interface UserPreferences {
  theme: Theme;
  default_commission: number;
  default_slippage: number;
  default_initial_capital: number;
  default_lot_size: number;
  default_fee_per_trade: number;
  default_daily_profit_target: number;
  default_option_delta: number;
  default_option_price_per_unit: number;
  default_intraday_mode: boolean;
  default_session_close_time: string;
  default_direction_filter: Array<'long' | 'short'>;
  default_apply_time_filter: boolean;
  default_start_hour: number;
  default_end_hour: number;
  default_apply_weekday_filter: boolean;
  default_weekdays: number[];
  chart_preferences: {
    show_trades: boolean;
    show_signals: boolean;
    chart_type: 'candlestick' | 'line' | 'area';
  };
  table_preferences: {
    page_size: number;
    auto_refresh: boolean;
    refresh_interval: number;
  };
}

export interface NotificationSettings {
  backtest_completion: boolean;
  optimization_completion: boolean;
  job_failures: boolean;
  system_alerts: boolean;
}
