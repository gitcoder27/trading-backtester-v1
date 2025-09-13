import { useMemo } from 'react';
import { useJobStats } from './useJobStats';
import type { BacktestDisplay } from '../types/backtest';

export interface BacktestStats {
  totalBacktests: number;
  completedBacktests: number;
  runningJobs: number;
  avgReturn: number;
}

export function useBacktestStats(backtests: BacktestDisplay[]) {
  const baseStats = useMemo<BacktestStats>(() => {
    const completed = backtests.filter(bt => bt.status === 'completed');
    const avgReturn = completed.length > 0
      ? completed.reduce((acc, bt) => {
          const value = parseFloat(bt.totalReturn.replace('%', '').replace('+', ''));
          return acc + (Number.isNaN(value) ? 0 : value);
        }, 0) / completed.length
      : 0;

    return {
      totalBacktests: backtests.length,
      completedBacktests: completed.length,
      runningJobs: 0,
      avgReturn,
    };
  }, [backtests]);

  const { data } = useJobStats();
  const runningJobs = (data as any)?.stats?.running ?? backtests.filter(bt => bt.status === 'running').length;

  return { ...baseStats, runningJobs };
}
