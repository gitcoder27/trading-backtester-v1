import { useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { BacktestService } from '../services/backtest';
import { formatTradingSessionsDuration } from '../utils/formatters';
import type { BacktestDisplay } from '../types/backtest';

const FALLBACK_DATASET_LABEL = 'NIFTY Aug 2025 (1min)';
const PAGE_SIZE = 100;
const QUERY_KEY = ['backtests', { pageSize: PAGE_SIZE, compact: true }];

function extractJobIdNumber(jobId?: string): number {
  if (!jobId) return -Infinity;
  const asNum = Number(jobId);
  if (!Number.isNaN(asNum)) return asNum;
  const match = jobId.match(/(\d+)/g);
  if (match && match.length > 0) {
    const last = match[match.length - 1];
    const n = Number(last);
    if (!Number.isNaN(n)) return n;
  }
  return -Infinity;
}

const selectItems = (res: any): any[] => {
  if (!res) return [];
  if (Array.isArray((res as any).results)) return (res as any).results;
  if (Array.isArray((res as any).data)) return (res as any).data;
  if (Array.isArray((res as any).items)) return (res as any).items;
  return Array.isArray(res) ? res : [];
};

const mapToDisplay = (bt: any): BacktestDisplay => {
  const metrics = bt.results?.metrics || bt.metrics || {};
  const strategyName = bt.strategy_name || bt.strategy_id || 'Unknown Strategy';
  const cleanStrategyName = strategyName.includes('.')
    ? strategyName.split('.').pop() || strategyName
    : strategyName;

  const parseNumeric = (value: unknown): number | null => {
    if (value === null || value === undefined) return null;
    if (typeof value === 'number' && Number.isFinite(value)) return value;
    if (typeof value === 'string') {
      const parsed = Number(value);
      return Number.isFinite(parsed) ? parsed : null;
    }
    return null;
  };

  const resolveLots = (): number | null => {
    const candidates = [
      bt.engine_config?.lots,
      bt.results?.engine_config?.lots,
      bt.execution_info?.engine_config?.lots,
      bt.engine_options?.lots,
      bt.strategy_params?.position_size,
      bt.strategy_params?.lots,
      bt.position_size,
      bt.lots,
    ];

    for (const candidate of candidates) {
      const parsed = parseNumeric(candidate);
      if (parsed !== null) {
        return parsed;
      }
    }
    return null;
  };

  const deriveReturnPercent = (): string => {
    let pct: number | null = null;
    if (typeof metrics.total_return_percent === 'number') {
      pct = metrics.total_return_percent;
    } else if (typeof metrics.total_return === 'number') {
      pct = Math.abs(metrics.total_return) <= 1 ? metrics.total_return * 100 : metrics.total_return;
    }
    if (pct === null || Number.isNaN(pct)) return 'N/A';
    const sign = pct > 0 ? '+' : '';
    return `${sign}${pct.toFixed(2)}%`;
  };

  const tradingDays: number | undefined = (
    metrics.trading_sessions_days ??
    metrics.trading_days ??
    metrics.total_trading_days
  );
  const durationDisplay =
    typeof tradingDays === 'number' && tradingDays > 0
      ? formatTradingSessionsDuration(tradingDays)
      : bt.status === 'running'
      ? 'In Progress'
      : bt.status === 'pending'
      ? 'Pending'
      : '—';

  const datasetName = bt.dataset_name && bt.dataset_name !== 'Unknown Dataset'
    ? bt.dataset_name
    : FALLBACK_DATASET_LABEL;

  const createdAtDate = bt.created_at ? new Date(bt.created_at) : null;

  return {
    id: bt.id,
    jobId: (bt.job_id ?? bt.backtest_job_id)?.toString(),
    strategy: cleanStrategyName,
    dataset: datasetName,
    status: (bt.status === 'error' ? 'failed' : bt.status) || 'pending',
    totalReturn: deriveReturnPercent(),
    sharpeRatio: metrics.sharpe_ratio || 0,
    maxDrawdown: metrics.max_drawdown_percent
      ? `${metrics.max_drawdown_percent.toFixed(2)}%`
      : metrics.max_drawdown
      ? `${(metrics.max_drawdown * 100).toFixed(2)}%`
      : 'N/A',
    totalTrades: metrics.total_trades || 0,
    winRate: typeof metrics.win_rate === 'number' ? `${metrics.win_rate.toFixed(1)}%` : 'N/A',
    createdAt: createdAtDate ? createdAtDate.toLocaleDateString() : '—',
    createdAtTs: createdAtDate ? createdAtDate.getTime() : 0,
    duration: durationDisplay,
    lots: resolveLots(),
  };
};

export function useBacktestsList() {
  const queryClient = useQueryClient();

  const fetchBacktests = useCallback(async (): Promise<BacktestDisplay[]> => {
    const first = await BacktestService.listBacktests({ page: 1, size: PAGE_SIZE, compact: true });
    const firstItems = selectItems(first);
    const total = (first as any)?.total ?? firstItems.length;
    const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));

    let combined = [...firstItems];
    if (pages > 1) {
      const requests: Array<Promise<any>> = [];
      for (let p = 2; p <= pages; p++) {
        requests.push(BacktestService.listBacktests({ page: p, size: PAGE_SIZE, compact: true }));
      }

      if (requests.length > 0) {
        const settled = await Promise.allSettled(requests);
        settled.forEach((result, index) => {
          if (result.status === 'fulfilled') {
            combined = combined.concat(selectItems(result.value));
          } else if (typeof import.meta !== 'undefined' && import.meta.env?.DEV) {
            console.warn(`useBacktestsList: failed to fetch page ${index + 2}`, result.reason);
          }
        });
      }
    }

    const displays = combined.map(mapToDisplay);
    return displays.sort((a, b) => {
      const aNum = extractJobIdNumber(a.jobId);
      const bNum = extractJobIdNumber(b.jobId);
      if (aNum !== bNum) return bNum - aNum;
      return b.createdAtTs - a.createdAtTs;
    });
  }, []);

  const query = useQuery<BacktestDisplay[]>({
    queryKey: QUERY_KEY,
    queryFn: fetchBacktests,
    refetchOnMount: false,
  });

  const removeBacktestLocally = useCallback((id: string) => {
    queryClient.setQueryData<BacktestDisplay[]>(QUERY_KEY, (prev) => {
      if (!prev) return prev;
      return prev.filter((bt) => bt.id !== id);
    });
  }, [queryClient]);

  const backtests = query.data ?? [];
  const loading = query.isLoading || query.isFetching;
  const normalizedError = query.error instanceof Error ? query.error : null;

  return {
    backtests,
    loading,
    error: normalizedError,
    refetch: query.refetch,
    removeBacktestLocally,
  } as const;
}
