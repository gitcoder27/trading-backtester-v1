import type {
  BacktestDisplay,
  Job,
  BacktestConfig,
  Strategy,
  ParameterSchema,
} from '../types';

export function createBacktestDisplay(overrides: Partial<BacktestDisplay> = {}): BacktestDisplay {
  return {
    id: 'bt-1',
    jobId: 'job-1',
    strategy: 'Mean Reversion',
    dataset: 'EURUSD',
    status: 'completed',
    totalReturn: '+12.5%',
    sharpeRatio: 1.45,
    maxDrawdown: '-5.2%',
    totalTrades: 120,
    winRate: '54%',
    createdAt: '2024-01-01',
    createdAtTs: 1704067200000,
    duration: '2h 10m',
    ...overrides,
  };
}

export function createJob(overrides: Partial<Job> = {}): Job {
  return {
    id: 'job-1',
    type: 'backtest',
    status: 'completed',
    progress: 100,
    created_at: '2024-01-01T00:00:00Z',
    started_at: '2024-01-01T00:00:00Z',
    completed_at: '2024-01-01T02:00:00Z',
    metadata: {},
    ...overrides,
  };
}

export function createBacktestConfig(overrides: Partial<BacktestConfig> = {}): BacktestConfig {
  return {
    strategy_id: 'strategy-1',
    dataset_id: 'dataset-1',
    initial_capital: 10000,
    position_size: 1,
    start_date: '2024-01-01',
    end_date: '2024-02-01',
    commission: 0.001,
    slippage: 0.0005,
    risk_management: {
      stop_loss: 0.02,
      take_profit: 0.04,
      trailing_stop: false,
    },
    parameters: {},
    ...overrides,
  };
}

export function createStrategy(overrides: Partial<Strategy> = {}): Strategy {
  return {
    id: 'strategy-1',
    name: 'Sample Strategy',
    description: 'Test strategy',
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    file_path: '/strategies/sample.py',
    parameters_schema: [],
    ...overrides,
  };
}

export function createDataset(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    id: 'dataset-1',
    name: 'EURUSD Dataset',
    description: 'Sample dataset',
    timeframe: '1h',
    rows: 1000,
    columns: ['timestamp', 'open', 'high', 'low', 'close'],
    size_bytes: 1024 * 1024,
    quality_score: 0.9,
    source: 'local',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
    tags: ['fx'],
    ...overrides,
  };
}

export function createParameter(name: string, overrides: Partial<ParameterSchema> = {}): ParameterSchema {
  return {
    name,
    type: 'int',
    default: 1,
    min: 0,
    max: 10,
    description: 'Sample parameter',
    required: true,
    ...overrides,
  };
}
