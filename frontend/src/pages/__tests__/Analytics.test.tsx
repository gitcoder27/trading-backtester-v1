import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Analytics from '../Analytics/Analytics';

// Mock search params to include a backtest id
vi.mock('react-router-dom', async (orig) => {
  const actual: any = await orig();
  return {
    ...actual,
    useSearchParams: () => [new URLSearchParams({ backtest_id: '123' })],
    Link: ({ children }: any) => <a>{children}</a>,
  };
});

// Mock heavy child components
vi.mock('../../components/charts', () => ({
  __esModule: true,
  EquityChart: () => <div>EquityChart</div>,
  DrawdownChart: () => <div>DrawdownChart</div>,
  PriceChartPanel: () => <div>PriceChartPanel</div>,
}));
vi.mock('../../components/analytics/AdvancedMetrics', () => ({
  __esModule: true,
  default: ({ backtestId }: any) => <div>AdvancedMetrics {backtestId}</div>,
}));

// Mock service
vi.mock('../../services/backtest', () => ({
  BacktestService: {
    getBacktest: vi.fn().mockResolvedValue({ id: '123', strategy_name: 'My.Strategy', status: 'completed' }),
  },
}));

describe('Analytics page', () => {
  it('renders overview with charts and metrics', async () => {
    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter>
          <Analytics />
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(await screen.findByText(/AdvancedMetrics 123/)).toBeInTheDocument();
    expect(screen.getAllByText(/EquityChart|DrawdownChart/).length).toBeGreaterThan(0);
  });
});

