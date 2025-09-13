import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Dashboard from '../Dashboard/Dashboard';

// Mock data hook
vi.mock('../Dashboard/hooks/useDashboardData', () => ({
  useDashboardData: () => ({
    loading: false,
    recentBacktests: [],
    recentJobs: [],
    latestCompletedBacktestId: '1',
    topStrategies: [],
    mostTestedStrategies: [],
    datasetSummary: { total_datasets: 1, total_records: 1000 },
  })
}));

// Mock modal to a simple stub
vi.mock('../../components/modals/BacktestModal', () => ({
  __esModule: true,
  default: (props: any) => props.isOpen ? <div>Modal Open</div> : null,
}));

describe('Dashboard page', () => {
  it('renders and opens backtest modal', () => {
    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter>
          <Dashboard />
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(screen.getByText('Welcome back')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /run backtest/i }));
    expect(screen.getByText('Modal Open')).toBeInTheDocument();
  });
});
