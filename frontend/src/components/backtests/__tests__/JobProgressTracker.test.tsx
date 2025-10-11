import { describe, it, expect, vi, beforeEach, afterEach, type SpyInstance } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';

const toastMock = vi.hoisted(() => ({
  success: vi.fn(),
  error: vi.fn(),
  warning: vi.fn(),
}));

vi.mock('../../ui/Toast', () => ({
  showToast: toastMock,
  ToastProvider: () => null,
  default: () => null,
}));

const useJobPollingMock = vi.hoisted(() => vi.fn());

vi.mock('../../../hooks/useJobPolling', () => ({
  useJobPolling: (...args: unknown[]) => useJobPollingMock(...args),
}));

const cancelJobMock = vi.hoisted(() => vi.fn());
const getJobResultsMock = vi.hoisted(() => vi.fn());

vi.mock('../../../services/backtest', () => ({
  JobService: {
    cancelJob: cancelJobMock,
    getJobResults: getJobResultsMock,
  },
}));

import JobProgressTracker from '../JobProgressTracker';

type TestJob = {
  id: string;
  status: string;
  created_at: string;
  completed_at: string | null;
  progress: number;
  type: string;
  error?: string | null;
};

const baseJob: TestJob = {
  id: 'job-1',
  status: 'running',
  created_at: '2024-01-01T00:00:00Z',
  completed_at: null,
  progress: 50,
  type: 'backtest',
};

const createPollingState = (overrides: Partial<TestJob> = {}, opts: Partial<{ isPolling: boolean; eta: string }> = {}) => {
  const job = { ...baseJob, ...overrides };
  const setJob = vi.fn((updater: any) => {
    if (typeof updater === 'function') {
      updater(job);
    }
  });
  return {
    job,
    setJob,
    isPolling: opts.isPolling ?? false,
    estimatedTimeRemaining: opts.eta ?? '5m',
  };
};

describe('JobProgressTracker', () => {
  let anchorClickSpy: SpyInstance;

  beforeEach(() => {
    Object.values(toastMock).forEach((fn) => fn.mockReset());
    cancelJobMock.mockReset();
    getJobResultsMock.mockReset();
    useJobPollingMock.mockReset();
    (global.URL as any).createObjectURL = vi.fn(() => 'blob://test');
    (global.URL as any).revokeObjectURL = vi.fn();
    anchorClickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
  });

  afterEach(() => {
    anchorClickSpy.mockRestore();
  });

  it('renders compact view summary', () => {
    const polling = createPollingState({}, { eta: '10m' });
    useJobPollingMock.mockReturnValue(polling);

    render(<JobProgressTracker job={baseJob as any} compact showActions={false} />);

    expect(screen.getByText(/Job job-1/)).toBeInTheDocument();
  });

  it('cancels running job and notifies user', async () => {
    const polling = createPollingState({ status: 'running', progress: 80 });
    useJobPollingMock.mockReturnValue(polling);
    cancelJobMock.mockResolvedValue(undefined);

    render(<JobProgressTracker job={baseJob as any} />);

    fireEvent.click(screen.getByRole('button', { name: /Cancel/ }));

    await waitFor(() => expect(cancelJobMock).toHaveBeenCalledWith('job-1'));
    expect(polling.setJob).toHaveBeenCalled();
    expect(toastMock.warning).toHaveBeenCalled();
  });

  it('downloads results for completed job', async () => {
    const polling = createPollingState({ status: 'completed', progress: 100 });
    useJobPollingMock.mockReturnValue(polling);
    getJobResultsMock.mockResolvedValue({ metrics: { total_return: 1.2 } });

    render(<JobProgressTracker job={{ ...baseJob, status: 'completed' } as any} />);

    fireEvent.click(screen.getByRole('button', { name: /Download Results/ }));

    await waitFor(() => expect(getJobResultsMock).toHaveBeenCalledWith('job-1'));
    expect(toastMock.success).toHaveBeenCalled();
  });
});
