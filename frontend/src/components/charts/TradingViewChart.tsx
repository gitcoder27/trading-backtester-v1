import React, { useEffect, useRef, useState } from 'react';
import { 
  createChart, 
  CandlestickSeries,
  LineSeries,
  ColorType,
  createSeriesMarkers,
} from 'lightweight-charts';
import type { 
  IChartApi, 
  ISeriesApi, 
  CandlestickData, 
  LineData,
  SeriesMarker,
  UTCTimestamp
} from 'lightweight-charts';
import { Maximize2, Download, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';

interface CandleData {
  time: UTCTimestamp;
  open: number;
  high: number;
  low: number;
  close: number;
}

interface TradeMarker {
  time: UTCTimestamp;
  position: 'belowBar' | 'aboveBar';
  color: string;
  shape: 'arrowUp' | 'arrowDown' | 'circle' | 'square';
  text: string;
  size: number;
}

interface IndicatorLine {
  name: string;
  color: string;
  data: LineData[];
  lineWidth?: number;
  visible?: boolean;
}

interface TradingViewChartProps {
  candleData: CandleData[];
  tradeMarkers?: TradeMarker[];
  indicators?: IndicatorLine[];
  height?: number;
  theme?: 'light' | 'dark';
  title?: string;
  loading?: boolean;
  showControls?: boolean;
  autoFit?: boolean;
  dataBadge?: string; // small identifier like 'Real' or 'Sim'
  timeZone?: string; // e.g., 'Asia/Kolkata' for axis/crosshair formatting
}

const TradingViewChart: React.FC<TradingViewChartProps> = ({
  candleData,
  tradeMarkers = [],
  indicators = [],
  height = 600,
  theme = 'dark',
  title = 'Price Chart',
  loading = false,
  showControls = true,
  autoFit = true,
  dataBadge,
  timeZone
}) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const indicatorSeriesRef = useRef<Map<string, ISeriesApi<'Line'>>>(new Map());
  const markersPluginRef = useRef<any>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [visibleIndicators, setVisibleIndicators] = useState<Set<string>>(new Set());

  // Chart theme configuration
  // Time formatter respecting an explicit time zone
  const formatTimeInZone = (t: any) => {
    try {
      const date = typeof t === 'number' ? new Date(t * 1000) :
        (t?.year && t?.month && t?.day ? new Date(Date.UTC(t.year, t.month - 1, t.day)) : new Date());
      return new Intl.DateTimeFormat('en-IN', {
        timeZone: timeZone || 'UTC',
        year: 'numeric', month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit'
      }).format(date);
    } catch {
      const date = typeof t === 'number' ? new Date(t * 1000) : new Date();
      return date.toISOString();
    }
  };

  const getChartOptions = () => ({
    layout: {
      background: { 
        type: ColorType.Solid, 
        color: theme === 'dark' ? '#0a0e16' : '#ffffff' 
      },
      textColor: theme === 'dark' ? '#d1d5db' : '#374151',
      fontSize: 12,
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    },
    localization: {
      locale: 'en-IN',
      timeFormatter: (time: any) => formatTimeInZone(time),
      priceFormatter: (p: number) => (Math.abs(p) < 1 ? p.toFixed(4) : p.toFixed(2)),
      dateFormat: 'dd MMM yyyy'
    },
    grid: {
      vertLines: { 
        color: theme === 'dark' ? '#1f2937' : '#e5e7eb',
        visible: true,
      },
      horzLines: { 
        color: theme === 'dark' ? '#1f2937' : '#e5e7eb',
        visible: true,
      },
    },
    crosshair: {
      mode: 1 as const,
      vertLine: {
        color: theme === 'dark' ? '#6b7280' : '#9ca3af',
        width: 1 as const,
        style: 3 as const,
        visible: true,
        labelVisible: true,
      },
      horzLine: {
        color: theme === 'dark' ? '#6b7280' : '#9ca3af',
        width: 1 as const,
        style: 3 as const,
        visible: true,
        labelVisible: true,
      },
    },
    rightPriceScale: {
      borderColor: theme === 'dark' ? '#374151' : '#d1d5db',
      visible: true,
      borderVisible: true,
      scaleMargins: {
        top: 0.1,
        bottom: 0.1,
      },
    },
    timeScale: {
      borderColor: theme === 'dark' ? '#374151' : '#d1d5db',
      borderVisible: true,
      fixLeftEdge: false,
      fixRightEdge: false,
      lockVisibleTimeRangeOnResize: true,
      rightBarStaysOnScroll: true,
      shiftVisibleRangeOnNewBar: true,
      timeVisible: true,
      secondsVisible: false,
      tickMarkFormatter: (time: any) => {
        // Axis labels: show only HH:mm for intraday, or date for daily
        try {
          const d = new Date((time as number) * 1000);
          const opts: Intl.DateTimeFormatOptions = {
            timeZone: timeZone || 'UTC',
            hour: '2-digit', minute: '2-digit'
          };
          return new Intl.DateTimeFormat('en-IN', opts).format(d);
        } catch {
          return String(time);
        }
      },
    },
    handleScroll: {
      mouseWheel: true,
      pressedMouseMove: true,
      horzTouchDrag: true,
      vertTouchDrag: true,
    },
    handleScale: {
      axisPressedMouseMove: true,
      mouseWheel: true,
      pinch: true,
    },
  });

  // Candlestick series configuration
  const getCandlestickOptions = () => ({
    upColor: '#26a69a',
    downColor: '#ef5350',
    borderVisible: false,
    wickUpColor: '#26a69a',
    wickDownColor: '#ef5350',
    priceLineVisible: true,
    lastValueVisible: true,
  });

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current || loading) return;

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      ...getChartOptions(),
      width: chartContainerRef.current.clientWidth,
      height: height,
    });

    chartRef.current = chart;

    // Add candlestick series
    const candleSeries = chart.addSeries(CandlestickSeries, getCandlestickOptions());
    candleSeriesRef.current = candleSeries;

    // Prepare markers plugin attached to the candlestick series
    try {
      markersPluginRef.current = createSeriesMarkers(candleSeries);
    } catch (err) {
      // Plugin not available; markers will be skipped gracefully
      markersPluginRef.current = null;
    }

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chart) {
        chart.applyOptions({ 
          width: chartContainerRef.current.clientWidth,
          height: isFullscreen ? window.innerHeight - 100 : height 
        });
      }
    };

    const resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(chartContainerRef.current);

    // Cleanup
    return () => {
      resizeObserver.disconnect();
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
      candleSeriesRef.current = null;
      if (markersPluginRef.current && typeof markersPluginRef.current.detach === 'function') {
        try { markersPluginRef.current.detach(); } catch {}
      }
      markersPluginRef.current = null;
      indicatorSeriesRef.current.clear();
    };
  }, [height, theme, loading, isFullscreen]);

  // Update candlestick data
  useEffect(() => {
    if (!candleSeriesRef.current || !candleData.length) return;

    try {
      const formattedData: CandlestickData[] = candleData.map(candle => ({
        time: candle.time,
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close,
      }));

      candleSeriesRef.current.setData(formattedData);

      if (autoFit && chartRef.current) {
        setTimeout(() => {
          chartRef.current?.timeScale().fitContent();
        }, 100);
      }
    } catch (error) {
      console.error('Error setting candlestick data:', error);
    }
  }, [candleData, autoFit]);

  // Update trade markers via series markers plugin
  // Include candleData so markers apply after series creation/data load as well
  useEffect(() => {
    if (!candleSeriesRef.current || !tradeMarkers.length) return;

    try {
      const formattedMarkers: SeriesMarker<UTCTimestamp>[] = tradeMarkers.map(marker => ({
        time: marker.time,
        position: marker.position,
        color: marker.color,
        shape: marker.shape,
        text: marker.text,
        size: marker.size || 1,
      }));

      // Prefer plugin API for modern lightweight-charts
      if (markersPluginRef.current && typeof markersPluginRef.current.setMarkers === 'function') {
        markersPluginRef.current.setMarkers(formattedMarkers);
      }
    } catch (error) {
      console.error('Error setting trade markers:', error);
    }
  }, [tradeMarkers, candleData]);

  // Update indicators
  useEffect(() => {
    if (!chartRef.current) return;

    // Remove existing indicator series
    indicatorSeriesRef.current.forEach((series) => {
      chartRef.current?.removeSeries(series);
    });
    indicatorSeriesRef.current.clear();

    // Add new indicator series
    indicators.forEach((indicator) => {
      if (!chartRef.current) return;

      try {
        const lineSeries = chartRef.current.addSeries(LineSeries, {
          color: indicator.color,
          lineWidth: (indicator.lineWidth || 2) as any,
          priceLineVisible: false,
          lastValueVisible: true,
          crosshairMarkerVisible: true,
          title: indicator.name,
        });

        lineSeries.setData(indicator.data);
        indicatorSeriesRef.current.set(indicator.name, lineSeries);

        // Set initial visibility
        if (indicator.visible === false) {
          lineSeries.applyOptions({ visible: false });
        } else {
          setVisibleIndicators(prev => new Set([...prev, indicator.name]));
        }
      } catch (error) {
        console.error(`Error adding indicator ${indicator.name}:`, error);
      }
    });
  }, [indicators]);

  // Chart control functions
  const handleZoomIn = () => {
    if (!chartRef.current) return;
    const timeScale = chartRef.current.timeScale();
    const visibleRange = timeScale.getVisibleRange();
    if (visibleRange) {
      const range = (visibleRange.to as number) - (visibleRange.from as number);
      const newRange = range * 0.8;
      const center = ((visibleRange.from as number) + (visibleRange.to as number)) / 2;
      timeScale.setVisibleRange({
        from: (center - newRange / 2) as UTCTimestamp,
        to: (center + newRange / 2) as UTCTimestamp,
      });
    }
  };

  const handleZoomOut = () => {
    if (!chartRef.current) return;
    const timeScale = chartRef.current.timeScale();
    const visibleRange = timeScale.getVisibleRange();
    if (visibleRange) {
      const range = (visibleRange.to as number) - (visibleRange.from as number);
      const newRange = range * 1.2;
      const center = ((visibleRange.from as number) + (visibleRange.to as number)) / 2;
      timeScale.setVisibleRange({
        from: (center - newRange / 2) as UTCTimestamp,
        to: (center + newRange / 2) as UTCTimestamp,
      });
    }
  };

  const handleReset = () => {
    if (!chartRef.current) return;
    chartRef.current.timeScale().fitContent();
  };

  const handleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  const handleDownload = () => {
    if (!chartRef.current) return;
    
    try {
      const canvas = chartContainerRef.current?.querySelector('canvas');
      if (canvas) {
        const link = document.createElement('a');
        link.download = `chart_${new Date().toISOString().split('T')[0]}.png`;
        link.href = canvas.toDataURL();
        link.click();
      }
    } catch (error) {
      console.error('Error downloading chart:', error);
    }
  };

  const toggleIndicator = (indicatorName: string) => {
    const series = indicatorSeriesRef.current.get(indicatorName);
    if (series) {
      const isVisible = visibleIndicators.has(indicatorName);
      series.applyOptions({ visible: !isVisible });
      
      setVisibleIndicators(prev => {
        const newSet = new Set(prev);
        if (isVisible) {
          newSet.delete(indicatorName);
        } else {
          newSet.add(indicatorName);
        }
        return newSet;
      });
    }
  };

  if (loading) {
    return (
      <div 
        className="flex items-center justify-center bg-gray-900 rounded-lg"
        style={{ height: height }}
      >
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading chart data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative bg-gray-900 rounded-lg overflow-hidden ${isFullscreen ? 'fixed inset-0 z-50' : ''}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center space-x-3">
          <h3 className="text-lg font-semibold text-white">{title}</h3>
          {dataBadge && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-700 text-gray-300 border border-gray-600">
              {dataBadge}
            </span>
          )}
          {candleData.length > 0 && (
            <span className="text-sm text-gray-400">
              {candleData.length.toLocaleString()} candles
            </span>
          )}
        </div>

        {showControls && (
          <div className="flex items-center space-x-2">
            {/* Indicator toggles */}
            {indicators.length > 0 && (
              <div className="flex items-center space-x-2 mr-4">
                {indicators.map((indicator) => (
                  <button
                    key={indicator.name}
                    onClick={() => toggleIndicator(indicator.name)}
                    className={`px-2 py-1 text-xs rounded ${
                      visibleIndicators.has(indicator.name)
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-600 text-gray-300'
                    }`}
                    style={{
                      borderLeft: `3px solid ${indicator.color}`,
                    }}
                  >
                    {indicator.name}
                  </button>
                ))}
              </div>
            )}

            {/* Chart controls */}
            <button
              onClick={handleZoomIn}
              className="p-2 text-gray-400 hover:text-white transition-colors"
              title="Zoom In"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <button
              onClick={handleZoomOut}
              className="p-2 text-gray-400 hover:text-white transition-colors"
              title="Zoom Out"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <button
              onClick={handleReset}
              className="p-2 text-gray-400 hover:text-white transition-colors"
              title="Fit Content"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
            <button
              onClick={handleDownload}
              className="p-2 text-gray-400 hover:text-white transition-colors"
              title="Download PNG"
            >
              <Download className="w-4 h-4" />
            </button>
            <button
              onClick={handleFullscreen}
              className="p-2 text-gray-400 hover:text-white transition-colors"
              title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
            >
              <Maximize2 className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* Chart container */}
      <div 
        ref={chartContainerRef}
        className="w-full"
        style={{ height: isFullscreen ? window.innerHeight - 100 : height }}
      />

      {/* Attribution */}
      <div className="absolute bottom-2 right-2 text-xs text-gray-500">
        Charting by{' '}
        <a 
          href="https://www.tradingview.com/" 
          target="_blank" 
          rel="noopener noreferrer"
          className="text-blue-400 hover:text-blue-300"
        >
          TradingView
        </a>
      </div>
    </div>
  );
};

export default TradingViewChart;
