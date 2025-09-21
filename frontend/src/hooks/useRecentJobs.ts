import { useMemo } from 'react';
import type { Job } from '../types';
import { useJobsQuery } from './useJobsQuery';

/**
 * Hook that returns the most recent jobs along with query state and controls.
 *
 * The hook fetches up to `fetchLimit` jobs (or `limit` when `fetchLimit` is omitted)
 * and exposes the first `limit` items as `recentJobs`.
 *
 * @param limit - Maximum number of jobs to return in `recentJobs`. Defaults to `5`.
 * @param fetchLimit - Optional number of jobs to request from the backend; when omitted the hook requests `limit` items.
 * @returns An object with:
 *  - `recentJobs`: an array of up to `limit` Job items (empty until data is available),
 *  - `loading`: `true` while the underlying query is loading or fetching,
 *  - `error`: the query error or `null` if none,
 *  - `refetch`: function to trigger a refetch of the jobs.
 */
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
