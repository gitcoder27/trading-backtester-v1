import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, LoadingSkeleton } from '../../../components/ui';
import { BacktestService } from '../../../services/backtest';

interface PerformanceRowProps {
  backtestId: string | null;
}

const Tile: React.FC<{ label: string; value: string; accent?: 'pos' | 'neg' | 'muted' }> = ({ label, value, accent = 'muted' }) => {
  const color = accent === 'pos' ? 'text-emerald-600 dark:text-emerald-400' : accent === 'neg' ? 'text-rose-600 dark:text-rose-400' : 'text-gray-900 dark:text-gray-100';
  const bg = accent === 'pos' ? 'bg-emerald-50 dark:bg-emerald-900/30' : accent === 'neg' ? 'bg-rose-50 dark:bg-rose-900/30' : 'bg-gray-50 dark:bg-gray-800/60';
  return (
    <div className={`rounded-lg ${bg} border border-gray-200 dark:border-gray-700 px-4 py-3`}> 
      <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">{label}</p>
      <p className={`mt-1 text-xl font-semibold ${color}`}>{value}</p>
    </div>
  );
};

const PerformanceRow: React.FC<PerformanceRowProps> = ({ backtestId }) => {
  if (!backtestId) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Performance Snapshot</h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">No completed backtests yet. Run your first one to see live metrics here.</p>
      </Card>
    );
  }

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard-performance-row', backtestId],
    queryFn: () => BacktestService.getBacktest(backtestId, { minimal: true }),
    staleTime: 5 * 60 * 1000,
  });

  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {[...Array(6)].map((_, i) => (
            <LoadingSkeleton key={i} className="h-16" />
          ))}
        </div>
      </Card>
    );
  }

  if (error || !data) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Performance Snapshot</h3>
        <p className="text-sm text-rose-600 dark:text-rose-400 mt-1">Failed to load performance data.</p>
      </Card>
    );
  }

  const obj = (data as any) || {};
  const m = obj.metrics || (obj.results?.metrics || {});
  const pct = (n: number | undefined) => (typeof n === 'number' ? `${n.toFixed(2)}%` : '—');
  const num = (n: number | undefined) => (typeof n === 'number' && Number.isFinite(n) ? n.toFixed(2) : '—');
  const totalReturn = (m.total_return_pct ?? (typeof m.total_return === 'number' ? (Math.abs(m.total_return) <= 1 ? m.total_return * 100 : m.total_return) : undefined)) as number | undefined;
  const maxDD = (m.max_drawdown_pct ?? (typeof m.max_drawdown === 'number' ? (Math.abs(m.max_drawdown) <= 1 ? m.max_drawdown * 100 : m.max_drawdown) : undefined)) as number | undefined;

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Performance Snapshot</h3>
        <p className="text-xs text-gray-500 dark:text-gray-400">Backtest ID {backtestId}</p>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {/* Total Return */}
        <Tile label="Total Return" value={pct(totalReturn)} accent={typeof totalReturn === 'number' ? (totalReturn >= 0 ? 'pos' : 'neg') : 'muted'} />
        {/* Sharpe Ratio: green >=1, red <0 */}
        <Tile label="Sharpe Ratio" value={num(m.sharpe_ratio)} accent={typeof m.sharpe_ratio === 'number' ? (m.sharpe_ratio >= 1 ? 'pos' : (m.sharpe_ratio < 0 ? 'neg' : 'muted')) : 'muted'} />
        {/* Max Drawdown: always alert color when present, display as negative */}
        <Tile label="Max Drawdown" value={typeof maxDD === 'number' ? `-${Math.abs(maxDD).toFixed(2)}%` : '—'} accent={typeof maxDD === 'number' ? 'neg' : 'muted'} />
        {/* Win Rate: green >=50, red <40 */}
        <Tile label="Win Rate" value={pct(m.win_rate)} accent={typeof m.win_rate === 'number' ? (m.win_rate >= 50 ? 'pos' : (m.win_rate < 40 ? 'neg' : 'muted')) : 'muted'} />
        {/* Profit Factor: green >=1.2, red <1.0 */}
        <Tile label="Profit Factor" value={num(m.profit_factor)} accent={typeof m.profit_factor === 'number' ? (m.profit_factor >= 1.2 ? 'pos' : (m.profit_factor < 1.0 ? 'neg' : 'muted')) : 'muted'} />
        <Tile label="Total Trades" value={String(m.total_trades ?? '—')} />
      </div>
    </Card>
  );
};

export default PerformanceRow;
