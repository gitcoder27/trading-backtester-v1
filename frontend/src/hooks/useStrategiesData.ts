import { useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
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

const EMPTY_STATS: StrategyStats = {
  total_strategies: 0,
  active_strategies: 0,
  discovered_strategies: 0,
  total_backtests: 0,
  avg_performance: 0,
};

export function useStrategiesData() {
  const {
    data: strategies,
    isLoading: strategiesLoading,
    isFetching: strategiesFetching,
    refetch: refetchStrategies,
  } = useQuery<Strategy[]>({
    queryKey: ['strategies', { scope: 'library' }],
    queryFn: async () => {
      const strategiesData = await StrategyService.getStrategies();
      if (!Array.isArray(strategiesData)) {
        return [];
      }
      return strategiesData;
    },
    refetchOnMount: false,
    onError: (error) => {
      console.error('Failed to load strategies:', error);
      showToast.error('Failed to load strategies');
    },
  });

  const {
    data: stats,
    isLoading: statsLoading,
    isFetching: statsFetching,
    refetch: refetchStats,
  } = useQuery<StrategyStats>({
    queryKey: ['strategies', 'stats'],
    queryFn: async () => {
      const summary = await StrategyService.getStrategyStats();
      return summary || EMPTY_STATS;
    },
    refetchOnMount: false,
    onError: (error) => {
      console.error('Failed to load strategy stats:', error);
    },
  });

  const loading = strategiesLoading || statsLoading || strategiesFetching || statsFetching;

  const refetch = useCallback(async () => {
    await Promise.all([refetchStrategies(), refetchStats()]);
  }, [refetchStrategies, refetchStats]);

  return {
    strategies: strategies ?? [],
    stats: stats ?? EMPTY_STATS,
    loading,
    refetch,
  } as const;
}
