import { describe, it, expect, beforeEach, vi } from 'vitest';
import { BacktestService, JobService } from '../backtest';
import { apiClient } from '../api';
import type { BacktestConfig, BacktestResult, Job } from '../../types';

// Mock the API client
vi.mock('../api', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
    delete: vi.fn(),
    upload: vi.fn(),
  },
}));

const mockApiClient = vi.mocked(apiClient);

describe('BacktestService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('runBacktest', () => {
    it('should map frontend config to backend format and call API', async () => {
      const mockConfig: BacktestConfig = {
        strategy_id: 1,
        dataset_id: 2,
        initial_capital: 100000,
        position_size: 10,
        commission: 20,
        slippage: 0.01,
        start_date: '2024-01-01',
        end_date: '2024-12-31',
        parameters: { fast_ema: 10, slow_ema: 20 }
      };

      const mockResult: BacktestResult = {
        id: '123',
        status: 'completed',
        created_at: '2024-01-01T00:00:00Z',
        metrics: {
          total_return: 15.5,
          annual_return: 12.3,
          volatility: 8.7,
          sharpe_ratio: 1.41,
          max_drawdown: -5.2,
          win_rate: 0.65,
          profit_factor: 1.8,
          total_trades: 150
        }
      };

      mockApiClient.post.mockResolvedValue(mockResult);

      const result = await BacktestService.runBacktest(mockConfig);

      expect(mockApiClient.post).toHaveBeenCalledWith('/backtests', {
        strategy: '1',
        dataset: '2',
        strategy_params: { fast_ema: 10, slow_ema: 20 },
        engine_options: expect.objectContaining({
          initial_cash: 100000,
          lots: 10,
          fee_per_trade: 20,
          slippage: 0.01,
        })
      });
      expect(result).toEqual(mockResult);
    });

    it('should handle empty parameters', async () => {
      const mockConfig: BacktestConfig = {
        strategy_id: 1,
        dataset_id: 2,
        initial_capital: 100000,
        position_size: 10,
        commission: 20,
        slippage: 0.01,
        start_date: '2024-01-01',
        end_date: '2024-12-31'
      };

      mockApiClient.post.mockResolvedValue({ id: '123' });

      await BacktestService.runBacktest(mockConfig);

      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/backtests',
        expect.objectContaining({
          strategy_params: {},
          engine_options: expect.any(Object)
        })
      );
    });
  });

  describe('getBacktestResults', () => {
    it('should fetch backtest results by ID', async () => {
      const mockResult: BacktestResult = {
        id: '123',
        status: 'completed',
        created_at: '2024-01-01T00:00:00Z',
        metrics: {
          total_return: 15.5,
          annual_return: 12.3,
          volatility: 8.7,
          sharpe_ratio: 1.41,
          max_drawdown: -5.2,
          win_rate: 0.65,
          profit_factor: 1.8,
          total_trades: 150
        }
      };

      mockApiClient.get.mockResolvedValue(mockResult);

      const result = await BacktestService.getBacktestResults('123');

      expect(mockApiClient.get).toHaveBeenCalledWith('/backtests/123/results');
      expect(result).toEqual(mockResult);
    });
  });

  describe('getBacktest', () => {
    it('should fetch backtest by ID', async () => {
      const mockBacktest = { id: '123', name: 'Test Backtest' };
      mockApiClient.get.mockResolvedValue(mockBacktest);

      const result = await BacktestService.getBacktest('123');

      // Service passes an empty params object for consistency
      expect(mockApiClient.get).toHaveBeenCalledWith('/backtests/123', {});
      expect(result).toEqual(mockBacktest);
    });
  });

  describe('listBacktests', () => {
    it('should list backtests without parameters', async () => {
      const mockResponse = {
        items: [{ id: '1' }, { id: '2' }],
        total: 2,
        page: 1,
        page_size: 20,
        total_pages: 1
      };

      mockApiClient.get.mockResolvedValue(mockResponse);

      const result = await BacktestService.listBacktests();

      expect(mockApiClient.get).toHaveBeenCalledWith('/backtests', undefined);
      expect(result).toEqual(mockResponse);
    });

    it('should list backtests with pagination parameters', async () => {
      const params = { page: 2, page_size: 10 };
      const mockResponse = {
        items: [{ id: '3' }],
        total: 1,
        page: 2,
        page_size: 10,
        total_pages: 1
      };

      mockApiClient.get.mockResolvedValue(mockResponse);

      const result = await BacktestService.listBacktests(params);

      expect(mockApiClient.get).toHaveBeenCalledWith('/backtests', params);
      expect(result).toEqual(mockResponse);
    });
  });

  describe('uploadAndRunBacktest', () => {
    it('should upload file and run backtest', async () => {
      const file = new File(['test'], 'test.csv', { type: 'text/csv' });
      const config = { initial_capital: 50000 };
      const mockResult: BacktestResult = {
        id: '456',
        status: 'completed',
        created_at: '2024-01-01T00:00:00Z',
        metrics: {
          total_return: 10.0,
          annual_return: 8.5,
          volatility: 12.0,
          sharpe_ratio: 0.71,
          max_drawdown: -8.5,
          win_rate: 0.55,
          profit_factor: 1.2,
          total_trades: 75
        }
      };

      mockApiClient.upload.mockResolvedValue(mockResult);

      const result = await BacktestService.uploadAndRunBacktest(file, config);

      expect(mockApiClient.upload).toHaveBeenCalledWith(
        '/backtests/upload',
        expect.any(FormData)
      );
      expect(result).toEqual(mockResult);
    });
  });

  describe('deleteBacktest', () => {
    it('should delete backtest by ID', async () => {
      mockApiClient.delete.mockResolvedValue(undefined);

      await BacktestService.deleteBacktest('123');

      expect(mockApiClient.delete).toHaveBeenCalledWith('/backtests/123');
    });
  });

  describe('getChartData', () => {
    it('should fetch chart data without options', async () => {
      const mockChartData = { equity: [], drawdown: [] };
      mockApiClient.get.mockResolvedValue(mockChartData);

      const result = await BacktestService.getChartData('123');

      expect(mockApiClient.get).toHaveBeenCalledWith('/analytics/chart-data/123');
      expect(result).toEqual(mockChartData);
    });

    it('should fetch chart data with options', async () => {
      const options = {
        includeTrades: true,
        includeIndicators: false,
        maxCandles: 1000
      };
      const mockChartData = { equity: [], drawdown: [], trades: [] };
      mockApiClient.get.mockResolvedValue(mockChartData);

      const result = await BacktestService.getChartData('123', options);

      expect(mockApiClient.get).toHaveBeenCalledWith(
        '/analytics/chart-data/123?include_trades=true&include_indicators=false&max_candles=1000'
      );
      expect(result).toEqual(mockChartData);
    });

    it('should skip undefined options', async () => {
      const options = {
        includeTrades: undefined,
        includeIndicators: true
      };
      const mockChartData = { equity: [], indicators: [] };
      mockApiClient.get.mockResolvedValue(mockChartData);

      await BacktestService.getChartData('123', options);

      expect(mockApiClient.get).toHaveBeenCalledWith(
        '/analytics/chart-data/123?include_indicators=true'
      );
    });
  });
});

describe('JobService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('submitBackgroundJob', () => {
    it('should submit background job with mapped config', async () => {
      const mockConfig: BacktestConfig = {
        strategy_id: 1,
        dataset_id: 2,
        initial_capital: 100000,
        position_size: 10,
        commission: 20,
        slippage: 0.01,
        start_date: '2024-01-01',
        end_date: '2024-12-31',
        parameters: { fast_ema: 10 }
      };

      const mockJob: Job = {
        id: 'job-123',
        type: 'backtest',
        status: 'queued',
        progress: 0,
        created_at: '2024-01-01T00:00:00Z'
      };

      mockApiClient.post.mockResolvedValue(mockJob);

      const result = await JobService.submitBackgroundJob(mockConfig);

      expect(mockApiClient.post).toHaveBeenCalledWith('/jobs/', {
        strategy: '1',
        dataset: '2',
        strategy_params: { fast_ema: 10 },
        engine_options: expect.objectContaining({
          initial_cash: 100000,
          lots: 10,
          fee_per_trade: 20,
          slippage: 0.01,
        })
      });
      expect(result).toEqual(mockJob);
    });
  });

  describe('getJobStatus', () => {
    it('should fetch job status by ID', async () => {
      const mockJob: Job = {
        id: 'job-123',
        type: 'backtest',
        status: 'running',
        progress: 50,
        created_at: '2024-01-01T00:00:00Z'
      };

      mockApiClient.get.mockResolvedValue(mockJob);

      const result = await JobService.getJobStatus('job-123');

      expect(mockApiClient.get).toHaveBeenCalledWith('/jobs/job-123/status');
      expect(result).toEqual(mockJob);
    });
  });

  describe('getJobResults', () => {
    it('should fetch job results by ID', async () => {
      const mockResults = { 
        id: '123',
        metrics: { total_return: 15.5 },
        trades: []
      };

      mockApiClient.get.mockResolvedValue(mockResults);

      const result = await JobService.getJobResults('job-123');

      expect(mockApiClient.get).toHaveBeenCalledWith('/jobs/job-123/results');
      expect(result).toEqual(mockResults);
    });
  });

  describe('cancelJob', () => {
    it('should cancel job by ID', async () => {
      const mockResponse = { message: 'Job cancelled successfully' };
      mockApiClient.post.mockResolvedValue(mockResponse);

      const result = await JobService.cancelJob('job-123');

      expect(mockApiClient.post).toHaveBeenCalledWith('/jobs/job-123/cancel');
      expect(result).toEqual(mockResponse);
    });
  });

  describe('listJobs', () => {
    it('should list jobs without parameters', async () => {
      const mockResponse = {
        items: [
          { id: 'job-1', type: 'backtest', status: 'completed' },
          { id: 'job-2', type: 'optimization', status: 'running' }
        ],
        total: 2,
        page: 1,
        page_size: 20,
        total_pages: 1
      };

      mockApiClient.get.mockResolvedValue(mockResponse);

      const result = await JobService.listJobs();

      expect(mockApiClient.get).toHaveBeenCalledWith('/jobs', undefined);
      expect(result).toEqual(mockResponse);
    });

    it('should list jobs with parameters', async () => {
      const params = { page: 1, page_size: 10, status: 'completed' };
      const mockResponse = {
        items: [{ id: 'job-1', status: 'completed' }],
        total: 1,
        page: 1,
        page_size: 10,
        total_pages: 1
      };

      mockApiClient.get.mockResolvedValue(mockResponse);

      const result = await JobService.listJobs(params);

      expect(mockApiClient.get).toHaveBeenCalledWith('/jobs', params);
      expect(result).toEqual(mockResponse);
    });
  });
});
