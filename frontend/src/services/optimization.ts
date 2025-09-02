import { apiClient } from './api';
import type { PaginatedResponse, PaginationParams } from '../types';

export interface OptimizationRequest {
  strategy: string;
  dataset: string;
  parameter_ranges: Record<string, any>;
  metric: string;
  engine_options?: Record<string, any>;
}

export interface OptimizationJob {
  id: string;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  strategy: string;
  dataset: string;
  progress: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
}

export interface OptimizationResult {
  best_parameters: Record<string, any>;
  best_score: number;
  results: Array<{
    parameters: Record<string, any>;
    score: number;
    metrics: Record<string, any>;
  }>;
}

export class OptimizationService {
  static async startOptimization(request: OptimizationRequest): Promise<OptimizationJob> {
    return apiClient.post<OptimizationJob>('/optimize', request);
  }

  static async listOptimizationJobs(params?: PaginationParams): Promise<PaginatedResponse<OptimizationJob>> {
    return apiClient.get<PaginatedResponse<OptimizationJob>>('/optimize', params);
  }

  static async getOptimizationStatus(jobId: string): Promise<OptimizationJob> {
    return apiClient.get<OptimizationJob>(`/optimize/${jobId}/status`);
  }

  static async getOptimizationResults(jobId: string): Promise<OptimizationResult> {
    return apiClient.get<OptimizationResult>(`/optimize/${jobId}/results`);
  }

  static async cancelOptimization(jobId: string): Promise<void> {
    return apiClient.post<void>(`/optimize/${jobId}/cancel`);
  }

  static async getOptimizationStats(): Promise<any> {
    return apiClient.get<any>('/optimize/stats/summary');
  }

  static async validateOptimizationRequest(request: OptimizationRequest): Promise<any> {
    return apiClient.post<any>('/optimize/validate', request);
  }

  static async getAvailableOptimizationMetrics(): Promise<string[]> {
    return apiClient.get<string[]>('/optimize/metrics');
  }

  static async quickOptimization(request: OptimizationRequest): Promise<OptimizationResult> {
    return apiClient.post<OptimizationResult>('/optimize/quick', request);
  }
}
