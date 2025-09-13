import { useCallback, useEffect, useState } from 'react';
import { JobService } from '../services/backtest';
import type { Job } from '../types';

export function useRecentJobs(limit: number = 5) {
  const [recentJobs, setRecentJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchRecent = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await JobService.listJobs({ page: 1, size: limit });
      const jobs = (response as any).jobs || (response as any).items || [];
      setRecentJobs(jobs);
    } catch (e: any) {
      setError(e instanceof Error ? e : new Error('Failed to load recent jobs'));
      setRecentJobs([]);
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    fetchRecent();
  }, [fetchRecent]);

  return { recentJobs, loading, error, refetch: fetchRecent };
}

