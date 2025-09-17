import { useEffect, useRef } from 'react';
import type { ISeriesApi, ISeriesMarkersPluginApi, SeriesMarker, UTCTimestamp } from 'lightweight-charts';
import { createSeriesMarkers } from 'lightweight-charts';

export function useSeriesMarkers(
  seriesRef: React.RefObject<ISeriesApi<'Candlestick'> | null>,
  markers: SeriesMarker<UTCTimestamp>[],
  enabled: boolean = true
) {
  const markersPluginRef = useRef<ISeriesMarkersPluginApi<UTCTimestamp> | null>(null);

  useEffect(() => {
    if (!enabled) {
      if (markersPluginRef.current) {
        try {
          markersPluginRef.current.setMarkers([]);
          markersPluginRef.current.detach();
        } catch {}
        markersPluginRef.current = null;
      }
      return;
    }

    const series = seriesRef.current;
    if (!series) return;

    try {
      markersPluginRef.current = createSeriesMarkers(series, []);
    } catch {
      markersPluginRef.current = null;
    }

    return () => {
      if (markersPluginRef.current) {
        try {
          markersPluginRef.current.detach();
        } catch {}
        markersPluginRef.current = null;
      }
    };
  }, [enabled, seriesRef]);

  useEffect(() => {
    if (!enabled) return;
    const plugin = markersPluginRef.current;
    if (!plugin) return;
    try {
      plugin.setMarkers(markers || []);
    } catch {}
  }, [enabled, markers]);
}
