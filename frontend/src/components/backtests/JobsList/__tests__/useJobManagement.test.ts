import { describe, it, expect, vi, beforeEach, afterEach, afterAll, type SpyInstance } from 'vitest';
import { renderHook, act } from '@testing-library/react';

const toastMock = vi.hoisted(() => ({
  success: vi.fn(),
  error: vi.fn(),
  warning: vi.fn(),
}));

vi.mock('../../../ui/Toast', () => ({
  showToast: toastMock,
  ToastProvider: () => null,
  default: () => null,
}));

const useJobsQueryMock = vi.hoisted(() => vi.fn());

vi.mock('../../../../hooks/useJobsQuery', () => ({
  useJobsQuery: (...args: unknown[]) => useJobsQueryMock(...args),
}));

const jobServiceMock = vi.hoisted(() => ({
  cancelJob: vi.fn(),
  getJobResults: vi.fn(),
  deleteJob: vi.fn(),
}));

vi.mock('../../../../services/backtest', () => ({
  JobService: jobServiceMock,
}));

import { useJobManagement } from '../useJobManagement';

const jobs = [
  { id: 'job-a', status: 'completed', created_at: '2024-01-03T00:00:00Z', progress: 100, type: 'backtest' },
  { id: 'job-b', status: 'running', created_at: '2024-01-01T00:00:00Z', progress: 10, type: 'optimization' },
];

const refetchMock = vi.fn(() => Promise.resolve());

const setQueryState = (overrides: Record<string, unknown> = {}) => {
  useJobsQueryMock.mockReturnValue({
    data: { jobs },
    isLoading: false,
    isFetching: false,
    isError: false,
    error: null,
    refetch: refetchMock,
    ...overrides,
  });
};

describe('useJobManagement', () => {
  const originalCreate = global.URL?.createObjectURL;
  const originalRevoke = global.URL?.revokeObjectURL;
  const confirmOriginal = global.confirm;
  const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
  let anchorClickSpy: SpyInstance;

  beforeEach(() => {
    refetchMock.mockClear();
    Object.values(toastMock).forEach((fn) => fn.mockReset());
    Object.values(jobServiceMock).forEach((fn) => fn.mockReset());
    (global.URL as any).createObjectURL = vi.fn(() => 'blob://results');
    (global.URL as any).revokeObjectURL = vi.fn();
    global.confirm = vi.fn(() => true);
    anchorClickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
    setQueryState();
  });

  afterEach(() => {
    (global.URL as any).createObjectURL = originalCreate;
    (global.URL as any).revokeObjectURL = originalRevoke;
    global.confirm = confirmOriginal;
    anchorClickSpy.mockRestore();
  });

  afterEach(() => {
    consoleErrorSpy.mockClear();
  });

  afterAll(() => {
    consoleErrorSpy.mockRestore();
  });

  it('returns sorted jobs and supports search and status filters', () => {
    const { result } = renderHook(() => useJobManagement());

    expect(result.current.jobs[0].id).toBe('job-a');

    act(() => result.current.handleSearch('job-b'));
    expect(result.current.jobs).toHaveLength(1);

    act(() => result.current.handleSearch(''));
    act(() => result.current.handleStatusFilterChange('completed'));
    expect(result.current.jobs[0].id).toBe('job-a');
  });

  it('refreshes jobs and notifies user', async () => {
    const { result } = renderHook(() => useJobManagement());

    await act(async () => {
      await result.current.handleRefresh();
    });

    expect(refetchMock).toHaveBeenCalled();
    expect(toastMock.success).toHaveBeenCalledWith('Jobs refreshed');
  });

  it('cancels job and triggers warning toast', async () => {
    jobServiceMock.cancelJob.mockResolvedValue(undefined);
    const { result } = renderHook(() => useJobManagement());

    await act(async () => {
      await result.current.handleCancelJob('job-a');
    });

    expect(jobServiceMock.cancelJob).toHaveBeenCalledWith('job-a');
    expect(refetchMock).toHaveBeenCalled();
    expect(toastMock.warning).toHaveBeenCalledWith('Job cancelled');
  });

  it('downloads results and revokes blob url', async () => {
    jobServiceMock.getJobResults.mockResolvedValue({ foo: 'bar' });
    const appendSpy = vi.spyOn(document.body, 'appendChild');
    const removeSpy = vi.spyOn(document.body, 'removeChild');

    const { result } = renderHook(() => useJobManagement());

    await act(async () => {
      await result.current.handleDownloadResults('job-a');
    });

    expect(jobServiceMock.getJobResults).toHaveBeenCalledWith('job-a');
    expect(appendSpy).toHaveBeenCalled();
    expect(removeSpy).toHaveBeenCalled();
    expect(toastMock.success).toHaveBeenCalledWith('Results downloaded');

    appendSpy.mockRestore();
    removeSpy.mockRestore();
  });

  it('deletes job after confirmation', async () => {
    jobServiceMock.deleteJob.mockResolvedValue(undefined);
    const { result } = renderHook(() => useJobManagement());

    await act(async () => {
      await result.current.handleDeleteJob('job-b');
    });

    expect(jobServiceMock.deleteJob).toHaveBeenCalledWith('job-b');
    expect(toastMock.success).toHaveBeenCalledWith('Job deleted successfully');
  });

  it('does not delete when confirmation fails', async () => {
    (global.confirm as any).mockReturnValue(false);
    const { result } = renderHook(() => useJobManagement());

    await act(async () => {
      await result.current.handleDeleteJob('job-b');
    });

    expect(jobServiceMock.deleteJob).not.toHaveBeenCalled();
  });

  it('emits toast on query error', () => {
    setQueryState({ isError: true, error: new Error('boom') });
    renderHook(() => useJobManagement());
    expect(toastMock.error).toHaveBeenCalledWith('Failed to load jobs');
  });
});
