import { useEffect, useMemo, useState } from 'react';
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

  const [stats, setStats] = useState<BacktestStats>(baseStats);

  useEffect(() => {
    // Use client-side derived running jobs to avoid extra network calls
    const running = backtests.filter(bt => bt.status === 'running').length;
    setStats({ ...baseStats, runningJobs: running });
  }, [baseStats, backtests]);

  return stats;
}
