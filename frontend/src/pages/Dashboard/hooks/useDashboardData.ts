import { useState, useEffect, useMemo } from 'react';
import { showToast } from '../../../components/ui/Toast';
import { StrategyService } from '../../../services/strategyService';
import { BacktestService, JobService } from '../../../services/backtest';
import { DatasetService } from '../../../services/dataset';
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

export const useDashboardData = () => {
  const [loading, setLoading] = useState(true);
  const [kpis, setKpis] = useState<KpiStats>({
    activeStrategies: 0,
    totalStrategies: 0,
    totalDatasets: 0,
    totalBacktests: 0,
    runningJobs: 0,
  });
  const [recentBacktests, setRecentBacktests] = useState<any[]>([]);
  const [recentJobs, setRecentJobs] = useState<any[]>([]);
  const [latestCompletedBacktestId, setLatestCompletedBacktestId] = useState<string | null>(null);
  const [topStrategies, setTopStrategies] = useState<Strategy[]>([]);
  const [mostTestedStrategies, setMostTestedStrategies] = useState<Strategy[]>([]);
  const [datasetSummary, setDatasetSummary] = useState<DatasetSummary | null>(null);

  const loadDashboardData = async () => {
    try {
      setLoading(true);

      const [strategyStatsRaw, strategiesRaw, backtestsRaw, jobsRaw, jobsStatsRaw, datasetSummaryRaw] = await Promise.all([
        StrategyService.getStrategyStats().catch(() => ({} as any)),
        StrategyService.getStrategies().catch(() => [] as Strategy[]),
        BacktestService.listBacktests({ page: 1, size: 10, compact: true } as any).catch(() => ({} as any)),
        JobService.listJobs({ page: 1, size: 5 }).catch(() => ({} as any)),
        JobService.getJobStats().catch(() => ({} as any)),
        DatasetService.getSummary().catch(() => ({} as any)),
      ]);

      // Strategy summary
      const strategySummary = (strategyStatsRaw as any).summary || strategyStatsRaw || {};
      const activeStrategies = Number(strategySummary.active_strategies || 0);
      const totalStrategies = Number(strategySummary.total_strategies || 0);

      // Backtests list and total
      const btItems: any[] = (backtestsRaw as any).results || (backtestsRaw as any).items || (backtestsRaw as any).data || [];
      const btTotal: number = Number((backtestsRaw as any).total || strategySummary.total_backtests || btItems.length || 0);

      // Sort backtests by created_at desc and pick latest completed for snapshot
      const sortedByDate = [...btItems].sort((a, b) => {
        const aTs = a.created_at ? new Date(a.created_at).getTime() : 0;
        const bTs = b.created_at ? new Date(b.created_at).getTime() : 0;
        return bTs - aTs;
      });
      const latestCompleted = sortedByDate.find((b) => b.status === 'completed');
      setLatestCompletedBacktestId(latestCompleted?.id ? String(latestCompleted.id) : null);
      setRecentBacktests(sortedByDate.slice(0, 5));

      // Jobs list and stats
      const jobs: any[] = (jobsRaw as any).jobs || (jobsRaw as any).items || [];
      setRecentJobs(jobs.slice(0, 5));
      const runningJobs = Number(((jobsStatsRaw as any).stats?.running) ?? jobs.filter(j => j.status === 'running').length);

      // Dataset summary
      const dsSummary: DatasetSummary | null = (datasetSummaryRaw as any).summary || null;
      setDatasetSummary(dsSummary);

      // Strategy highlights
      const strategies: Strategy[] = Array.isArray(strategiesRaw) ? strategiesRaw : [];
      let top = [...strategies]
        .filter(s => typeof (s as any).avg_performance === 'number')
        .sort((a: any, b: any) => (b.avg_performance ?? 0) - (a.avg_performance ?? 0))
        .slice(0, 3);

      // Fallback: compute top performers from recent backtests if strategies lack avg_performance
      if (top.length === 0 && btItems.length > 0) {
        const byStrategy: Record<string, { name: string; returns: number[]; count: number } > = {};
        for (const bt of btItems) {
          if (bt.status !== 'completed') continue;
          const metrics = bt.results?.metrics || bt.metrics || bt.results || {};
          const raw = (metrics.total_return_percent ?? metrics.total_return_pct);
          let pct: number | null = null;
          if (typeof raw === 'number') pct = raw;
          else if (typeof metrics.total_return === 'number') pct = Math.abs(metrics.total_return) <= 1 ? metrics.total_return * 100 : metrics.total_return;
          if (pct === null || Number.isNaN(pct)) continue;

          const name = String(bt.strategy_name || bt.strategy_id || 'Unknown');
          if (!byStrategy[name]) byStrategy[name] = { name, returns: [], count: 0 };
          byStrategy[name].returns.push(pct);
          byStrategy[name].count += 1;
        }
        const aggregates = Object.values(byStrategy)
          .map(s => ({
            id: s.name,
            name: s.name,
            avg_performance: s.returns.reduce((a, b) => a + b, 0) / Math.max(1, s.returns.length),
            total_backtests: s.count
          }))
          .sort((a, b) => (b.avg_performance ?? 0) - (a.avg_performance ?? 0))
          .slice(0, 3) as any;
        top = aggregates as Strategy[];
      }
      setTopStrategies(top as Strategy[]);

      // Most tested strategies (prefer DB field, fallback to recent backtests)
      let mostTested = [...strategies]
        .sort((a: any, b: any) => (b.total_backtests ?? 0) - (a.total_backtests ?? 0))
        .slice(0, 3);
      if (mostTested.length === 0 && btItems.length > 0) {
        const counts: Record<string, number> = {};
        for (const bt of btItems) {
          const name = String(bt.strategy_name || bt.strategy_id || 'Unknown');
          counts[name] = (counts[name] || 0) + 1;
        }
        mostTested = Object.entries(counts)
          .map(([name, count]) => ({ id: name, name, total_backtests: count } as any))
          .sort((a, b) => (b.total_backtests ?? 0) - (a.total_backtests ?? 0))
          .slice(0, 3);
      }
      setMostTestedStrategies(mostTested as Strategy[]);

      // KPIs
      setKpis({
        activeStrategies,
        totalStrategies,
        totalDatasets: Number(dsSummary?.total_datasets || 0),
        totalBacktests: btTotal,
        runningJobs,
      });
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      showToast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const hasAnyData = useMemo(() => {
    return (
      kpis.activeStrategies + kpis.totalDatasets + kpis.totalBacktests + kpis.runningJobs > 0 ||
      recentBacktests.length > 0 || recentJobs.length > 0
    );
  }, [kpis, recentBacktests, recentJobs]);

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
    refetch: loadDashboardData,
  };
};
