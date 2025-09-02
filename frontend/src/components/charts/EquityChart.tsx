import React from 'react';
import PlotlyChart from './PlotlyChart';

interface EquityChartProps {
  data?: Array<{timestamp: string; equity: number}>;
  backtestId?: string;
  className?: string;
}

const EquityChart: React.FC<EquityChartProps> = ({ data, className = '' }) => {
  const plotlyData = React.useMemo(() => {
    if (!data || data.length === 0) return [];

    // Convert timestamp strings to dates and equity values
    const dates = data.map(point => new Date(parseInt(point.timestamp) * 1000).toISOString());
    const equity = data.map(point => point.equity);

    return [
      {
        x: dates,
        y: equity,
        type: 'scatter',
        mode: 'lines',
        name: 'Portfolio Equity',
        line: {
          color: '#3b82f6',
          width: 2
        },
        hovertemplate: '<b>$%{y:,.2f}</b><br>%{x}<extra></extra>'
      }
    ];
  }, [data]);

  const layout = React.useMemo(() => ({
    title: {
      text: 'Portfolio Equity Curve',
      font: { size: 16 }
    },
    xaxis: {
      title: { text: 'Date' },
      type: 'date' as const
    },
    yaxis: {
      title: { text: 'Portfolio Value ($)' },
      tickformat: ',.0f'
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

export default EquityChart;
