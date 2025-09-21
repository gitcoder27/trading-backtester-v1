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

/**
 * Normalize a PaginatedResponse<Job> into the internal JobsQueryResult shape.
 *
 * Converts the possibly-partial paginated response into a stable object with
 * concrete values for jobs, total, limit, pages, and page. If fields are
 * missing the function applies safe defaults:
 * - `items` -> `jobs`: defaults to an empty array.
 * - `limit`: uses response.limit if present, otherwise jobs.length or 1.
 * - `total`: uses response.total if present, otherwise jobs.length.
 * - `pages`: uses response.pages if present, otherwise max(1, ceil(total / max(1, limit))).
 * - `page`: uses response.page if present, otherwise 1.
 *
 * @param response - The paginated API response to normalize. Missing or undefined
 *                   pagination fields will be replaced with the defaults described above.
 * @returns A JobsQueryResult object with guaranteed numeric pagination fields and an array of jobs.
 */
function normalizeJobsResponse(response: PaginatedResponse<Job>): JobsQueryResult {
  const jobs = Array.isArray(response?.items) ? response.items : [];
  const limit = response?.limit ?? (jobs.length || 1);
  const total = response?.total ?? jobs.length;
  const pages = response?.pages ?? Math.max(1, Math.ceil(total / Math.max(1, limit)));
  const page = response?.page ?? 1;

  return { jobs, total, limit, pages, page };
}

/**
 * React Query hook that fetches a paginated list of jobs and returns a normalized result.
 *
 * The provided `limit` is clamped to the range [1, 100] and used as the page size for the request.
 * The raw API response is transformed into a `JobsQueryResult` (fields: `jobs`, `total`, `limit`, `pages`, `page`).
 *
 * @param limit - Desired number of items per page (will be clamped to 1–100)
 * @returns A `UseQueryResult` whose `data` is a `JobsQueryResult` or an `Error` on failure
 */
export function useJobsQuery(limit: number): UseQueryResult<JobsQueryResult, Error> {
  const queryLimit = Math.max(1, Math.min(100, limit));

  return useQuery<PaginatedResponse<Job>, Error, JobsQueryResult>({
    queryKey: ['jobs', { limit: queryLimit }],
    queryFn: () => JobService.listJobs({ limit: queryLimit }),
    refetchOnMount: false,
    select: normalizeJobsResponse,
  });
}
