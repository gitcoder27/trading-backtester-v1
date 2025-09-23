import { useQuery } from '@tanstack/react-query';
import { JobService } from '../services/backtest';

type JobsStatsResponse = {
  success?: boolean;
  stats?: {
    total_jobs?: number;
    pending?: number;
    running?: number;
    completed?: number;
    failed?: number;
    cancelled?: number;
  };
};

export function useJobStats() {
  return useQuery<JobsStatsResponse>({
    queryKey: ['jobs-stats'],
    queryFn: () => JobService.getJobStats(),
    staleTime: 30_000, // stats are volatile; refresh every 30s if needed
    refetchOnWindowFocus: false,
  });
}
