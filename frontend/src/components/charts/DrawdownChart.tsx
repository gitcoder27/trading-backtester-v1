import React from 'react';
import { useQuery } from '@tanstack/react-query';
import PlotlyChart from './PlotlyChart';
import { AnalyticsService } from '../../services/analytics';

interface DrawdownChartProps {
  data?: Array<{timestamp: string; equity: number}>;
  backtestId?: string;
  className?: string;
}

const DrawdownChart: React.FC<DrawdownChartProps> = ({ data, backtestId, className = '' }) => {
  const { data: apiData, isLoading, error } = useQuery({
    queryKey: ['drawdown-chart', backtestId],
    queryFn: async () => AnalyticsService.getDrawdownChart(backtestId as string),
    enabled: !!backtestId && !data,
    staleTime: 5 * 60 * 1000,
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
      } catch {}
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

export default DrawdownChart;
