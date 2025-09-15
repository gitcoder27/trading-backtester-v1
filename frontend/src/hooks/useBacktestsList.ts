import { useEffect, useState, useCallback } from 'react';
import { BacktestService } from '../services/backtest';
import { formatDuration, formatTradingSessionsDuration } from '../utils/formatters';
import type { BacktestDisplay } from '../types/backtest';

const FALLBACK_DATASET_LABEL = 'NIFTY Aug 2025 (1min)';

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

export function useBacktestsList() {
  const [backtests, setBacktests] = useState<BacktestDisplay[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  const mapToDisplay = (bt: any): BacktestDisplay => {
    const metrics = bt.results?.metrics || bt.metrics || {};
    const strategyName = bt.strategy_name || bt.strategy_id || 'Unknown Strategy';
    const cleanStrategyName = strategyName.includes('.')
      ? strategyName.split('.').pop() || strategyName
      : strategyName;

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

    // Compute trading sessions based duration
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

    return {
      id: bt.id,
      jobId: (bt.job_id ?? bt.backtest_job_id)?.toString(),
      strategy: cleanStrategyName,
      dataset: bt.dataset_name && bt.dataset_name !== 'Unknown Dataset' ? bt.dataset_name : FALLBACK_DATASET_LABEL,
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
      createdAt: new Date(bt.created_at).toLocaleDateString(),
      createdAtTs: new Date(bt.created_at).getTime(),
      duration: durationDisplay,
    };
  };

  const fetchBacktests = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const pageSize = 100;
      const first = await BacktestService.listBacktests({ page: 1, size: pageSize });
      let items: any[] = [];
      let total = 0;
      if ((first as any).results) {
        items = (first as any).results;
        total = (first as any).total || items.length;
      } else if ((first as any).data) {
        items = (first as any).data;
        total = (first as any).total || items.length;
      } else if ((first as any).items) {
        items = (first as any).items;
        total = (first as any).total || items.length;
      }
      const pages = Math.max(1, Math.ceil(total / pageSize));
      const rest: any[] = [];
      for (let p = 2; p <= pages; p++) {
        try {
          const res = await BacktestService.listBacktests({ page: p, size: pageSize });
          if ((res as any).results) rest.push(...(res as any).results);
          else if ((res as any).data) rest.push(...(res as any).data);
          else if ((res as any).items) rest.push(...(res as any).items);
        } catch (e) {
          // Stop pagination on first error
          break;
        }
      }
      const all = [...items, ...rest];
      const displays = all.map(mapToDisplay);
      const sorted = displays.sort((a, b) => {
        const aNum = extractJobIdNumber(a.jobId);
        const bNum = extractJobIdNumber(b.jobId);
        if (aNum !== bNum) return bNum - aNum;
        return b.createdAtTs - a.createdAtTs;
      });
      setBacktests(sorted);
    } catch (e: any) {
      setError(e instanceof Error ? e : new Error('Failed to load backtests'));
      setBacktests([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBacktests();
  }, [fetchBacktests]);

  const removeBacktestLocally = (id: string) => {
    setBacktests(prev => prev.filter(b => b.id !== id));
  };

  return { backtests, loading, error, refetch: fetchBacktests, setBacktests, removeBacktestLocally };
}
