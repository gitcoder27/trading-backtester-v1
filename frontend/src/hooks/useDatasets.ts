import { useQuery } from '@tanstack/react-query';
import { DatasetService } from '../services/dataset';
import type { Dataset, PaginatedResponse } from '../types';

/**
 * Normalize various API response shapes into a flat array of dataset objects with a guaranteed `rows_count`.
 *
 * Accepts paginated or non-paginated responses and extracts items from `datasets`, `items`, or `data`. For each item,
 * ensures a `rows_count` property exists by using the existing `rows_count` if present or falling back to `record_count`.
 *
 * @param res - API response (can be a PaginatedResponse<Dataset> or any object containing `datasets`, `items`, or `data`)
 * @returns An array of dataset objects with `rows_count` populated where possible
 */
function normalizeDatasets(res: PaginatedResponse<Dataset> | any): any[] {
  const items: any[] = (res as any)?.datasets || (res as any)?.items || (res as any)?.data || [];
  return items.map((d: any) => ({
    ...d,
    rows_count: d.rows_count ?? d.record_count,
  }));
}

/**
 * React hook that fetches and returns a normalized page of datasets (page 1, size 100) via react-query.
 *
 * The hook normalizes the API response with `normalizeDatasets`, exposes an empty array when no data
 * is available, treats the query as loading while either `isLoading` or `isFetching` is true, and
 * converts the query error to an `Error` instance or `null`.
 *
 * @returns An object containing:
 *  - `datasets`: The normalized dataset items (array, defaults to []).
 *  - `loading`: `true` when the query is loading or fetching.
 *  - `error`: The `Error` instance when the query failed, otherwise `null`.
 *  - `refetch`: Function to manually refetch the datasets query.
 */
export function useDatasets() {
  const {
    data,
    isLoading,
    isFetching,
    error,
    refetch,
  } = useQuery<any[]>({
    queryKey: ['datasets', { page: 1, size: 100 }],
    queryFn: async () => {
      const res = await DatasetService.listDatasets({ page: 1, size: 100 });
      return normalizeDatasets(res);
    },
    refetchOnMount: false,
  });

  const datasets = data ?? [];
  const loading = isLoading || isFetching;
  const normalizedError = error instanceof Error ? error : null;

  return { datasets, loading, error: normalizedError, refetch };
}
