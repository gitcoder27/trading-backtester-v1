import { useMemo, useCallback, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { showToast } from '../../../components/ui/Toast';
import { StrategyService } from '../../../services/strategyService';
import { BacktestService } from '../../../services/backtest';
import { DatasetService } from '../../../services/dataset';
import { useJobsQuery } from '../../../hooks/useJobsQuery';
import { useJobStats } from '../../../hooks/useJobStats';
import type { Strategy } from '../../../types';

export interface KpiStats {
  activeStrategies: number;
  totalStrategies: number;
  totalDatasets: number;
  totalBacktests: number;
  runningJobs: number;
}

export interface DatasetSummary {
  total_datasets: number;
  total_file_size: number;
  total_rows: number;
  average_quality_score: number;
  timeframes: Record<string, number>;
  exchanges: Record<string, number>;
  symbols: Record<string, number>;
}

const DASHBOARD_RECENT_BACKTEST_LIMIT = 5;
const DASHBOARD_BACKTEST_FETCH_SIZE = 10;
const DASHBOARD_JOBS_FETCH_LIMIT = 50;
const DASHBOARD_RECENT_JOBS_LIMIT = 5;

/**
 * Normalize various backtest response shapes into an array of items.
 *
 * Accepts a payload that may be an array or an object containing an array under
 * `results`, `items`, or `data`. Returns the first found array or an empty
 * array if none are present.
 *
 * @param payload - The response payload to normalize (array or object)
 * @returns An array of backtest items (possibly empty)
 */
function selectBacktestItems(payload: any): any[] {
  if (!payload) return [];
  if (Array.isArray(payload.results)) return payload.results;
  if (Array.isArray(payload.items)) return payload.items;
  if (Array.isArray(payload.data)) return payload.data;
  return Array.isArray(payload) ? payload : [];
}

/**
 * Normalize a raw dataset-summary payload into a DatasetSummary object or null.
 *
 * If `raw` has a `summary` property, that value is returned (cast to DatasetSummary).
 * If `raw` itself is an object and contains the summary fields, `raw` is returned.
 * Returns `null` for falsy inputs or when the resolved value is not an object.
 *
 * @param raw - Response or payload from the dataset summary endpoint (may be the summary object itself or an envelope with a `summary` field)
 * @returns The normalized DatasetSummary or `null` when unavailable or invalid
 */
function deriveDatasetSummary(raw: any): DatasetSummary | null {
  if (!raw) return null;
  const summary = raw.summary ?? raw;
  if (!summary || typeof summary !== 'object') return null;
  return summary as DatasetSummary;
}

export const useDashboardData = () => {
  const jobsQuery = useJobsQuery(DASHBOARD_JOBS_FETCH_LIMIT);
  const jobStatsQuery = useJobStats();
  const strategiesQuery = useQuery<Strategy[]>({
    queryKey: ['strategies', { scope: 'library' }],
    queryFn: () => StrategyService.getStrategies(),
    refetchOnMount: false,
  });
  const strategyStatsQuery = useQuery({
    queryKey: ['strategies', 'stats'],
    queryFn: () => StrategyService.getStrategyStats(),
    refetchOnMount: false,
  });
  const backtestsQuery = useQuery({
    queryKey: ['dashboard', 'backtests', { page: 1, size: DASHBOARD_BACKTEST_FETCH_SIZE }],
    queryFn: () => BacktestService.listBacktests({ page: 1, size: DASHBOARD_BACKTEST_FETCH_SIZE, compact: true } as any),
    refetchOnMount: false,
  });
  const datasetSummaryQuery = useQuery({
    queryKey: ['datasets', 'summary'],
    queryFn: () => DatasetService.getSummary(),
    refetchOnMount: false,
  });

  const queryErrorRef = useRef(false);
  const firstError =
    strategyStatsQuery.error ||
    strategiesQuery.error ||
    backtestsQuery.error ||
    datasetSummaryQuery.error ||
    jobsQuery.error ||
    jobStatsQuery.error;

  useEffect(() => {
    if (firstError && !queryErrorRef.current) {
      queryErrorRef.current = true;
      showToast.error('Failed to load dashboard data');
    } else if (!firstError) {
      queryErrorRef.current = false;
    }
  }, [firstError]);

  const strategies = useMemo<Strategy[]>(
    () => (Array.isArray(strategiesQuery.data) ? strategiesQuery.data : []),
    [strategiesQuery.data]
  );

  const backtestItems = useMemo(() => selectBacktestItems(backtestsQuery.data), [backtestsQuery.data]);
  const sortedBacktests = useMemo(() => {
    return [...backtestItems].sort((a, b) => {
      const aTs = a?.created_at ? new Date(a.created_at).getTime() : 0;
      const bTs = b?.created_at ? new Date(b.created_at).getTime() : 0;
      return bTs - aTs;
    });
  }, [backtestItems]);
  const recentBacktests = useMemo(
    () => sortedBacktests.slice(0, DASHBOARD_RECENT_BACKTEST_LIMIT),
    [sortedBacktests]
  );
  const latestCompletedBacktestId = useMemo(() => {
    const latestCompleted = sortedBacktests.find((bt) => bt.status === 'completed');
    return latestCompleted?.id ? String(latestCompleted.id) : null;
  }, [sortedBacktests]);
  const totalBacktests = useMemo(() => {
    const total = (backtestsQuery.data as any)?.total;
    if (typeof total === 'number' && !Number.isNaN(total)) {
      return total;
    }
    return sortedBacktests.length;
  }, [backtestsQuery.data, sortedBacktests.length]);

  const jobs = useMemo(() => jobsQuery.data?.jobs ?? [], [jobsQuery.data]);
  const recentJobs = useMemo(
    () => jobs.slice(0, DASHBOARD_RECENT_JOBS_LIMIT),
    [jobs]
  );

  const runningJobs = useMemo(() => {
    const runningFromStats = jobStatsQuery.data?.stats?.running;
    if (typeof runningFromStats === 'number') {
      return runningFromStats;
    }
    return jobs.filter((job) => job.status === 'running').length;
  }, [jobStatsQuery.data, jobs]);

  const datasetSummary = useMemo(
    () => deriveDatasetSummary(datasetSummaryQuery.data),
    [datasetSummaryQuery.data]
  );

  const topStrategies = useMemo(() => {
    const ranked = strategies
      .filter((s: any) => typeof s?.avg_performance === 'number')
      .sort((a: any, b: any) => (b.avg_performance ?? 0) - (a.avg_performance ?? 0))
      .slice(0, 3);

    if (ranked.length > 0) {
      return ranked;
    }

    if (sortedBacktests.length === 0) {
      return ranked;
    }

    const aggregates: Record<string, { name: string; returns: number[]; count: number }> = {};
    for (const bt of sortedBacktests) {
      if (bt.status !== 'completed') continue;
      const metrics = bt.results?.metrics || bt.metrics || bt.results || {};
      const raw = metrics.total_return_percent ?? metrics.total_return_pct;
      let pct: number | null = null;
      if (typeof raw === 'number') pct = raw;
      else if (typeof metrics.total_return === 'number') {
        pct = Math.abs(metrics.total_return) <= 1 ? metrics.total_return * 100 : metrics.total_return;
      }
      if (pct === null || Number.isNaN(pct)) continue;

      const name = String(bt.strategy_name || bt.strategy_id || 'Unknown');
      if (!aggregates[name]) {
        aggregates[name] = { name, returns: [], count: 0 };
      }
      aggregates[name].returns.push(pct);
      aggregates[name].count += 1;
    }

    return Object.values(aggregates)
      .map((entry) => ({
        id: entry.name,
        name: entry.name,
        avg_performance: entry.returns.reduce((acc, value) => acc + value, 0) / Math.max(1, entry.returns.length),
        total_backtests: entry.count,
      }))
      .sort((a, b) => (b.avg_performance ?? 0) - (a.avg_performance ?? 0))
      .slice(0, 3) as Strategy[];
  }, [strategies, sortedBacktests]);

  const mostTestedStrategies = useMemo(() => {
    const ranked = [...strategies]
      .sort((a: any, b: any) => (b.total_backtests ?? 0) - (a.total_backtests ?? 0))
      .slice(0, 3);

    if (ranked.length > 0) {
      return ranked;
    }

    if (sortedBacktests.length === 0) {
      return ranked;
    }

    const counts: Record<string, number> = {};
    for (const bt of sortedBacktests) {
      const name = String(bt.strategy_name || bt.strategy_id || 'Unknown');
      counts[name] = (counts[name] || 0) + 1;
    }

    return Object.entries(counts)
      .map(([name, count]) => ({ id: name, name, total_backtests: count } as Strategy))
      .sort((a, b) => (b.total_backtests ?? 0) - (a.total_backtests ?? 0))
      .slice(0, 3);
  }, [strategies, sortedBacktests]);

  const kpis = useMemo<KpiStats>(() => {
    const strategySummary = (strategyStatsQuery.data as any)?.summary ?? strategyStatsQuery.data ?? {};
    const activeStrategies = Number(strategySummary?.active_strategies ?? 0);
    const totalStrategies = Number(strategySummary?.total_strategies ?? strategies.length ?? 0);
    const totalDatasets = Number(datasetSummary?.total_datasets ?? 0);
    const totalBacktestsValue = Number(strategySummary?.total_backtests ?? totalBacktests ?? 0);

    return {
      activeStrategies,
      totalStrategies,
      totalDatasets,
      totalBacktests: Number.isFinite(totalBacktestsValue) ? totalBacktestsValue : totalBacktests,
      runningJobs,
    };
  }, [strategyStatsQuery.data, strategies.length, datasetSummary, totalBacktests, runningJobs]);

  const hasAnyData = useMemo(() => {
    return (
      kpis.activeStrategies + kpis.totalDatasets + kpis.totalBacktests + kpis.runningJobs > 0 ||
      recentBacktests.length > 0 ||
      recentJobs.length > 0
    );
  }, [kpis, recentBacktests.length, recentJobs.length]);

  const initialLoading =
    strategyStatsQuery.isLoading ||
    strategiesQuery.isLoading ||
    backtestsQuery.isLoading ||
    datasetSummaryQuery.isLoading ||
    jobsQuery.isLoading ||
    jobStatsQuery.isLoading;
  const refetching =
    strategyStatsQuery.isFetching ||
    strategiesQuery.isFetching ||
    backtestsQuery.isFetching ||
    datasetSummaryQuery.isFetching ||
    jobsQuery.isFetching ||
    jobStatsQuery.isFetching;
  const loading = initialLoading || (refetching && !hasAnyData);

  const refetch = useCallback(async () => {
    await Promise.all([
      strategyStatsQuery.refetch({ cancelRefetch: false }),
      strategiesQuery.refetch({ cancelRefetch: false }),
      backtestsQuery.refetch({ cancelRefetch: false }),
      datasetSummaryQuery.refetch({ cancelRefetch: false }),
      jobsQuery.refetch({ cancelRefetch: false }),
      jobStatsQuery.refetch({ cancelRefetch: false }),
    ]);
  }, [
    strategyStatsQuery,
    strategiesQuery,
    backtestsQuery,
    datasetSummaryQuery,
    jobsQuery,
    jobStatsQuery,
  ]);

  return {
    loading,
    kpis,
    recentBacktests,
    recentJobs,
    latestCompletedBacktestId,
    topStrategies,
    mostTestedStrategies,
    datasetSummary,
    hasAnyData,
    refetch,
  } as const;
};
