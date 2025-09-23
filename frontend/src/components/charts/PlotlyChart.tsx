import React from 'react';

interface PlotlyChartProps {
  data?: unknown[];
  layout?: Record<string, unknown>;
  config?: Record<string, unknown>;
  className?: string;
  loading?: boolean;
  error?: string | null;
}

const PlotlyChart: React.FC<PlotlyChartProps> = ({
  data: _data,
  layout: _layout = {},
  config: _config = {},
  className = '',
  loading: _loading = false,
  error: _error = null,
}) => (
  <div className={`w-full min-h-[200px] ${className}`} />
);

export default PlotlyChart;

/* Original Plotly implementation retained for future reference:
import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';
import { useThemeStore } from '../../stores/themeStore';

interface PlotlyChartProps {
  data: any[];
  layout?: Partial<Plotly.Layout>;
  config?: Partial<Plotly.Config>;
  className?: string;
  loading?: boolean;
  error?: string;
}

const PlotlyChart: React.FC<PlotlyChartProps> = ({
  data,
  layout = {},
  config = {},
  className = '',
  loading = false,
  error = null
}) => {
  const { actualTheme } = useThemeStore();
  const isDark = actualTheme === 'dark';

  const defaultLayout = useMemo(() => ({
    autosize: true,
    font: {
      family: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
      size: 12,
      color: isDark ? '#e5e7eb' : '#374151'
    },
    paper_bgcolor: isDark ? '#0f172a' : '#ffffff',
    plot_bgcolor: isDark ? '#020617' : '#f9fafb',
    colorway: [
      '#3b82f6', // blue
      '#10b981', // emerald
      '#f59e0b', // amber
      '#ef4444', // red
      '#8b5cf6', // violet
      '#06b6d4', // cyan
      '#f97316', // orange
      '#84cc16'  // lime
    ],
    xaxis: {
      gridcolor: isDark ? '#1e293b' : '#e5e7eb',
      zerolinecolor: isDark ? '#334155' : '#d1d5db',
      tickfont: {
        color: isDark ? '#cbd5e1' : '#6b7280'
      },
      title: {
        font: {
          color: isDark ? '#f1f5f9' : '#374151'
        }
      }
    },
    yaxis: {
      gridcolor: isDark ? '#1e293b' : '#e5e7eb',
      zerolinecolor: isDark ? '#334155' : '#d1d5db',
      tickfont: {
        color: isDark ? '#cbd5e1' : '#6b7280'
      },
      title: {
        font: {
          color: isDark ? '#f1f5f9' : '#374151'
        }
      }
    },
    margin: {
      l: 45,
      r: 15,
      t: 25,
      b: 45
    },
    ...layout
  }), [isDark, layout]);

  const mergedConfig = useMemo(() => ({
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToAdd: [
      {
        name: 'Export as PNG',
        icon: {
          width: 1000,
          height: 1000,
          path: 'M500,1000C223.9,1000,0,776.1,0,500S223.9,0,500,0s500,223.9,500,500S776.1,1000,500,1000z M500,100C279.0,100,100,279.0,100,500s179.0,400,400,400s400-179.0,400-400S721.0,100,500,100z M650,350L450,550L350,450l-75,75l175,175l275-275L650,350z',
          transform: 'matrix(1 0 0 -1 0 850)'
        },
        click: (gd: any) => {
          (window as any).Plotly.downloadImage(gd, {
            format: 'png',
            width: 1200,
            height: 600,
            filename: `chart_${Date.now()}`
          });
        }
      },
      {
        name: 'Export as SVG',
        icon: {
          width: 1000,
          height: 1000,
          path: 'M500,1000C223.9,1000,0,776.1,0,500S223.9,0,500,0s500,223.9,500,500S776.1,1000,500,1000z M500,100C279.0,100,100,279.0,100,500s179.0,400,400,400s400-179.0,400-400S721.0,100,500,100z M650,350L450,550L350,450l-75,75l175,175l275-275L650,350z',
          transform: 'matrix(1 0 0 -1 0 850)'
        },
        click: (gd: any) => {
          (window as any).Plotly.downloadImage(gd, {
            format: 'svg',
            width: 1200,
            height: 600,
            filename: `chart_${Date.now()}`
          });
        }
      }
    ],
    modeBarButtonsToRemove: [
      'pan2d',
      'lasso2d',
      'select2d',
      'autoScale2d',
      'hoverClosestCartesian',
      'hoverCompareCartesian',
      'toggleSpikelines',
      'sendDataToCloud'
    ],
    responsive: true,
    ...config
  }), [config]);

  if (loading) {
    return (
      <div className={`flex items-center justify-center h-64 ${className}`}>
        <div className="flex items-center space-x-2">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <span className="text-gray-600 dark:text-gray-400">Loading chart...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`flex items-center justify-center h-64 ${className}`}>
        <div className="text-center space-y-2">
          <div className="text-red-500 font-medium">Failed to load chart</div>
          <div className="text-sm text-gray-500 dark:text-gray-400">{error}</div>
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className={`flex items-center justify-center h-64 ${className}`}>
        <div className="text-center space-y-2">
          <div className="text-gray-500 dark:text-gray-400 font-medium">No data available</div>
          <div className="text-sm text-gray-400 dark:text-gray-500">Chart data is empty</div>
        </div>
      </div>
    );
  }

  return (
    <div className={`w-full h-full ${className}`} style={{ minHeight: '200px' }}>
      <Plot
        data={data}
        layout={defaultLayout}
        config={mergedConfig}
        useResizeHandler={true}
        style={{ width: '100%', height: '100%' }}
        className="overflow-hidden"
      />
    </div>
  );
};

export default PlotlyChart;
*/
