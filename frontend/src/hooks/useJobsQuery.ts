import { useQuery } from '@tanstack/react-query';
import type { UseQueryResult } from '@tanstack/react-query';
import { JobService } from '../services/backtest';
import type { Job, PaginatedResponse } from '../types';

export interface JobsQueryResult {
  jobs: Job[];
  total: number;
  limit: number;
  pages: number;
  page: number;
}

function normalizeJobsResponse(response: PaginatedResponse<Job>): JobsQueryResult {
  const jobs = Array.isArray(response?.items) ? response.items : [];
  const limit = response?.limit ?? (jobs.length || 1);
  const total = response?.total ?? jobs.length;
  const pages = response?.pages ?? Math.max(1, Math.ceil(total / Math.max(1, limit)));
  const page = response?.page ?? 1;

  return { jobs, total, limit, pages, page };
}

export function useJobsQuery(limit: number): UseQueryResult<JobsQueryResult, Error> {
  const queryLimit = Math.max(1, Math.min(100, limit));

  return useQuery<PaginatedResponse<Job>, Error, JobsQueryResult>({
    queryKey: ['jobs', { limit: queryLimit }],
    queryFn: () => JobService.listJobs({ limit: queryLimit }),
    refetchOnMount: false,
    select: normalizeJobsResponse,
  });
}
