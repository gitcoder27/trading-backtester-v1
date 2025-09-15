import { useEffect } from 'react';
import type { ISeriesApi, SeriesMarker, UTCTimestamp } from 'lightweight-charts';

export function useSeriesMarkers(
  seriesRef: React.RefObject<ISeriesApi<'Candlestick'> | null>,
  markers: SeriesMarker<UTCTimestamp>[],
  enabled: boolean = true
) {
  useEffect(() => {
    if (!enabled) return;
    const series = seriesRef.current as any;
    if (!series || typeof series.setMarkers !== 'function') return;
    try {
      series.setMarkers(markers || []);
    } catch {}
  }, [enabled, seriesRef, JSON.stringify(markers)]);
}
