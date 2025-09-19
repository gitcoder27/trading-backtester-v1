import React from 'react';
import { useQuery, keepPreviousData } from '@tanstack/react-query';
import PlotlyChart from './PlotlyChart';
import { AnalyticsService } from '../../services/analytics';

interface ReturnsChartProps {
  data?: Array<{timestamp: string; equity: number}>;
  backtestId?: string;
  className?: string;
}

const ReturnsChart: React.FC<ReturnsChartProps> = ({ data, backtestId, className = '' }) => {
  const { data: apiData, isLoading, error } = useQuery({
    queryKey: ['returns-chart', backtestId],
    queryFn: async () => AnalyticsService.getReturnsChart(backtestId as string),
    enabled: !!backtestId && !data,
    staleTime: 10 * 60 * 1000,
    placeholderData: keepPreviousData,
    refetchOnWindowFocus: false,
  });

  const { traces, layout } = React.useMemo(() => {
    if (data && data.length > 1) {
      const returns: number[] = [];
      for (let i = 1; i < data.length; i++) {
        const prevEquity = data[i - 1].equity;
        const currentEquity = data[i].equity;
        if (prevEquity > 0) returns.push((currentEquity - prevEquity) / prevEquity);
      }
      if (returns.length === 0) return { traces: [], layout: {} };
      return {
        traces: [
          {
            x: returns,
            type: 'histogram',
            name: 'Daily Returns',
            nbinsx: 30,
            marker: { color: '#3b82f6', opacity: 0.7 },
            hovertemplate: '<b>%{y}</b> occurrences<br>Return: %{x:.2%}<extra></extra>'
          }
        ],
        layout: {
          title: { text: 'Returns Distribution', font: { size: 16 } },
          xaxis: { title: { text: 'Daily Returns (%)' }, tickformat: '.1%' },
          yaxis: { title: { text: 'Frequency' } },
          showlegend: false,
          bargap: 0.1
        } as Partial<Plotly.Layout>
      };
    }
    const chartStr = (apiData as any)?.chart;
    if (chartStr) {
      try {
        const fig = JSON.parse(chartStr);
        return { traces: fig.data || [], layout: fig.layout || {} };
      } catch (error) {
        if (typeof import.meta !== 'undefined' && import.meta.env?.DEV) {
          console.warn('ReturnsChart: failed to parse chart payload', error);
        }
      }
    }
    return { traces: [], layout: {} };
  }, [data, apiData]);

  const errMsg = error ? (error as Error).message : (!data && !isLoading && (!apiData || !(apiData as any).chart) ? 'No equity data available' : undefined);

  return (
    <PlotlyChart
      data={traces}
      layout={layout}
      loading={!!backtestId && !data ? isLoading : false}
      error={errMsg}
      className={className}
    />
  );
};

export default ReturnsChart;
