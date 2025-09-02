import { useQuery } from '@tanstack/react-query';
import type { PerformanceData } from './types';

const fetchPerformanceData = async (backtestId: string): Promise<PerformanceData> => {
  const response = await fetch(`http://localhost:8000/api/v1/analytics/performance/${backtestId}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch performance data: ${response.statusText}`);
  }
  
  return response.json();
};

export const usePerformanceData = (backtestId: string) => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['performance', backtestId],
    queryFn: () => fetchPerformanceData(backtestId),
    enabled: !!backtestId,
  });

  return {
    data,
    isLoading,
    error,
    performance: data?.performance
  };
};
