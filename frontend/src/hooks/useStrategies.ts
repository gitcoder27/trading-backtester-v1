import { useEffect, useState, useCallback } from 'react';
import { StrategyService } from '../services/strategyService';
import type { Strategy } from '../types';

export function useStrategies(options: { activeOnly?: boolean } = {}) {
  const { activeOnly = true } = options;
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchStrategies = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await StrategyService.getStrategies();
      setStrategies(activeOnly ? list.filter(s => s.is_active) : list);
    } catch (e: any) {
      setError(e instanceof Error ? e : new Error('Failed to load strategies'));
      setStrategies([]);
    } finally {
      setLoading(false);
    }
  }, [activeOnly]);

  useEffect(() => {
    fetchStrategies();
  }, [fetchStrategies]);

  return { strategies, loading, error, refetch: fetchStrategies };
}

