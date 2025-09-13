import React from 'react';
import { useQuery } from '@tanstack/react-query';
import PlotlyChart from './PlotlyChart';
import { AnalyticsService } from '../../services/analytics';
import { useInView } from '../../hooks/useInView';

interface EquityChartProps {
  data?: Array<{timestamp: string; equity: number}>;
  backtestId?: string;
  className?: string;
  maxPoints?: number;
}

const EquityChart: React.FC<EquityChartProps> = ({ data, backtestId, className = '', maxPoints = 1000 }) => {
  // If data not provided, fetch Plotly figure from backend
  const { ref, inView } = useInView({ once: true, rootMargin: '0px 0px -15% 0px' });
  const { data: apiData, isLoading, error } = useQuery({
    queryKey: ['equity-chart', backtestId, maxPoints],
    queryFn: async () => AnalyticsService.getEquityChart(backtestId as string, { maxPoints }),
    enabled: !!backtestId && !data && inView,
    staleTime: 10 * 60 * 1000,
    keepPreviousData: true,
    refetchOnWindowFocus: false,
  });

  // Build traces/layout from either provided data or API figure
  const { traces, layout } = React.useMemo(() => {
    // Path 1: provided simple equity data
    if (data && data.length > 0) {
      const dates = data.map(point => new Date(parseInt(point.timestamp) * 1000).toISOString());
      const equity = data.map(point => point.equity);
      return {
        traces: [
          {
            x: dates,
            y: equity,
            type: 'scatter',
            mode: 'lines',
            name: 'Portfolio Equity',
            line: { color: '#3b82f6', width: 2 },
            hovertemplate: '<b>$%{y:,.2f}</b><br>%{x}<extra></extra>'
          }
        ],
        layout: {
          title: { text: 'Portfolio Equity Curve', font: { size: 16 } },
          xaxis: { title: { text: 'Date' }, type: 'date' as const },
          yaxis: { title: { text: 'Portfolio Value ($)' }, tickformat: ',.0f' },
          hovermode: 'x unified' as const,
          showlegend: false
        } as Partial<Plotly.Layout>
      };
    }

    // Path 2: parse Plotly figure JSON from API
    const chartStr = (apiData as any)?.chart;
    if (chartStr) {
      try {
        const fig = JSON.parse(chartStr);
        return { traces: fig.data || [], layout: fig.layout || {} };
      } catch {
        // fallthrough to empty
      }
    }
    return { traces: [], layout: {} };
  }, [data, apiData]);

  const errMsg = error ? (error as Error).message : (!data && !isLoading && (!apiData || !(apiData as any).chart) ? 'No equity data available' : undefined);

  return (
    <div ref={ref} className={className}>
      <PlotlyChart
        data={traces}
        layout={layout}
        loading={!!backtestId && !data ? (isLoading || !inView) : false}
        error={errMsg}
      />
    </div>
  );
};

export default EquityChart;
