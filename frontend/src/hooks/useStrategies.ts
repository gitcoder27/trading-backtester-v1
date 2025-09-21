import { useQuery } from '@tanstack/react-query';
import { StrategyService } from '../services/strategyService';
import type { Strategy } from '../types';

/**
 * Hook to load strategies, optionally returning only active ones.
 *
 * Fetches strategies via the StrategyService and exposes loading state, a normalized error, and a `refetch` function.
 *
 * @param options - Optional settings.
 * @param options.activeOnly - If true (default), only strategies with `is_active` truthy are returned.
 * @returns An object with:
 *  - `strategies`: array of Strategy (empty array while unavailable),
 *  - `loading`: boolean true while the query is loading or fetching,
 *  - `error`: normalized Error or null,
 *  - `refetch`: function to manually re-run the query.
 */
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
