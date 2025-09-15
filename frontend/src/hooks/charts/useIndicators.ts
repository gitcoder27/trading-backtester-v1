import { useEffect, useRef, useState, useCallback } from 'react';
import type { IChartApi, ISeriesApi } from 'lightweight-charts';
import { LineSeries } from 'lightweight-charts';
import type { IndicatorLine } from '../../types/chart';

export function useIndicators(
  chartRef: React.RefObject<IChartApi | null>,
  indicators: IndicatorLine[],
  enabled: boolean = true
) {
  // Track which chart created the series to remove safely even if chartRef changes
  const seriesMapRef = useRef<Map<string, { chart: IChartApi; series: ISeriesApi<'Line'> }>>(new Map());
  const [visible, setVisible] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!enabled) return;
    const chart = chartRef.current;
    if (!chart) return;

    // Remove old
    seriesMapRef.current.forEach(({ chart: owner, series }) => {
      try { owner.removeSeries(series); } catch {}
    });
    seriesMapRef.current.clear();
    setVisible(new Set());

    // Add new
    indicators.forEach((ind) => {
      try {
        const s = chart.addSeries(LineSeries, {
          color: ind.color,
          lineWidth: ind.lineWidth ?? 2,
          priceLineVisible: false,
          lastValueVisible: true,
          crosshairMarkerVisible: true,
          title: ind.name,
        });
        s.setData(ind.data);
        if (ind.visible === false) s.applyOptions({ visible: false });
        else setVisible((prev) => new Set(prev).add(ind.name));
        seriesMapRef.current.set(ind.name, { chart, series: s });
      } catch {}
    });
  }, [enabled, chartRef, JSON.stringify(indicators)]);

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
