import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';

import JobActions from '../JobsList/JobActions';
import JobCard from '../JobsList/JobCard';
import JobFilters from '../JobsList/JobFilters';
import JobsList from '../JobsList';

const toastMock = {
  success: vi.fn(),
  error: vi.fn(),
  warning: vi.fn(),
  info: vi.fn(),
};

vi.mock('../../ui/Toast', () => ({
  showToast: toastMock,
  ToastProvider: () => null,
  default: () => null,
}));

const useJobManagementMock = vi.fn();

vi.mock('../JobsList/useJobManagement', () => ({
  useJobManagement: (...args: unknown[]) => useJobManagementMock(...args),
}));

vi.mock('../JobProgressTracker', () => ({
  __esModule: true,
  default: ({ job }: { job: { id: string } }) => (
    <div data-testid="job-progress" data-job-id={job.id} />
  ),
}));

const baseJob = {
  id: 'job-1',
  status: 'running',
  created_at: '2024-01-01T00:00:00Z',
  completed_at: null,
  progress: 50,
  type: 'backtest',
  error: undefined,
};

describe('Jobs list components', () => {
  beforeEach(() => {
    Object.values(toastMock).forEach((fn) => fn.mockReset());
    useJobManagementMock.mockReset();
  });

  it('renders JobActions buttons according to status', () => {
    const onCancel = vi.fn();
    const onDelete = vi.fn();
    const onDownload = vi.fn();

    const { rerender } = render(
      <JobActions
        job={{ ...baseJob, status: 'running' }}
        onCancel={onCancel}
        onDelete={onDelete}
        onDownload={onDownload}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /Cancel/ }));
    expect(onCancel).toHaveBeenCalledWith('job-1');

    rerender(
      <JobActions
        job={{ ...baseJob, status: 'completed' }}
        onCancel={onCancel}
        onDelete={onDelete}
        onDownload={onDownload}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /Download/ }));
    fireEvent.click(screen.getByRole('button', { name: /Delete/ }));

    expect(onDownload).toHaveBeenCalledWith('job-1');
    expect(onDelete).toHaveBeenCalledWith('job-1');
  });

  it('renders JobCard with meta information and actions', () => {
    const onClick = vi.fn();
    const onCancel = vi.fn();
    const onDelete = vi.fn();
    const onDownload = vi.fn();

    render(
      <JobCard
        job={{ ...baseJob, status: 'failed', error: 'Network error', progress: 100 }}
        onCancel={onCancel}
        onDelete={onDelete}
        onDownload={onDownload}
        onClick={onClick}
      />
    );

    expect(screen.getByText(/Job #job-1/)).toBeInTheDocument();
    expect(screen.getByText(/Network error/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Delete/ }));
    expect(onDelete).toHaveBeenCalledWith('job-1');
  });

  it('JobFilters forwards user interactions', () => {
    const onSearchChange = vi.fn();
    const onStatusFilterChange = vi.fn();
    const onSortChange = vi.fn();

    render(
      <JobFilters
        searchTerm=""
        onSearchChange={onSearchChange}
        statusFilter="all"
        onStatusFilterChange={onStatusFilterChange}
        sortBy="created_at"
        sortOrder="desc"
        onSortChange={onSortChange}
      />
    );

    fireEvent.change(screen.getByPlaceholderText('Search jobs...'), { target: { value: 'abc' } });
    fireEvent.change(screen.getByDisplayValue('All Status'), { target: { value: 'completed' } });
    fireEvent.change(screen.getByDisplayValue('Newest First'), { target: { value: 'status-asc' } });

    expect(onSearchChange).toHaveBeenCalledWith('abc');
    expect(onStatusFilterChange).toHaveBeenCalledWith('completed');
    expect(onSortChange).toHaveBeenCalledWith('status', 'asc');
  });

  it('renders JobsList in detailed mode', () => {
    const state = {
      jobs: [{ ...baseJob, status: 'running' }],
      totalCount: 1,
      loading: false,
      isRefreshing: false,
      searchTerm: '',
      statusFilter: 'all',
      sortBy: 'created_at',
      sortOrder: 'desc',
      page: 1,
      totalPages: 1,
      handleRefresh: vi.fn(),
      handleSearch: vi.fn(),
      handleStatusFilterChange: vi.fn(),
      handleSortChange: vi.fn(),
      handleCancelJob: vi.fn(),
      handleDownloadResults: vi.fn(),
      handleDeleteJob: vi.fn(),
      setPage: vi.fn(),
    };
    useJobManagementMock.mockReturnValue(state);

    render(<JobsList compact={false} />);

    expect(screen.getByText(/Background Jobs/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Refresh/ }));
    expect(state.handleRefresh).toHaveBeenCalled();
  });

  it('renders JobsList compact view fallback', () => {
    useJobManagementMock.mockReturnValue({
      jobs: [],
      totalCount: 0,
      loading: false,
      isRefreshing: false,
      searchTerm: '',
      statusFilter: 'all',
      sortBy: 'created_at',
      sortOrder: 'desc',
      page: 1,
      totalPages: 1,
      handleRefresh: vi.fn(),
      handleSearch: vi.fn(),
      handleStatusFilterChange: vi.fn(),
      handleSortChange: vi.fn(),
      handleCancelJob: vi.fn(),
      handleDownloadResults: vi.fn(),
      handleDeleteJob: vi.fn(),
      setPage: vi.fn(),
    });

    render(<JobsList compact maxJobs={3} />);
    expect(screen.getByText(/No jobs found/)).toBeInTheDocument();
  });
});
