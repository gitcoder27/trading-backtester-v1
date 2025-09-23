import React, { useEffect, useRef, useState } from 'react';
import type { CandlestickData, SeriesMarker, UTCTimestamp, Time } from 'lightweight-charts';
import { useTradingViewChart } from '../../hooks/charts/useTradingViewChart';
import { useSeriesMarkers } from '../../hooks/charts/useSeriesMarkers';
import { useIndicators } from '../../hooks/charts/useIndicators';
import ChartControls from './ChartControls';
import type { CandleData, TradeMarker, IndicatorLine } from '../../types/chart';
import { getChartOptions } from '../../utils/chartOptions';

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
  const isDevEnv = typeof import.meta !== 'undefined' && Boolean(import.meta.env?.DEV);
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const { chartRef, candleSeriesRef, ready } = useTradingViewChart(chartContainerRef, { height, theme, timeZone, isFullscreen, enabled: !loading, withCandles: true });

  // Split indicators into overlay (with price) and separate pane (oscillators like RSI/MACD)
  const overlayIndicators = React.useMemo(() => (indicators || []).filter(ind => {
    // Respect explicit pane flag if provided
    if ((ind as any).pane === 'separate') return false;
    // Heuristic: common oscillators should be in a separate pane
    const name = (ind.name || '').toLowerCase();
    const separateNames = ['rsi', 'macd', 'stoch', 'stochastic', 'cci', 'atr'];
    return !separateNames.some(k => name.includes(k));
  }), [indicators]);

  const separateIndicators = React.useMemo(() => (indicators || []).filter(ind => {
    if ((ind as any).pane === 'separate') return true;
    const name = (ind.name || '').toLowerCase();
    const separateNames = ['rsi', 'macd', 'stoch', 'stochastic', 'cci', 'atr'];
    return separateNames.some(k => name.includes(k));
  }), [indicators]);

  const { visibleIndicators: visibleOverlay, toggleIndicator: toggleOverlay } = useIndicators(chartRef, overlayIndicators, ready);
  useSeriesMarkers(
    candleSeriesRef,
    (tradeMarkers || []).map(m => ({ ...m, size: (m as any).size || 1 })) as SeriesMarker<Time>[],
    ready
  );

  // Separate pane for oscillators
  const paneContainerRef = useRef<HTMLDivElement>(null);
  const paneHeight = separateIndicators.length > 0 ? Math.max(160, Math.round(height * 0.28)) : 0;
  const { chartRef: paneChartRef, ready: paneReady } = useTradingViewChart(
    paneContainerRef,
    { height: paneHeight, theme, timeZone, isFullscreen, enabled: !loading && separateIndicators.length > 0, withCandles: false }
  );
  const { visibleIndicators: visiblePane, toggleIndicator: togglePane } = useIndicators(paneChartRef, separateIndicators, paneReady);

  // Combine indicator visibility and toggles for controls
  const allIndicators = React.useMemo(() => [...overlayIndicators, ...separateIndicators], [overlayIndicators, separateIndicators]);
  const visibleCombined = React.useMemo(() => {
    const s = new Set<string>();
    visibleOverlay.forEach(v => s.add(v));
    visiblePane.forEach(v => s.add(v));
    return s;
  }, [visibleOverlay, visiblePane]);
  const overlayNames = React.useMemo(() => new Set(overlayIndicators.map(i => i.name)), [overlayIndicators]);
  const toggleCombined = (name: string) => {
    if (overlayNames.has(name)) toggleOverlay(name);
    else togglePane(name);
  };

  // Sync timescales between panes using logical ranges for smoother drag at edges
  useEffect(() => {
    const top = chartRef.current;
    const bottom = paneChartRef.current;
    if (!top || !bottom) return;
    let syncing = false;

    const syncBottomToTop = () => {
      if (syncing) return;
      const lr = top.timeScale().getVisibleLogicalRange();
      if (!lr) return;
      syncing = true;
      try {
        bottom.timeScale().setVisibleLogicalRange(lr as any);
      } finally {
        syncing = false;
      }
    };
    const syncTopToBottom = () => {
      if (syncing) return;
      const lr = bottom.timeScale().getVisibleLogicalRange();
      if (!lr) return;
      syncing = true;
      try {
        top.timeScale().setVisibleLogicalRange(lr as any);
      } finally {
        syncing = false;
      }
    };

    top.timeScale().subscribeVisibleLogicalRangeChange(syncBottomToTop);
    bottom.timeScale().subscribeVisibleLogicalRangeChange(syncTopToBottom);
    return () => {
      try {
        top.timeScale().unsubscribeVisibleLogicalRangeChange(syncBottomToTop);
      } catch (error) {
        if (isDevEnv) console.warn('TradingViewChart: failed to unsubscribe top range sync', error);
      }
      try {
        bottom.timeScale().unsubscribeVisibleLogicalRangeChange(syncTopToBottom);
      } catch (error) {
        if (isDevEnv) console.warn('TradingViewChart: failed to unsubscribe bottom range sync', error);
      }
    };
  }, [ready, paneReady, chartRef, paneChartRef]);

  // Re-apply size/options when fullscreen toggles
  useEffect(() => {
    if (!chartRef.current || !chartContainerRef.current) return;
    chartRef.current.applyOptions({
      ...getChartOptions(theme, timeZone),
      width: chartContainerRef.current.clientWidth,
      height: isFullscreen ? window.innerHeight - 100 : height,
    });
  }, [isFullscreen, height, theme, timeZone, chartRef]);

  // Update candlestick data
  useEffect(() => {
    if (!ready || !candleSeriesRef.current || !candleData.length) return;

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
  }, [candleData, autoFit, ready, candleSeriesRef, chartRef]);

  // Indicators handled in useIndicators; markers handled in useSeriesMarkers

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

  // toggleIndicator provided by useIndicators hook

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

        <ChartControls
          show={showControls}
          indicators={allIndicators.map(i => ({ name: i.name, color: i.color }))}
          visible={visibleCombined}
          onToggleIndicator={toggleCombined}
          onZoomIn={handleZoomIn}
          onZoomOut={handleZoomOut}
          onReset={handleReset}
          onDownload={handleDownload}
          onFullscreen={handleFullscreen}
          isFullscreen={isFullscreen}
        />
      </div>

      {/* Main price pane */}
      <div 
        ref={chartContainerRef}
        className="w-full"
        style={{ height: isFullscreen ? window.innerHeight - 100 : height }}
      />

      {/* Indicator pane (oscillators) */}
      {separateIndicators.length > 0 && (
        <div 
          ref={paneContainerRef}
          className="w-full border-t border-gray-700"
          style={{ height: isFullscreen ? Math.floor((window.innerHeight - 100) * 0.28) : paneHeight }}
        />
      )}

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
