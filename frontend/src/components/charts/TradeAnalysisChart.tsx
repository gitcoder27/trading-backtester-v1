import React from 'react';
import PlotlyChart from './PlotlyChart';

interface TradeAnalysisChartProps {
  data?: Array<any>;
  backtestId?: string;
  className?: string;
}

const TradeAnalysisChart: React.FC<TradeAnalysisChartProps> = ({ data, className = '' }) => {
  const plotlyData = React.useMemo(() => {
    if (!data || data.length === 0) return [];

    const traces = [];
    
    // Separate winning and losing trades
    const winningTrades = data.filter(trade => parseFloat(trade.pnl || 0) > 0);
    const losingTrades = data.filter(trade => parseFloat(trade.pnl || 0) <= 0);

    // Winning trades
    if (winningTrades.length > 0) {
      traces.push({
        x: winningTrades.map(trade => trade.entry_time || trade.entry_date),
        y: winningTrades.map(trade => {
          const pnl = parseFloat(trade.pnl || 0);
          const entryPrice = parseFloat(trade.entry_price || 1);
          return entryPrice > 0 ? (pnl / entryPrice) * 100 : 0;
        }),
        mode: 'markers',
        type: 'scatter',
        name: 'Winning Trades',
        marker: {
          color: '#10b981',
          size: 8,
          symbol: 'triangle-up'
        },
        hovertemplate: '<b>+%{y:.2f}%</b> profit<br>%{x}<extra></extra>'
      });
    }

    // Losing trades
    if (losingTrades.length > 0) {
      traces.push({
        x: losingTrades.map(trade => trade.entry_time || trade.entry_date),
        y: losingTrades.map(trade => {
          const pnl = parseFloat(trade.pnl || 0);
          const entryPrice = parseFloat(trade.entry_price || 1);
          return entryPrice > 0 ? (pnl / entryPrice) * 100 : 0;
        }),
        mode: 'markers',
        type: 'scatter',
        name: 'Losing Trades',
        marker: {
          color: '#ef4444',
          size: 8,
          symbol: 'triangle-down'
        },
        hovertemplate: '<b>%{y:.2f}%</b> loss<br>%{x}<extra></extra>'
      });
    }

    return traces;
  }, [data]);

  const layout = React.useMemo(() => ({
    title: {
      text: 'Trade Analysis',
      font: { size: 16 }
    },
    xaxis: {
      title: { text: 'Trade Date' },
      type: 'date' as const
    },
    yaxis: {
      title: { text: 'P&L (%)' },
      ticksuffix: '%',
      zeroline: true,
      zerolinewidth: 2
    },
    hovermode: 'closest' as const,
    showlegend: true,
    legend: {
      x: 0.02,
      y: 0.98
    }
  }), []);

  return (
    <PlotlyChart
      data={plotlyData}
      layout={layout}
      loading={false}
      error={data ? undefined : 'No trade data available'}
      className={className}
    />
  );
};

export default TradeAnalysisChart;
