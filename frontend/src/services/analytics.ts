import { apiClient } from './api';

export class AnalyticsService {
  static async getPerformanceSummary(backtestId: string, sections?: string[]): Promise<any> {
    const params: Record<string, any> = {};
    if (sections && sections.length > 0) {
      params.sections = sections;
    }
    return apiClient.get<any>(`/analytics/performance/${backtestId}`, params);
  }

  static async getCharts(backtestId: string, chartTypes?: string[], options?: { maxPoints?: number }): Promise<any> {
    const params: Record<string, any> = {};
    if (chartTypes && chartTypes.length > 0) params.chart_types = chartTypes;
    if (options?.maxPoints) params.max_points = options.maxPoints;
    return apiClient.get<any>(`/analytics/charts/${backtestId}`, params);
  }

  static async compareStrategies(request: any): Promise<any> {
    return apiClient.post<any>('/analytics/compare', request);
  }

  static async getEquityChart(backtestId: string, options?: { maxPoints?: number }): Promise<any> {
    const params: Record<string, any> = {};
    if (options?.maxPoints) params.max_points = options.maxPoints;
    return apiClient.get<any>(`/analytics/charts/${backtestId}/equity`, params);
  }

  static async getDrawdownChart(backtestId: string, options?: { maxPoints?: number }): Promise<any> {
    const params: Record<string, any> = {};
    if (options?.maxPoints) params.max_points = options.maxPoints;
    return apiClient.get<any>(`/analytics/charts/${backtestId}/drawdown`, params);
  }

  static async getReturnsChart(backtestId: string): Promise<any> {
    return apiClient.get<any>(`/analytics/charts/${backtestId}/returns`);
  }

  static async getTradesChart(backtestId: string, options?: { maxPoints?: number }): Promise<any> {
    const params: Record<string, any> = {};
    if (options?.maxPoints) params.max_points = options.maxPoints;
    return apiClient.get<any>(`/analytics/charts/${backtestId}/trades`, params);
  }

  static async getMonthlyReturnsChart(backtestId: string): Promise<any> {
    return apiClient.get<any>(`/analytics/charts/${backtestId}/monthly_returns`);
  }

  static async getMetricsSummary(): Promise<any> {
    return apiClient.get<any>('/analytics/summary/metrics');
  }
}
