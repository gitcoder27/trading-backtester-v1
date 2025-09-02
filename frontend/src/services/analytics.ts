import { apiClient } from './api';

export class AnalyticsService {
  static async getPerformanceSummary(backtestId: string): Promise<any> {
    return apiClient.get<any>(`/analytics/performance/${backtestId}`);
  }

  static async getCharts(backtestId: string): Promise<any> {
    return apiClient.get<any>(`/analytics/charts/${backtestId}`);
  }

  static async compareStrategies(request: any): Promise<any> {
    return apiClient.post<any>('/analytics/compare', request);
  }

  static async getEquityChart(backtestId: string): Promise<any> {
    return apiClient.get<any>(`/analytics/charts/${backtestId}/equity`);
  }

  static async getDrawdownChart(backtestId: string): Promise<any> {
    return apiClient.get<any>(`/analytics/charts/${backtestId}/drawdown`);
  }

  static async getReturnsChart(backtestId: string): Promise<any> {
    return apiClient.get<any>(`/analytics/charts/${backtestId}/returns`);
  }

  static async getTradesChart(backtestId: string): Promise<any> {
    return apiClient.get<any>(`/analytics/charts/${backtestId}/trades`);
  }

  static async getMonthlyReturnsChart(backtestId: string): Promise<any> {
    return apiClient.get<any>(`/analytics/charts/${backtestId}/monthly_returns`);
  }

  static async getMetricsSummary(): Promise<any> {
    return apiClient.get<any>('/analytics/summary/metrics');
  }
}
