import { useQuery } from '@tanstack/react-query';
import type { PerformanceData } from './types';
import { AnalyticsService } from '../../../services/analytics';

export const usePerformanceData = (
  backtestId: string,
  options?: { enabled?: boolean; sections?: string[] }
) => {
  const sections = options?.sections ?? [
    'basic_metrics',
    'advanced_analytics',
    'risk_metrics',
    'trade_analysis',
    'daily_target_stats',
    'drawdown_analysis',
  ];

  const { data, isLoading, error } = useQuery({
    queryKey: ['performance', backtestId, sections.join(',')],
    queryFn: () => AnalyticsService.getPerformanceSummary(backtestId, sections),
    enabled: !!backtestId && (options?.enabled ?? true),
    staleTime: 10 * 60 * 1000,
    keepPreviousData: true,
    refetchOnWindowFocus: false,
    retry: 1,
  });

  return {
    data: data as PerformanceData | undefined,
    isLoading,
    error,
    performance: (data as any)?.performance
  };
};
