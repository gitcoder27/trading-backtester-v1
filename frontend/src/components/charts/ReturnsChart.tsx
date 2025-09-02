import React from 'react';
import PlotlyChart from './PlotlyChart';

interface ReturnsChartProps {
  data?: Array<{timestamp: string; equity: number}>;
  backtestId?: string;
  className?: string;
}

const ReturnsChart: React.FC<ReturnsChartProps> = ({ data, className = '' }) => {
  const plotlyData = React.useMemo(() => {
    if (!data || data.length < 2) return [];

    // Calculate daily returns from equity curve
    const returns = [];
    for (let i = 1; i < data.length; i++) {
      const prevEquity = data[i - 1].equity;
      const currentEquity = data[i].equity;
      if (prevEquity > 0) {
        returns.push((currentEquity - prevEquity) / prevEquity);
      }
    }

    if (returns.length === 0) return [];

    return [
      {
        x: returns,
        type: 'histogram',
        name: 'Daily Returns',
        nbinsx: 30,
        marker: {
          color: '#3b82f6',
          opacity: 0.7
        },
        hovertemplate: '<b>%{y}</b> occurrences<br>Return: %{x:.2%}<extra></extra>'
      }
    ];
  }, [data]);

  const layout = React.useMemo(() => ({
    title: {
      text: 'Returns Distribution',
      font: { size: 16 }
    },
    xaxis: {
      title: { text: 'Daily Returns (%)' },
      tickformat: '.1%'
    },
    yaxis: {
      title: { text: 'Frequency' }
    },
    showlegend: false,
    bargap: 0.1
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

export default ReturnsChart;
