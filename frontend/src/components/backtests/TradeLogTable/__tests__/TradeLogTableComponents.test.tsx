import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';

import TableHeader from '../TableHeader';
import SortableTableHeader from '../SortableTableHeader';
import TradeRow from '../TradeRow';
import Pagination from '../Pagination';
import TradeLogTable from '..';

const useTradeDataMock = vi.fn();
const exportCsvMock = vi.fn();

vi.mock('../useTradeData', () => ({
  useTradeData: (...args: unknown[]) => useTradeDataMock(...args),
}));

vi.mock('../ExportControls', () => ({
  useExportCSV: () => ({ exportToCSV: exportCsvMock }),
}));

const sampleTrade = {
  id: 'trade-1',
  entry_time: '2024-01-01T00:00:00Z',
  exit_time: '2024-01-01T01:00:00Z',
  symbol: 'AAPL',
  side: 'buy',
  entry_price: 100,
  exit_price: 110,
  quantity: 10,
  pnl: 100,
  pnl_pct: 10,
  duration: 60,
  fees: 2,
};

describe('Trade log table components', () => {
  beforeEach(() => {
    useTradeDataMock.mockReset();
    exportCsvMock.mockReset();
  });

  it('TableHeader triggers callbacks', () => {
    const onExport = vi.fn();
    const onSearchChange = vi.fn();
    const onFilterChange = vi.fn();

    render(
      <TableHeader
        onExportCSV={onExport}
        hasData
        searchTerm=""
        onSearchChange={onSearchChange}
        filterProfitable={undefined}
        onFilterChange={onFilterChange}
        totalTrades={50}
        currentPage={2}
        pageSize={25}
        winningTrades={30}
        losingTrades={20}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /Export CSV/ }));
    fireEvent.change(screen.getByPlaceholderText('Search trades...'), { target: { value: 'aapl' } });
    fireEvent.click(screen.getByRole('button', { name: /Winners/ }));

    expect(onExport).toHaveBeenCalled();
    expect(onSearchChange).toHaveBeenCalledWith('aapl');
    expect(onFilterChange).toHaveBeenCalledWith(true);
  });

  it('SortableTableHeader sorts columns', () => {
    const onSort = vi.fn();
    render(
      <table>
        <SortableTableHeader columns={[]} sortBy="entry_time" sortOrder="desc" onSort={onSort} />
      </table>
    );

    fireEvent.click(screen.getByText('Entry Time'));
    expect(onSort).toHaveBeenCalledWith('entry_time');
  });

  it('TradeRow displays trade information', () => {
    render(
      <table>
        <tbody>
          <TradeRow trade={sampleTrade as any} index={0} />
        </tbody>
      </table>
    );

    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('BUY')).toBeInTheDocument();
  });

  it('Pagination controls page navigation', () => {
    const onPageChange = vi.fn();
    const onPageSizeChange = vi.fn();

    render(
      <Pagination
        currentPage={2}
        totalPages={5}
        pageSize={50}
        onPageChange={onPageChange}
        onPageSizeChange={onPageSizeChange}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /Previous/ }));
    fireEvent.click(screen.getByRole('button', { name: /Next/ }));
    fireEvent.change(screen.getByDisplayValue('50'), { target: { value: '25' } });

    expect(onPageChange).toHaveBeenCalledWith(1);
    expect(onPageChange).toHaveBeenCalledWith(3);
    expect(onPageSizeChange).toHaveBeenCalledWith(25);
  });

  it('renders TradeLogTable with data and export action', () => {
    useTradeDataMock.mockReturnValue({
      data: { trades: [sampleTrade], total_trades: 1, total_pages: 1 },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      page: 1,
      pageSize: 25,
      sortBy: 'entry_time',
      sortOrder: 'desc',
      filterProfitable: undefined,
      searchTerm: '',
      handleSort: vi.fn(),
      handleFilterChange: vi.fn(),
      handlePageChange: vi.fn(),
      handlePageSizeChange: vi.fn(),
      handleSearchChange: vi.fn(),
    });

    render(<TradeLogTable backtestId="bt-1" />);

    fireEvent.click(screen.getByRole('button', { name: /Export CSV/ }));
    expect(exportCsvMock).toHaveBeenCalledWith([sampleTrade], 'bt-1');
    expect(screen.getByText('AAPL')).toBeInTheDocument();
  });

  it('renders loading state', () => {
    useTradeDataMock.mockReturnValue({
      data: { trades: [] },
      isLoading: true,
      error: null,
      refetch: vi.fn(),
      page: 1,
      pageSize: 25,
      sortBy: 'entry_time',
      sortOrder: 'desc',
      filterProfitable: undefined,
      searchTerm: '',
      handleSort: vi.fn(),
      handleFilterChange: vi.fn(),
      handlePageChange: vi.fn(),
      handlePageSizeChange: vi.fn(),
      handleSearchChange: vi.fn(),
    });

    render(<TradeLogTable backtestId="bt-loading" />);
    expect(screen.getByText(/Loading trades/)).toBeInTheDocument();
  });

  it('renders empty state', () => {
    useTradeDataMock.mockReturnValue({
      data: { trades: [] },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      page: 1,
      pageSize: 25,
      sortBy: 'entry_time',
      sortOrder: 'desc',
      filterProfitable: undefined,
      searchTerm: '',
      handleSort: vi.fn(),
      handleFilterChange: vi.fn(),
      handlePageChange: vi.fn(),
      handlePageSizeChange: vi.fn(),
      handleSearchChange: vi.fn(),
    });

    render(<TradeLogTable backtestId="bt-empty" />);
    expect(screen.getByText(/No trades found/)).toBeInTheDocument();
  });

  it('renders error state and retries', () => {
    const refetch = vi.fn();
    useTradeDataMock.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('boom'),
      refetch,
      page: 1,
      pageSize: 25,
      sortBy: 'entry_time',
      sortOrder: 'desc',
      filterProfitable: undefined,
      searchTerm: '',
      handleSort: vi.fn(),
      handleFilterChange: vi.fn(),
      handlePageChange: vi.fn(),
      handlePageSizeChange: vi.fn(),
      handleSearchChange: vi.fn(),
    });

    render(<TradeLogTable backtestId="bt-error" />);
    fireEvent.click(screen.getByRole('button', { name: /Try Again/ }));
    expect(refetch).toHaveBeenCalled();
  });
});
