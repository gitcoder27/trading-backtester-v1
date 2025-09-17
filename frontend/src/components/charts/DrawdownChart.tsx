import React from 'react';
import { useQuery } from '@tanstack/react-query';
import PlotlyChart from './PlotlyChart';
import { AnalyticsService } from '../../services/analytics';
import { useInView } from '../../hooks/useInView';

interface DrawdownChartProps {
  data?: Array<{timestamp: string; equity: number}>;
  backtestId?: string;
  className?: string;
  maxPoints?: number;
}

const DrawdownChart: React.FC<DrawdownChartProps> = ({ data, backtestId, className = '', maxPoints = 1000 }) => {
  const { ref, inView } = useInView({ once: true, rootMargin: '0px 0px -15% 0px' });
  const { data: apiData, isLoading, error } = useQuery({
    queryKey: ['drawdown-chart', backtestId, maxPoints],
    queryFn: async () => AnalyticsService.getDrawdownChart(backtestId as string, { maxPoints }),
    enabled: !!backtestId && !data && inView,
    staleTime: 10 * 60 * 1000,
    keepPreviousData: true,
    refetchOnWindowFocus: false,
  });

  const { traces, layout } = React.useMemo(() => {
    if (data && data.length > 0) {
      const dates = data.map(point => new Date(parseInt(point.timestamp) * 1000).toISOString());
      const equity = data.map(point => point.equity);
      let peak = equity[0];
      const drawdown = equity.map(value => {
        if (value > peak) peak = value;
        return peak > 0 ? ((value - peak) / peak) * 100 : 0;
      });
      return {
        traces: [
          {
            x: dates,
            y: drawdown,
            type: 'scatter',
            mode: 'lines',
            name: 'Drawdown',
            fill: 'tonexty',
            fillcolor: 'rgba(239, 68, 68, 0.1)',
            line: { color: '#ef4444', width: 2 },
            hovertemplate: '<b>%{y:.2f}%</b><br>%{x}<extra></extra>'
          }
        ],
        layout: {
          title: { text: 'Portfolio Drawdown', font: { size: 16 } },
          xaxis: { title: { text: 'Date' }, type: 'date' as const },
          yaxis: { title: { text: 'Drawdown (%)' }, ticksuffix: '%' },
          hovermode: 'x unified' as const,
          showlegend: false
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
          console.warn('DrawdownChart: failed to parse chart payload', error);
        }
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

export default DrawdownChart;
