import React from 'react';
import PlotlyChart from './PlotlyChart';

interface DrawdownChartProps {
  data?: Array<{timestamp: string; equity: number}>;
  backtestId?: string;
  className?: string;
}

const DrawdownChart: React.FC<DrawdownChartProps> = ({ data, className = '' }) => {
  const plotlyData = React.useMemo(() => {
    if (!data || data.length === 0) return [];

    // Calculate drawdown from equity curve
    const dates = data.map(point => new Date(parseInt(point.timestamp) * 1000).toISOString());
    const equity = data.map(point => point.equity);
    
    // Calculate running maximum (peak)
    let peak = equity[0];
    const drawdown = equity.map(value => {
      if (value > peak) peak = value;
      return peak > 0 ? ((value - peak) / peak) * 100 : 0;
    });

    return [
      {
        x: dates,
        y: drawdown,
        type: 'scatter',
        mode: 'lines',
        name: 'Drawdown',
        fill: 'tonexty',
        fillcolor: 'rgba(239, 68, 68, 0.1)',
        line: {
          color: '#ef4444',
          width: 2
        },
        hovertemplate: '<b>%{y:.2f}%</b><br>%{x}<extra></extra>'
      }
    ];
  }, [data]);

  const layout = React.useMemo(() => ({
    title: {
      text: 'Portfolio Drawdown',
      font: { size: 16 }
    },
    xaxis: {
      title: { text: 'Date' },
      type: 'date' as const
    },
    yaxis: {
      title: { text: 'Drawdown (%)' },
      ticksuffix: '%'
    },
    hovermode: 'x unified' as const,
    showlegend: false
  }), []);

  return (
    <PlotlyChart
      data={plotlyData}
      layout={layout}
      loading={false}
      error={data ? undefined : 'No equity data available'}
      className={className}
    />
  );
};

export default DrawdownChart;
