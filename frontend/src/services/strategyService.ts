import { apiClient } from './api';
import type {
  Strategy,
  ParameterSchema,
  StrategySource,
  StrategyCodeSaveResponse,
  StrategyDeleteResponse,
} from '../types';

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
  static async getStrategy(id: string | number): Promise<Strategy> {
    return apiClient.get<Strategy>(`/strategies/${id}`);
  }

  /**
   * Get strategy parameter schema
   */
  static async getStrategySchema(id: string | number): Promise<ParameterSchema[]> {
    return apiClient.get<ParameterSchema[]>(`/strategies/${id}/schema`);
  }

  /**
   * Validate strategy with parameters
   */
  static async validateStrategy(id: string | number, parameters?: Record<string, any>): Promise<StrategyValidationResult> {
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
  static async updateStrategy(id: string | number, updates: Partial<Strategy>): Promise<Strategy> {
    return apiClient.put<Strategy>(`/strategies/${id}`, updates);
  }

  /**
   * Soft delete strategy
   */
  static async deleteStrategy(id: string | number): Promise<StrategyDeleteResponse> {
    return apiClient.delete<StrategyDeleteResponse>(`/strategies/${id}`);
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
  static async toggleStrategy(id: string | number, isActive: boolean): Promise<Strategy> {
    return apiClient.put<Strategy>(`/strategies/${id}`, { is_active: isActive });
  }

  /**
   * Retrieve Python source code for a registered strategy
   */
  static async getStrategyCode(id: string): Promise<StrategySource> {
    const response = await apiClient.get<{
      success: boolean;
      strategy_id: number;
      module_path: string;
      class_name?: string;
      file_path: string;
      content: string;
    }>(`/strategies/${id}/code`);

    return {
      strategy_id: response.strategy_id,
      module_path: response.module_path,
      class_name: response.class_name,
      file_path: response.file_path,
      content: response.content
    };
  }

  /**
   * Persist updated strategy source code
   */
  static async updateStrategyCode(id: string, content: string): Promise<StrategyCodeSaveResponse> {
    const response = await apiClient.put<{
      success: boolean;
      strategy_id: number;
      module_path: string;
      file_path: string;
      updated: boolean;
      registration?: StrategyCodeSaveResponse['registration'];
    }>(`/strategies/${id}/code`, { content });

    return {
      strategy_id: response.strategy_id,
      module_path: response.module_path,
      file_path: response.file_path,
      updated: response.updated,
      registration: response.registration
    };
  }

  /**
   * Create a brand new strategy Python file
   */
  static async createStrategyFile(payload: { file_name: string; content: string; overwrite?: boolean }): Promise<StrategyCodeSaveResponse> {
    const response = await apiClient.post<{
      success: boolean;
      file_path: string;
      module_path: string;
      created: boolean;
      registration?: StrategyCodeSaveResponse['registration'];
      registered_ids?: string[];
    }>(`/strategies/code`, payload);

    return {
      module_path: response.module_path,
      file_path: response.file_path,
      created: response.created,
      registration: response.registration,
      registered_ids: response.registered_ids
    };
  }
}
