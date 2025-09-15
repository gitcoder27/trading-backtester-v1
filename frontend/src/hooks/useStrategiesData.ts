import { useCallback, useEffect, useState } from 'react';
import { StrategyService } from '../services/strategyService';
import type { Strategy } from '../types';
import { showToast } from '../components/ui/Toast';

export interface StrategyStats {
  total_strategies: number;
  active_strategies: number;
  discovered_strategies: number;
  total_backtests: number;
  avg_performance: number;
}

export function useStrategiesData() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [stats, setStats] = useState<StrategyStats>({
    total_strategies: 0,
    active_strategies: 0,
    discovered_strategies: 0,
    total_backtests: 0,
    avg_performance: 0,
  });
  const [loading, setLoading] = useState<boolean>(true);

  const loadStrategies = useCallback(async () => {
    try {
      const strategiesData = await StrategyService.getStrategies();
      setStrategies(Array.isArray(strategiesData) ? strategiesData : []);
    } catch (error) {
      console.error('Failed to load strategies:', error);
      showToast.error('Failed to load strategies');
      setStrategies([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadStats = useCallback(async () => {
    try {
      const s = await StrategyService.getStrategyStats();
      setStats(s || {
        total_strategies: 0,
        active_strategies: 0,
        discovered_strategies: 0,
        total_backtests: 0,
        avg_performance: 0,
      });
    } catch (error) {
      console.error('Failed to load strategy stats:', error);
    }
  }, []);

  const refetch = useCallback(async () => {
    setLoading(true);
    await Promise.all([loadStrategies(), loadStats()]);
  }, [loadStrategies, loadStats]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { strategies, stats, loading, refetch, setStrategies } as const;
}

