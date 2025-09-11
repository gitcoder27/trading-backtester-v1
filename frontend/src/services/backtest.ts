import { apiClient } from './api';
import type { 
  BacktestConfig, 
  BacktestResult, 
  Job, 
  PaginatedResponse, 
  PaginationParams 
} from '../types/index';

export class BacktestService {
  static async runBacktest(config: BacktestConfig): Promise<BacktestResult> {
    // Map to BacktestRequest schema: strategy, strategy_params, dataset, engine_options
    const engineOptions: any = {
      initial_cash: config.initial_capital,
      lots: config.position_size,
      fee_per_trade: config.commission,
      slippage: config.slippage,
      // Map enhanced params if present
      intraday: (config.parameters as any)?.intraday_mode ?? true,
      daily_target: (config.parameters as any)?.daily_profit_target ?? 30.0,
      daily_profit_target: (config.parameters as any)?.daily_profit_target ?? 30.0,
      option_delta: (config.parameters as any)?.option_delta ?? 0.5,
      option_price_per_unit: (config.parameters as any)?.option_price_per_unit ?? 1.0,
    };

    const backtestRequest = {
      strategy: config.strategy_id.toString(),
      dataset: config.dataset_id.toString(),
      strategy_params: config.parameters || {},
      engine_options: engineOptions,
    };

    return apiClient.post<BacktestResult>('/backtests', backtestRequest);
  }

  static async getBacktestResults(id: string): Promise<BacktestResult> {
    return apiClient.get<BacktestResult>(`/backtests/${id}/results`);
  }

  static async getBacktest(id: string, options?: { minimal?: boolean }): Promise<any> {
    // Get backtest details; pass minimal=true to omit heavy results payload
    const params: Record<string, any> = {};
    if (options?.minimal) params.minimal = 'true';
    return apiClient.get<any>(`/backtests/${id}`, params);
  }

  static async listBacktests(params?: PaginationParams): Promise<PaginatedResponse<any>> {
    return apiClient.get<PaginatedResponse<any>>('/backtests', params);
  }

  static async uploadAndRunBacktest(file: File, config: Partial<BacktestConfig>): Promise<BacktestResult> {
    const formData = new FormData();
    formData.append('file', file);
    
    const engineOptions: any = {
      initial_cash: config.initial_capital,
      lots: config.position_size,
      fee_per_trade: config.commission,
      slippage: config.slippage,
      intraday: (config.parameters as any)?.intraday_mode ?? true,
      daily_target: (config.parameters as any)?.daily_profit_target ?? 30.0,
      daily_profit_target: (config.parameters as any)?.daily_profit_target ?? 30.0,
      option_delta: (config.parameters as any)?.option_delta ?? 0.5,
      option_price_per_unit: (config.parameters as any)?.option_price_per_unit ?? 1.0,
    };

    formData.append('strategy', String(config.strategy_id ?? ''));
    formData.append('strategy_params', JSON.stringify(config.parameters || {}));
    formData.append('engine_options', JSON.stringify(engineOptions));

    return apiClient.upload<BacktestResult>('/backtests/upload', formData);
  }

  static async deleteBacktest(id: string): Promise<void> {
    return apiClient.delete<void>(`/backtests/${id}`);
  }

  static async getChartData(
    id: string, 
    options?: {
      includeTrades?: boolean;
      includeIndicators?: boolean;
      maxCandles?: number;
      tz?: string;
      start?: string; // ISO datetime or YYYY-MM-DD
      end?: string;   // ISO datetime or YYYY-MM-DD
    }
  ): Promise<any> {
    const params = new URLSearchParams();
    if (options?.includeTrades !== undefined) {
      params.append('include_trades', options.includeTrades.toString());
    }
    if (options?.includeIndicators !== undefined) {
      params.append('include_indicators', options.includeIndicators.toString());
    }
    if (options?.maxCandles) {
      params.append('max_candles', options.maxCandles.toString());
    }
    if (options?.start) {
      params.append('start', options.start);
    }
    if (options?.end) {
      params.append('end', options.end);
    }
    if (options?.tz) {
      params.append('tz', options.tz);
    }
    
    const queryString = params.toString();
    const url = `/analytics/chart-data/${id}${queryString ? `?${queryString}` : ''}`;
    return apiClient.get<any>(url);
  }
}

export class JobService {
  static async submitBackgroundJob(config: BacktestConfig): Promise<Job> {
    // Map to BacktestRequest schema for jobs endpoint
    const engineOptions: any = {
      initial_cash: config.initial_capital,
      lots: config.position_size,
      fee_per_trade: config.commission,
      slippage: config.slippage,
      intraday: (config.parameters as any)?.intraday_mode ?? true,
      daily_target: (config.parameters as any)?.daily_profit_target ?? 30.0,
      daily_profit_target: (config.parameters as any)?.daily_profit_target ?? 30.0,
      option_delta: (config.parameters as any)?.option_delta ?? 0.5,
      option_price_per_unit: (config.parameters as any)?.option_price_per_unit ?? 1.0,
    };

    const jobRequest = {
      strategy: config.strategy_id.toString(),
      dataset: config.dataset_id.toString(),
      strategy_params: config.parameters || {},
      engine_options: engineOptions,
    };

    return apiClient.post<Job>('/jobs/', jobRequest);
  }

  static async getJobStatus(id: string): Promise<Job> {
    return apiClient.get<Job>(`/jobs/${id}/status`);
  }

  static async getJobResults(id: string): Promise<any> {
    return apiClient.get<any>(`/jobs/${id}/results`);
  }

  static async cancelJob(id: string): Promise<void> {
    return apiClient.post<void>(`/jobs/${id}/cancel`);
  }

  static async listJobs(params?: PaginationParams): Promise<PaginatedResponse<Job>> {
    return apiClient.get<PaginatedResponse<Job>>('/jobs', params);
  }

  static async deleteJob(id: string): Promise<void> {
    return apiClient.delete<void>(`/jobs/${id}`);
  }

  static async getJobStats(): Promise<any> {
    return apiClient.get<any>('/jobs/stats');
  }
}
