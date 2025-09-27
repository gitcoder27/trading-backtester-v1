import React, { useEffect, useMemo, useState } from 'react';
import type { ChartTrade, TradeListMeta } from '../../types/chart';
import TradeListHeader from './TradeListHeader';
import TradeListPagination from './TradeListPagination';
import type { SortField, SortOrder } from './TradeList.types';

interface TradeListProps {
  trades: ChartTrade[];
  meta?: TradeListMeta | null;
  isLoading?: boolean;
}

const PAGE_SIZE_OPTIONS = [10, 25, 50, 100];

const formatNumber = (value: unknown, options?: Intl.NumberFormatOptions) => {
  if (value === null || value === undefined) return '—';
  const num = Number(value);
  if (!Number.isFinite(num)) return '—';
  return num.toLocaleString('en-IN', {
    maximumFractionDigits: 2,
    minimumFractionDigits: Math.abs(num) < 1 ? 4 : 2,
    ...options,
  });
};

const formatDate = (value: unknown) => {
  if (!value) return '—';
  try {
    return new Date(String(value)).toLocaleString();
  } catch (error) {
    return String(value);
  }
};

const toNumber = (value: unknown): number | null => {
  if (value === null || value === undefined) return null;
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : null;
  }
  if (typeof value === 'string') {
    const normalized = value.replace(/,/g, '').trim();
    if (!normalized) return null;
    const parsed = Number(normalized);
    return Number.isFinite(parsed) ? parsed : null;
  }
  if (typeof value === 'boolean') {
    return value ? 1 : 0;
  }
  return null;
};

const resolveEntryTime = (trade: ChartTrade) =>
  trade.entry_time ?? trade.entry_timestamp ?? trade.entry_at ?? trade.timestamp ?? null;

const resolveExitTime = (trade: ChartTrade) =>
  trade.exit_time ?? trade.exit_timestamp ?? trade.exit_at ?? trade.close_time ?? null;

const resolveSide = (trade: ChartTrade) => {
  const side = trade.side ?? trade.direction ?? trade.position ?? trade.trade_type;
  if (!side) return '—';
  return String(side).toUpperCase();
};

const getQuantityValue = (trade: ChartTrade): number | null => {
  const qty = trade.quantity ?? trade.qty ?? trade.size ?? trade.contracts;
  return toNumber(qty);
};

const resolveQuantity = (trade: ChartTrade) => {
  const raw = getQuantityValue(trade);
  if (raw === null) return '—';
  return formatNumber(raw, { maximumFractionDigits: 0, minimumFractionDigits: 0 });
};

const getPriceValue = (trade: ChartTrade, candidates: (keyof ChartTrade)[]): number | null => {
  for (const key of candidates) {
    const value = toNumber(trade[key]);
    if (value !== null) {
      return value;
    }
  }
  return null;
};

const resolvePrice = (trade: ChartTrade, candidates: (keyof ChartTrade)[]) =>
  getPriceValue(trade, candidates);

const getPnlValue = (trade: ChartTrade): number | null =>
  toNumber(trade.pnl ?? trade.profit_loss ?? trade.profit ?? trade.net);

const resolvePnl = (trade: ChartTrade) => {
  const raw = getPnlValue(trade);
  if (raw === null) {
    return { value: '—', positive: false, negative: false };
  }
  return {
    value: formatNumber(raw, { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
    positive: raw > 0,
    negative: raw < 0,
  };
};

const getTimeValue = (value: unknown): number | null => {
  if (!value) return null;
  const parsed = Date.parse(String(value));
  return Number.isNaN(parsed) ? null : parsed;
};

const TradeList: React.FC<TradeListProps> = ({ trades, meta, isLoading = false }) => {
  const [sortField, setSortField] = useState<SortField>('entry_time');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [pageSize, setPageSize] = useState<number>(PAGE_SIZE_OPTIONS[0]);
  const [page, setPage] = useState<number>(1);

  useEffect(() => {
    setSortField('entry_time');
    setSortOrder('desc');
    setPage(1);
  }, [trades]);

  useEffect(() => {
    setPage(1);
  }, [pageSize]);

  const sortedTrades = useMemo(() => {
    if (!trades.length) return trades;

    const getComparableValue = (trade: ChartTrade, field: SortField) => {
      switch (field) {
        case 'entry_time':
          return getTimeValue(resolveEntryTime(trade));
        case 'exit_time':
          return getTimeValue(resolveExitTime(trade));
        case 'side':
          return resolveSide(trade);
        case 'quantity':
          return getQuantityValue(trade);
        case 'entry_price':
          return getPriceValue(trade, ['entry_price', 'price_in', 'buy_price']);
        case 'exit_price':
          return getPriceValue(trade, ['exit_price', 'price_out', 'sell_price']);
        case 'pnl':
        default:
          return getPnlValue(trade);
      }
    };

    return [...trades].sort((a, b) => {
      const aVal = getComparableValue(a, sortField);
      const bVal = getComparableValue(b, sortField);

      if (typeof aVal === 'string' || typeof bVal === 'string') {
        const comparison = String(aVal ?? '').localeCompare(String(bVal ?? ''));
        return sortOrder === 'asc' ? comparison : -comparison;
      }

      const aNum = typeof aVal === 'number' ? aVal : null;
      const bNum = typeof bVal === 'number' ? bVal : null;

      if (aNum === null && bNum === null) return 0;
      if (aNum === null) return sortOrder === 'asc' ? 1 : -1;
      if (bNum === null) return sortOrder === 'asc' ? -1 : 1;

      if (aNum === bNum) return 0;
      const comparison = aNum < bNum ? -1 : 1;
      return sortOrder === 'asc' ? comparison : -comparison;
    });
  }, [trades, sortField, sortOrder]);

  const totalTrades = sortedTrades.length;
  const totalPages = Math.max(1, Math.ceil(totalTrades / pageSize));
  const currentPage = Math.min(page, totalPages);
  const startIndex = totalTrades === 0 ? 0 : (currentPage - 1) * pageSize;
  const endIndexExclusive = Math.min(startIndex + pageSize, totalTrades);
  const visibleTrades = sortedTrades.slice(startIndex, endIndexExclusive);
  const displayFrom = totalTrades === 0 ? 0 : startIndex + 1;
  const displayTo = totalTrades === 0 ? 0 : endIndexExclusive;

  const handleSort = (field: SortField) => {
    if (field === sortField) {
      setSortOrder((prevOrder) => (prevOrder === 'asc' ? 'desc' : 'asc'));
      return;
    }
    setSortField(field);
    setSortOrder(field === 'side' ? 'asc' : 'desc');
  };

  const handlePageChange = (nextPage: number) => {
    setPage(Math.min(Math.max(nextPage, 1), totalPages));
  };

  const handlePageSizeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const nextSize = Number(event.target.value);
    setPageSize(nextSize);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-48">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
          <p className="mt-2 text-gray-500 dark:text-gray-400 text-sm">Loading trades…</p>
        </div>
      </div>
    );
  }

  if (!trades.length) {
    return (
      <div className="flex items-center justify-center h-40">
        <p className="text-gray-500 dark:text-gray-400 text-sm">No trades available for this backtest.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-gray-500 dark:text-gray-400">
        <span>
          Showing {displayFrom}-{displayTo} of {meta?.total ?? totalTrades} trades
        </span>
        <div className="flex items-center gap-2">
          {meta?.has_more && (
            <span className="text-[11px] text-gray-400">Limited to latest {meta.limit} entries</span>
          )}
          <label className="flex items-center gap-2">
            <span>Rows per page</span>
            <select
              value={pageSize}
              onChange={handlePageSizeChange}
              className="rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-2 py-1 text-gray-700 dark:text-gray-200"
            >
              {PAGE_SIZE_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      <div className="overflow-x-auto border border-gray-200 dark:border-gray-700 rounded-lg">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700 text-sm">
          <TradeListHeader sortField={sortField} sortOrder={sortOrder} onSort={handleSort} />
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700 bg-white dark:bg-gray-900">
            {visibleTrades.map((trade, index) => {
              const entryTime = resolveEntryTime(trade);
              const exitTime = resolveExitTime(trade);
              const side = resolveSide(trade);
              const quantity = resolveQuantity(trade);
              const entryPrice = resolvePrice(trade, ['entry_price', 'price_in', 'buy_price']);
              const exitPrice = resolvePrice(trade, ['exit_price', 'price_out', 'sell_price']);
              const pnl = resolvePnl(trade);
              const entryRef = entryTime;

              return (
                <tr
                  key={String(trade.id ?? entryRef ?? index + startIndex)}
                  className="hover:bg-gray-50 dark:hover:bg-gray-800/60"
                >
                  <td className="px-4 py-2 whitespace-nowrap text-gray-700 dark:text-gray-200">{formatDate(entryTime)}</td>
                  <td className="px-4 py-2 whitespace-nowrap text-gray-700 dark:text-gray-200">{formatDate(exitTime)}</td>
                  <td className="px-4 py-2 uppercase tracking-wide text-gray-700 dark:text-gray-200">{side}</td>
                  <td className="px-4 py-2 text-right text-gray-700 dark:text-gray-200">{quantity}</td>
                  <td className="px-4 py-2 text-right text-gray-700 dark:text-gray-200">{formatNumber(entryPrice)}</td>
                  <td className="px-4 py-2 text-right text-gray-700 dark:text-gray-200">{formatNumber(exitPrice)}</td>
                  <td
                    className={`px-4 py-2 text-right font-semibold ${
                      pnl.positive ? 'text-emerald-500' : pnl.negative ? 'text-rose-500' : 'text-gray-700 dark:text-gray-200'
                    }`}
                  >
                    {pnl.value}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <TradeListPagination page={currentPage} totalPages={totalPages} onPageChange={handlePageChange} />
    </div>
  );
};

export default TradeList;
