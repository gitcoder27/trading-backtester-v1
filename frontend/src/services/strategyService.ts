import { apiClient } from './api';
import type { Strategy, ParameterSchema } from '../types';

export interface StrategyDiscoveryResult {
  id: string;
  name: string;
  module_path: string;
  file_path: string;
  class_name: string;
  description?: string;
  is_valid: boolean;
  validation_errors?: string[];
  parameters_schema?: ParameterSchema[];
}

export interface StrategyValidationRequest {
  module_path: string;
  parameters?: Record<string, any>;
}

export interface StrategyValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  parameter_schema: ParameterSchema[];
}

export interface StrategyStats {
  total_strategies: number;
  active_strategies: number;
  discovered_strategies: number;
  total_backtests: number;
  avg_performance: number;
}

export class StrategyService {
  /**
   * Discover strategies from the filesystem
   */
  static async discoverStrategies(): Promise<StrategyDiscoveryResult[]> {
    const response = await apiClient.get<{success: boolean; strategies: StrategyDiscoveryResult[]; total: number}>('/strategies/discover');
    return response.strategies || [];
  }

  /**
   * Register discovered strategies
   */
  static async registerStrategies(strategyIds: string[]): Promise<{ success: boolean; registered: number; updated: number; errors: string[] }> {
    return apiClient.post<{ success: boolean; registered: number; updated: number; errors: string[] }>('/strategies/register', {
      strategy_ids: strategyIds
    });
  }

  /**
   * Get all registered strategies
   */
  static async getStrategies(): Promise<Strategy[]> {
    const response = await apiClient.get<{success: boolean; strategies: Strategy[]; total: number; active_only: boolean}>('/strategies/');
    return response.strategies || [];
  }

  /**
   * Get strategy details by ID
   */
  static async getStrategy(id: string): Promise<Strategy> {
    return apiClient.get<Strategy>(`/strategies/${id}`);
  }

  /**
   * Get strategy parameter schema
   */
  static async getStrategySchema(id: string): Promise<ParameterSchema[]> {
    return apiClient.get<ParameterSchema[]>(`/strategies/${id}/schema`);
  }

  /**
   * Validate strategy with parameters
   */
  static async validateStrategy(id: string, parameters?: Record<string, any>): Promise<StrategyValidationResult> {
    return apiClient.post<StrategyValidationResult>(`/strategies/${id}/validate`, {
      parameters: parameters || {}
    });
  }

  /**
   * Validate strategy by module path
   */
  static async validateStrategyByPath(request: StrategyValidationRequest): Promise<StrategyValidationResult> {
    return apiClient.post<StrategyValidationResult>('/strategies/validate-by-path', request);
  }

  /**
   * Update strategy metadata
   */
  static async updateStrategy(id: string, updates: Partial<Strategy>): Promise<Strategy> {
    return apiClient.put<Strategy>(`/strategies/${id}`, updates);
  }

  /**
   * Soft delete strategy
   */
  static async deleteStrategy(id: string): Promise<{ success: boolean }> {
    return apiClient.delete<{ success: boolean }>(`/strategies/${id}`);
  }

  /**
   * Get strategy statistics
   */
  static async getStrategyStats(): Promise<StrategyStats> {
    return apiClient.get<StrategyStats>('/strategies/stats/summary');
  }

  /**
   * Toggle strategy active status
   */
  static async toggleStrategy(id: string, isActive: boolean): Promise<Strategy> {
    return apiClient.put<Strategy>(`/strategies/${id}`, { is_active: isActive });
  }
}
