import React from 'react';
import { useQuery } from '@tanstack/react-query';
import PlotlyChart from './PlotlyChart';
import { AnalyticsService } from '../../services/analytics';

interface TradeAnalysisChartProps {
  data?: Array<any>;
  backtestId?: string;
  className?: string;
}

const TradeAnalysisChart: React.FC<TradeAnalysisChartProps> = ({ data, backtestId, className = '' }) => {
  // Fetch from backend when backtestId provided and no data prop
  const { data: apiData, isLoading, error } = useQuery({
    queryKey: ['trades-chart', backtestId],
    queryFn: async () => AnalyticsService.getTradesChart(backtestId as string),
    enabled: !!backtestId && !data,
    staleTime: 10 * 60 * 1000,
    keepPreviousData: true,
    refetchOnWindowFocus: false,
  });

  // Build traces/layout either from provided trades or backend Plotly figure
  const { traces, layout } = React.useMemo(() => {
    if (data && data.length > 0) {
      const winningTrades = data.filter(trade => parseFloat(trade.pnl || 0) > 0);
      const losingTrades = data.filter(trade => parseFloat(trade.pnl || 0) <= 0);
      const localTraces: any[] = [];
      if (winningTrades.length > 0) {
        localTraces.push({
          x: winningTrades.map(trade => trade.entry_time || trade.entry_date),
          y: winningTrades.map(trade => {
            const pnl = parseFloat(trade.pnl || 0);
            const entryPrice = parseFloat(trade.entry_price || 1);
            return entryPrice > 0 ? (pnl / entryPrice) * 100 : 0;
          }),
          mode: 'markers',
          type: 'scatter',
          name: 'Winning Trades',
          marker: { color: '#10b981', size: 8, symbol: 'triangle-up' },
          hovertemplate: '<b>+%{y:.2f}%</b> profit<br>%{x}<extra></extra>'
        });
      }
      if (losingTrades.length > 0) {
        localTraces.push({
          x: losingTrades.map(trade => trade.entry_time || trade.entry_date),
          y: losingTrades.map(trade => {
            const pnl = parseFloat(trade.pnl || 0);
            const entryPrice = parseFloat(trade.entry_price || 1);
            return entryPrice > 0 ? (pnl / entryPrice) * 100 : 0;
          }),
          mode: 'markers',
          type: 'scatter',
          name: 'Losing Trades',
          marker: { color: '#ef4444', size: 8, symbol: 'triangle-down' },
          hovertemplate: '<b>%{y:.2f}%</b> loss<br>%{x}<extra></extra>'
        });
      }
      const localLayout: Partial<Plotly.Layout> = {
        title: { text: 'Trade Analysis', font: { size: 16 } },
        xaxis: { title: { text: 'Trade Date' }, type: 'date' as const },
        yaxis: { title: { text: 'P&L (%)' }, ticksuffix: '%', zeroline: true, zerolinewidth: 2 },
        hovermode: 'closest' as const,
        showlegend: true,
        legend: { x: 0.02, y: 0.98 }
      };
      return { traces: localTraces, layout: localLayout };
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

  const errMsg = error ? (error as Error).message : (!data && !isLoading && (!apiData || !(apiData as any).chart) ? 'No trade data available' : undefined);

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

export default TradeAnalysisChart;
