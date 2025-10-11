import { describe, it, expect, vi, beforeEach } from 'vitest';

const mockApi = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
}));

vi.mock('../api', () => ({
  apiClient: mockApi,
}));

import { OptimizationService } from '../optimization';

const sampleRequest = {
  strategy: 'strategy-1',
  dataset: 'dataset-1',
  parameter_ranges: { lookback: { min: 5, max: 20, step: 1 } },
  metric: 'sharpe_ratio',
};

describe('OptimizationService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('starts optimization jobs', async () => {
    mockApi.post.mockResolvedValue({ id: 'job-1', status: 'queued' });
    const job = await OptimizationService.startOptimization(sampleRequest);
    expect(mockApi.post).toHaveBeenCalledWith('/optimize', sampleRequest);
    expect(job.id).toBe('job-1');
  });

  it('lists optimization jobs', async () => {
    mockApi.get.mockResolvedValue({ items: [], total: 0, page: 1, limit: 10, pages: 0 });
    await OptimizationService.listOptimizationJobs({ page: 1, limit: 10 });
    expect(mockApi.get).toHaveBeenCalledWith('/optimize', { page: 1, limit: 10 });
  });

  it('fetches job status and results', async () => {
    mockApi.get.mockResolvedValueOnce({ id: 'job-1', status: 'running' });
    await OptimizationService.getOptimizationStatus('job-1');
    expect(mockApi.get).toHaveBeenCalledWith('/optimize/job-1/status');

    mockApi.get.mockResolvedValueOnce({ best_parameters: {}, best_score: 1, results: [] });
    await OptimizationService.getOptimizationResults('job-1');
    expect(mockApi.get).toHaveBeenCalledWith('/optimize/job-1/results');
  });

  it('cancels optimization', async () => {
    mockApi.post.mockResolvedValue(undefined);
    await OptimizationService.cancelOptimization('job-1');
    expect(mockApi.post).toHaveBeenCalledWith('/optimize/job-1/cancel');
  });

  it('retrieves stats, metrics, validation, and quick optimization', async () => {
    mockApi.get.mockResolvedValueOnce({ total_jobs: 5 });
    await OptimizationService.getOptimizationStats();
    expect(mockApi.get).toHaveBeenCalledWith('/optimize/stats/summary');

    mockApi.post.mockResolvedValue({ valid: true });
    await OptimizationService.validateOptimizationRequest(sampleRequest);
    expect(mockApi.post).toHaveBeenCalledWith('/optimize/validate', sampleRequest);

    mockApi.get.mockResolvedValueOnce(['sharpe_ratio']);
    await OptimizationService.getAvailableOptimizationMetrics();
    expect(mockApi.get).toHaveBeenCalledWith('/optimize/metrics');

    mockApi.post.mockResolvedValue({ best_parameters: { lookback: 10 }, best_score: 1.2, results: [] });
    await OptimizationService.quickOptimization(sampleRequest);
    expect(mockApi.post).toHaveBeenCalledWith('/optimize/quick', sampleRequest);
  });
});
