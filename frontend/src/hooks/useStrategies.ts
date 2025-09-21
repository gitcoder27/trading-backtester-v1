import { useQuery } from '@tanstack/react-query';
import { StrategyService } from '../services/strategyService';
import type { Strategy } from '../types';

export function useStrategies(options: { activeOnly?: boolean } = {}) {
  const { activeOnly = true } = options;
  const {
    data,
    isLoading,
    isFetching,
    error,
    refetch,
  } = useQuery<Strategy[]>({
    queryKey: ['strategies', { activeOnly }],
    queryFn: async () => {
      const list = await StrategyService.getStrategies();
      return activeOnly ? list.filter(s => s.is_active) : list;
    },
    refetchOnMount: false,
  });

  const strategies = data ?? [];
  const loading = isLoading || isFetching;
  const normalizedError = error instanceof Error ? error : null;

  return { strategies, loading, error: normalizedError, refetch };
}
