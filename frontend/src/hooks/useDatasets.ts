import { useEffect, useState, useCallback } from 'react';
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
  const [datasets, setDatasets] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchDatasets = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await DatasetService.listDatasets({ page: 1, size: 100 });
      setDatasets(normalizeDatasets(res));
    } catch (e: any) {
      setError(e instanceof Error ? e : new Error('Failed to load datasets'));
      setDatasets([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDatasets();
  }, [fetchDatasets]);

  return { datasets, loading, error, refetch: fetchDatasets };
}

