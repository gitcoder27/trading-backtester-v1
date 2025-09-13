import { describe, it, expect, beforeEach, vi } from 'vitest';
import { AnalyticsService } from '../analytics';
import { apiClient } from '../api';

// Mock the API client
vi.mock('../api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const mockApiClient = vi.mocked(apiClient);

describe('AnalyticsService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getPerformanceSummary', () => {
    it('should fetch performance summary by backtest ID', async () => {
      const mockSummary = {
        total_return: 15.5,
        annual_return: 12.3,
        volatility: 8.7,
        sharpe_ratio: 1.41,
        max_drawdown: -5.2,
        win_rate: 0.65,
        profit_factor: 1.8,
        total_trades: 150,
        winning_trades: 98,
        losing_trades: 52,
        avg_win: 1250,
        avg_loss: -680,
        largest_win: 5000,
        largest_loss: -2500
      };

      mockApiClient.get.mockResolvedValue(mockSummary);

      const result = await AnalyticsService.getPerformanceSummary('123');

      // Service now passes a params object (possibly empty)
      expect(mockApiClient.get).toHaveBeenCalledWith('/analytics/performance/123', {});
      expect(result).toEqual(mockSummary);
    });

    it('should handle API errors gracefully', async () => {
      mockApiClient.get.mockRejectedValue(new Error('Network error'));

      await expect(AnalyticsService.getPerformanceSummary('123')).rejects.toThrow('Network error');
    });
  });

  describe('getCharts', () => {
    it('should fetch charts data by backtest ID', async () => {
      const mockCharts = {
        equity: {
          x: ['2024-01-01', '2024-01-02', '2024-01-03'],
          y: [100000, 101000, 102000],
          type: 'scatter',
          mode: 'lines'
        },
        drawdown: {
          x: ['2024-01-01', '2024-01-02', '2024-01-03'],
          y: [0, -1.2, -0.8],
          type: 'scatter',
          mode: 'lines'
        }
      };

      mockApiClient.get.mockResolvedValue(mockCharts);

      const result = await AnalyticsService.getCharts('123');

      // Service now passes a params object (possibly empty)
      expect(mockApiClient.get).toHaveBeenCalledWith('/analytics/charts/123', {});
      expect(result).toEqual(mockCharts);
    });
  });

  describe('compareStrategies', () => {
    it('should compare multiple strategies', async () => {
      const compareRequest = {
        strategy_ids: ['1', '2', '3'],
        metrics: ['total_return', 'sharpe_ratio', 'max_drawdown']
      };

      const mockComparison = {
        strategies: [
          { 
            id: '1',
            name: 'Strategy 1',
            metrics: { total_return: 15.5, sharpe_ratio: 1.41 }
          },
          { 
            id: '2',
            name: 'Strategy 2',
            metrics: { total_return: 18.2, sharpe_ratio: 1.65 }
          }
        ],
        correlation_matrix: [[1.0, 0.75], [0.75, 1.0]]
      };

      mockApiClient.post.mockResolvedValue(mockComparison);

      const result = await AnalyticsService.compareStrategies(compareRequest);

      expect(mockApiClient.post).toHaveBeenCalledWith('/analytics/compare', compareRequest);
      expect(result).toEqual(mockComparison);
    });

    it('should handle empty strategy list', async () => {
      const compareRequest = { strategy_ids: [] };

      mockApiClient.post.mockResolvedValue({ strategies: [] });

      const result = await AnalyticsService.compareStrategies(compareRequest);

      expect(result).toEqual({ strategies: [] });
    });
  });

  describe('getEquityChart', () => {
    it('should fetch equity chart data', async () => {
      const mockEquityChart = {
        x: ['2024-01-01', '2024-01-02', '2024-01-03'],
        y: [100000, 101500, 102300],
        type: 'scatter',
        mode: 'lines',
        name: 'Equity Curve'
      };

      mockApiClient.get.mockResolvedValue(mockEquityChart);

      const result = await AnalyticsService.getEquityChart('123');

      // Service now passes a params object (possibly empty)
      expect(mockApiClient.get).toHaveBeenCalledWith('/analytics/charts/123/equity', {});
      expect(result).toEqual(mockEquityChart);
    });
  });

  describe('getDrawdownChart', () => {
    it('should fetch drawdown chart data', async () => {
      const mockDrawdownChart = {
        x: ['2024-01-01', '2024-01-02', '2024-01-03'],
        y: [0, -2.1, -1.5],
        type: 'scatter',
        mode: 'lines',
        name: 'Drawdown',
        fill: 'tonexty'
      };

      mockApiClient.get.mockResolvedValue(mockDrawdownChart);

      const result = await AnalyticsService.getDrawdownChart('123');

      // Service now passes a params object (possibly empty)
      expect(mockApiClient.get).toHaveBeenCalledWith('/analytics/charts/123/drawdown', {});
      expect(result).toEqual(mockDrawdownChart);
    });
  });

  describe('getReturnsChart', () => {
    it('should fetch returns chart data', async () => {
      const mockReturnsChart = {
        x: ['2024-01-01', '2024-01-02', '2024-01-03'],
        y: [0, 1.5, 2.3],
        type: 'bar',
        name: 'Daily Returns'
      };

      mockApiClient.get.mockResolvedValue(mockReturnsChart);

      const result = await AnalyticsService.getReturnsChart('123');

      expect(mockApiClient.get).toHaveBeenCalledWith('/analytics/charts/123/returns');
      expect(result).toEqual(mockReturnsChart);
    });
  });

  describe('getTradesChart', () => {
    it('should fetch trades chart data', async () => {
      const mockTradesChart = {
        x: ['2024-01-01', '2024-01-02', '2024-01-03'],
        y: [5, 8, 3],
        type: 'bar',
        name: 'Trades per Day'
      };

      mockApiClient.get.mockResolvedValue(mockTradesChart);

      const result = await AnalyticsService.getTradesChart('123');

      // Service now passes a params object (possibly empty)
      expect(mockApiClient.get).toHaveBeenCalledWith('/analytics/charts/123/trades', {});
      expect(result).toEqual(mockTradesChart);
    });
  });

  describe('getMonthlyReturnsChart', () => {
    it('should fetch monthly returns chart data', async () => {
      const mockMonthlyChart = {
        x: ['Jan', 'Feb', 'Mar', 'Apr'],
        y: [2.5, 1.8, 3.2, -0.5],
        type: 'bar',
        name: 'Monthly Returns'
      };

      mockApiClient.get.mockResolvedValue(mockMonthlyChart);

      const result = await AnalyticsService.getMonthlyReturnsChart('123');

      expect(mockApiClient.get).toHaveBeenCalledWith('/analytics/charts/123/monthly_returns');
      expect(result).toEqual(mockMonthlyChart);
    });
  });

  describe('getMetricsSummary', () => {
    it('should fetch overall metrics summary', async () => {
      const mockMetricsSummary = {
        total_backtests: 150,
        total_strategies: 25,
        avg_annual_return: 12.5,
        avg_sharpe_ratio: 1.35,
        avg_max_drawdown: -6.8,
        best_performing_strategy: {
          id: '5',
          name: 'Advanced EMA',
          total_return: 45.2
        },
        recent_activity: {
          backtests_last_7_days: 12,
          backtests_last_30_days: 48
        }
      };

      mockApiClient.get.mockResolvedValue(mockMetricsSummary);

      const result = await AnalyticsService.getMetricsSummary();

      expect(mockApiClient.get).toHaveBeenCalledWith('/analytics/summary/metrics');
      expect(result).toEqual(mockMetricsSummary);
    });
  });

  describe('Error handling', () => {
    it('should propagate API errors for performance summary', async () => {
      const errorMessage = 'Backtest not found';
      mockApiClient.get.mockRejectedValue(new Error(errorMessage));

      await expect(AnalyticsService.getPerformanceSummary('invalid-id')).rejects.toThrow(errorMessage);
    });

    it('should propagate API errors for chart data', async () => {
      const errorMessage = 'Chart data unavailable';
      mockApiClient.get.mockRejectedValue(new Error(errorMessage));

      await expect(AnalyticsService.getEquityChart('invalid-id')).rejects.toThrow(errorMessage);
    });

    it('should propagate API errors for strategy comparison', async () => {
      const errorMessage = 'Invalid strategy IDs';
      mockApiClient.post.mockRejectedValue(new Error(errorMessage));

      await expect(AnalyticsService.compareStrategies({ strategy_ids: ['invalid'] })).rejects.toThrow(errorMessage);
    });
  });

  describe('Data validation', () => {
    it('should handle empty chart data gracefully', async () => {
      const emptyChart = { x: [], y: [], type: 'scatter', mode: 'lines' };
      mockApiClient.get.mockResolvedValue(emptyChart);

      const result = await AnalyticsService.getEquityChart('123');

      expect(result.x).toEqual([]);
      expect(result.y).toEqual([]);
    });

    it('should handle null/undefined responses', async () => {
      mockApiClient.get.mockResolvedValue(null);

      const result = await AnalyticsService.getPerformanceSummary('123');

      expect(result).toBeNull();
    });
  });
});
