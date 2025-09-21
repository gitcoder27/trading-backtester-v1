import { useMemo } from 'react';
import type { Job } from '../types';
import { useJobsQuery } from './useJobsQuery';

export function useRecentJobs(limit: number = 5, fetchLimit?: number) {
  const queryLimit = fetchLimit ?? limit;
  const query = useJobsQuery(queryLimit);

  const recentJobs = useMemo<Job[]>(() => {
    if (!query.data) return [];
    return query.data.jobs.slice(0, limit);
  }, [query.data, limit]);

  return {
    recentJobs,
    loading: query.isLoading || query.isFetching,
    error: query.error ?? null,
    refetch: query.refetch,
  } as const;
}
