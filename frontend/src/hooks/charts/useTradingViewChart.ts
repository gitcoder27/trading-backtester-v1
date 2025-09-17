import { useEffect, useRef, useState } from 'react';
import { createChart, CandlestickSeries } from 'lightweight-charts';
import type { IChartApi, ISeriesApi } from 'lightweight-charts';
import { getChartOptions, getCandlestickOptions } from '../../utils/chartOptions';

export function useTradingViewChart(
  containerRef: React.RefObject<HTMLDivElement>,
  params: { height: number; theme: 'light' | 'dark'; timeZone?: string; isFullscreen?: boolean; enabled?: boolean; withCandles?: boolean }
) {
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!params.enabled) return;
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      ...getChartOptions(params.theme, params.timeZone),
      width: containerRef.current.clientWidth,
      height: params.height,
    });
    chartRef.current = chart;

    if (params.withCandles !== false) {
      const candleSeries = chart.addSeries(CandlestickSeries, getCandlestickOptions());
      candleSeriesRef.current = candleSeries;
    }
    setReady(true);

    const handleResize = () => {
      if (!containerRef.current || !chart) return;
      chart.applyOptions({
        width: containerRef.current.clientWidth,
        height: params.isFullscreen ? window.innerHeight - 100 : params.height,
      });
    };

    const resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
      candleSeriesRef.current = null;
      setReady(false);
    };
  }, [containerRef, params.height, params.theme, params.timeZone, params.isFullscreen, params.enabled, params.withCandles]);

  return { chartRef, candleSeriesRef, ready } as const;
}
