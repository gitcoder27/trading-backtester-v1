import type { BacktestConfig as BaseBacktestConfig } from '../../../types';

export interface Dataset {
  id: number;
  name: string;
  description?: string;
  file_path: string;
  rows_count: number;
  date_range: {
    start: string;
    end: string;
  };
}

export interface Strategy {
  id: number;
  name: string;
  description: string;
}

// Enhanced config that extends the base with Streamlit-like features
export interface EnhancedBacktestConfig extends BaseBacktestConfig {
  // Map enhanced fields to base fields
  strategy_params: Record<string, any>; // maps to parameters
  option_delta: number;
  lots: number;
  option_price_per_unit: number;
  fee_per_trade: number;
  daily_profit_target: number;
  intraday_mode: boolean;
  session_close_time: string;
  // Trading filters
  direction_filter: string[];
  apply_time_filter: boolean;
  start_hour: number;
  end_hour: number;
  apply_weekday_filter: boolean;
  weekdays: number[];
}

export interface EnhancedBacktestModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (config: BaseBacktestConfig) => void;
  isSubmitting?: boolean;
}

export type TabType = 'strategy' | 'execution' | 'filters';
