import { useEffect, useRef, useState, useCallback } from 'react';
import type { IChartApi, ISeriesApi, LineWidth } from 'lightweight-charts';
import { LineSeries } from 'lightweight-charts';
import type { IndicatorLine } from '../../types/chart';

const isDevEnv = typeof import.meta !== 'undefined' && Boolean(import.meta.env?.DEV);

export function useIndicators(
  chartRef: React.RefObject<IChartApi | null>,
  indicators: IndicatorLine[],
  enabled: boolean = true
) {
  // Track which chart created the series to remove safely even if chartRef changes
  const seriesMapRef = useRef<Map<string, { chart: IChartApi; series: ISeriesApi<'Line'> }>>(new Map());
  const [visible, setVisible] = useState<Set<string>>(new Set());

  useEffect(() => {
    const chart = chartRef.current;
    if (!enabled || !chart) {
      if (!enabled) {
        seriesMapRef.current.forEach(({ chart: owner, series }) => {
          try {
            owner.removeSeries(series);
          } catch (error) {
            if (isDevEnv) console.warn('useIndicators: failed to remove series during disable', error);
          }
        });
        seriesMapRef.current.clear();
        setVisible(new Set());
      }
      return undefined;
    }

    seriesMapRef.current.forEach(({ chart: owner, series }) => {
      try {
        owner.removeSeries(series);
      } catch (error) {
        if (isDevEnv) console.warn('useIndicators: failed to remove existing series', error);
      }
    });
    seriesMapRef.current.clear();

    const nextVisible = new Set<string>();

    indicators.forEach((ind) => {
      try {
        const series = chart.addSeries(LineSeries, {
          color: ind.color,
          lineWidth: (ind.lineWidth ?? 2) as LineWidth,
          priceLineVisible: false,
          lastValueVisible: true,
          crosshairMarkerVisible: true,
          title: ind.name,
        });
        series.setData(ind.data);
        if (ind.visible === false) {
          series.applyOptions({ visible: false });
        } else {
          nextVisible.add(ind.name);
        }
        seriesMapRef.current.set(ind.name, { chart, series });
      } catch (error) {
        if (isDevEnv) console.warn('useIndicators: failed to add indicator series', error);
      }
    });

    setVisible(nextVisible);

    return () => {
      seriesMapRef.current.forEach(({ chart: owner, series }) => {
        try {
          owner.removeSeries(series);
        } catch (error) {
          if (isDevEnv) console.warn('useIndicators: failed to remove series on cleanup', error);
        }
      });
      seriesMapRef.current.clear();
    };
  }, [enabled, chartRef, indicators]);

  const toggle = useCallback((name: string) => {
    const owner = seriesMapRef.current.get(name);
    if (!owner) return;
    const s = owner.series;
    setVisible((prev) => {
      const next = new Set(prev);
      if (next.has(name)) {
        s.applyOptions({ visible: false });
        next.delete(name);
      } else {
        s.applyOptions({ visible: true });
        next.add(name);
      }
      return next;
    });
  }, []);

  return { visibleIndicators: visible, toggleIndicator: toggle } as const;
}
