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
    // Map frontend config to backend expected format
    const backtestRequest = {
      strategy: config.strategy_id.toString(),
      dataset: config.dataset_id.toString(),
      initial_cash: config.initial_capital,        // Map initial_capital -> initial_cash
      lots: config.position_size,                  // Map position_size -> lots
      commission: config.commission,
      slippage: config.slippage,
      start_date: config.start_date,
      end_date: config.end_date,
      parameters: config.parameters || {}
    };
    
    return apiClient.post<BacktestResult>('/backtests', backtestRequest);
  }

  static async getBacktestResults(id: string): Promise<BacktestResult> {
    return apiClient.get<BacktestResult>(`/backtests/${id}/results`);
  }

  static async getBacktest(id: string): Promise<any> {
    // Get backtest details from the new endpoint
    return apiClient.get<any>(`/backtests/${id}`);
  }

  static async listBacktests(params?: PaginationParams): Promise<PaginatedResponse<any>> {
    return apiClient.get<PaginatedResponse<any>>('/backtests', params);
  }

  static async uploadAndRunBacktest(file: File, config: Partial<BacktestConfig>): Promise<BacktestResult> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('config', JSON.stringify(config));
    
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
    
    const queryString = params.toString();
    const url = `/analytics/chart-data/${id}${queryString ? `?${queryString}` : ''}`;
    return apiClient.get<any>(url);
  }
}

export class JobService {
  static async submitBackgroundJob(config: BacktestConfig): Promise<Job> {
    // Map frontend config to backend expected format
    const jobRequest = {
      strategy: config.strategy_id.toString(),
      dataset: config.dataset_id.toString(),
      initial_cash: config.initial_capital,        // Map initial_capital -> initial_cash
      lots: config.position_size,                  // Map position_size -> lots  
      commission: config.commission,
      slippage: config.slippage,
      start_date: config.start_date,
      end_date: config.end_date,
      parameters: config.parameters || {}
    };
    
    return apiClient.post<Job>('/jobs', jobRequest);
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
