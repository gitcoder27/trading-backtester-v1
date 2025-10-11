import { describe, it, expect, vi, beforeEach, afterEach, afterAll } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { useTradeData } from '../useTradeData';

const originalFetch = global.fetch;

const createWrapper = () => {
  const client = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
};

describe('useTradeData', () => {
  beforeEach(() => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        trades: [
          {
            id: 'trade-1',
            symbol: 'AAPL',
            side: 'buy',
            pnl: 100,
            entry_time: '2024-01-01T00:00:00Z',
            exit_time: '2024-01-01T01:00:00Z',
            entry_price: 100,
            exit_price: 110,
            quantity: 1,
            duration: 60,
          },
        ],
        total_trades: 1,
        total_pages: 2,
      }),
    }) as any;
  });

  afterEach(() => {
    (global.fetch as any).mockReset?.();
  });

  afterAll(() => {
    global.fetch = originalFetch;
  });

  it('fetches trades and updates sorting', async () => {
    const { result } = renderHook(() => useTradeData('bt-1'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/analytics/bt-1/trades?'));

    act(() => result.current.handleSort('pnl'));
    expect(result.current.sortBy).toBe('pnl');
    expect(result.current.sortOrder).toBe('desc');

    act(() => result.current.handleSort('pnl'));
    expect(result.current.sortOrder).toBe('asc');

    act(() => result.current.handleFilterChange(true));
    expect(result.current.filterProfitable).toBe(true);

    act(() => result.current.handlePageChange(2));
    expect(result.current.page).toBe(2);

    act(() => result.current.handlePageSizeChange(100));
    expect(result.current.pageSize).toBe(100);
    expect(result.current.page).toBe(1);

    act(() => result.current.handleSearchChange('AAPL'));
    expect(result.current.searchTerm).toBe('AAPL');
    expect(result.current.page).toBe(1);
  });

  it('handles fetch errors', async () => {
    (global.fetch as any).mockResolvedValueOnce({ ok: false, statusText: 'Server Error' });

    const { result } = renderHook(() => useTradeData('bt-err'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.error).toBeTruthy());
    expect(result.current.error?.message).toContain('Failed to fetch trades');
  });
});
