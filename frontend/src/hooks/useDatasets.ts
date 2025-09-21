import { useQuery } from '@tanstack/react-query';
import { DatasetService } from '../services/dataset';
import type { Dataset, PaginatedResponse } from '../types';

// Normalizes API responses to a consistent array and backfills rows_count from record_count
function normalizeDatasets(res: PaginatedResponse<Dataset> | any): any[] {
  const items: any[] = (res as any)?.datasets || (res as any)?.items || (res as any)?.data || [];
  return items.map((d: any) => ({
    ...d,
    rows_count: d.rows_count ?? d.record_count,
  }));
}

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
