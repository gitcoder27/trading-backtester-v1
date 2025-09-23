import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useJobPolling } from '../useJobPolling';
import { JobService } from '../../services/backtest';

describe('useJobPolling', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('polls, updates progress, and calls onComplete', async () => {
    const onComplete = vi.fn();
    const initialJob = {
      id: '1',
      type: 'backtest' as const,
      status: 'running' as const,
      progress: 0,
      created_at: new Date().toISOString(),
    } as any;

    const spy = vi.spyOn(JobService, 'getJobStatus');
    spy.mockResolvedValueOnce({ ...initialJob, progress: 50, status: 'running' });
    spy.mockResolvedValueOnce({ ...initialJob, progress: 100, status: 'completed', completed_at: new Date().toISOString() });

    const { result } = renderHook(() => useJobPolling(initialJob, { onComplete, pollIntervalMs: 1000 }));

    expect(result.current.isPolling).toBe(true);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });
    expect(result.current.job.progress).toBe(50);
    expect(typeof result.current.estimatedTimeRemaining).toBe('string');

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });
    expect(onComplete).toHaveBeenCalledTimes(1);
    expect(result.current.job.status).toBe('completed');
    expect(result.current.isPolling).toBe(false);
  });

  it('does not auto-poll or call onComplete for completed initial job', () => {
    const onComplete = vi.fn();
    const initialJob = {
      id: '2',
      type: 'backtest' as const,
      status: 'completed' as const,
      progress: 100,
      created_at: new Date().toISOString(),
      completed_at: new Date().toISOString(),
    } as any;

    const { result } = renderHook(() => useJobPolling(initialJob, { onComplete }));

    expect(result.current.isPolling).toBe(false);
    expect(onComplete).not.toHaveBeenCalled();
  });
});
