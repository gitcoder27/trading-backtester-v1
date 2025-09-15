import { ColorType } from 'lightweight-charts';
import type { ChartOptions, DeepPartial, Time } from 'lightweight-charts';

export type TimeFormatter = (time: Time) => string;

export function formatTimeInZone(time: Time, timeZone?: string): string {
  try {
    const date = typeof time === 'number'
      ? new Date((time as number) * 1000)
      : (time && typeof time === 'object' && 'year' in time && 'month' in time && 'day' in time)
      ? new Date(Date.UTC((time as any).year, (time as any).month - 1, (time as any).day))
      : new Date();

    return new Intl.DateTimeFormat('en-IN', {
      timeZone: timeZone || 'UTC',
      year: 'numeric', month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit'
    }).format(date);
  } catch {
    const date = typeof time === 'number' ? new Date((time as number) * 1000) : new Date();
    return date.toISOString();
  }
}

export function getChartOptions(theme: 'light' | 'dark', timeZone?: string): DeepPartial<ChartOptions> {
  return {
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
      timeFormatter: (t) => formatTimeInZone(t, timeZone),
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
      mode: 1,
      vertLine: {
        color: theme === 'dark' ? '#6b7280' : '#9ca3af',
        width: 1,
        style: 3,
        visible: true,
        labelVisible: true,
      },
      horzLine: {
        color: theme === 'dark' ? '#6b7280' : '#9ca3af',
        width: 1,
        style: 3,
        visible: true,
        labelVisible: true,
      },
    },
    rightPriceScale: {
      borderColor: theme === 'dark' ? '#374151' : '#d1d5db',
      visible: true,
      borderVisible: true,
      scaleMargins: { top: 0.1, bottom: 0.1 },
    },
    timeScale: {
      borderColor: theme === 'dark' ? '#374151' : '#d1d5db',
      borderVisible: true,
      lockVisibleTimeRangeOnResize: true,
      // Make panning feel natural for historical analysis (not sticky to last bar)
      rightBarStaysOnScroll: false,
      shiftVisibleRangeOnNewBar: false,
      // Add a little breathing room on the right edge and keep bars readable
      rightOffset: 3,
      minBarSpacing: 1,
      timeVisible: true,
      secondsVisible: false,
      tickMarkFormatter: (time: number) => {
        try {
          const d = new Date(time * 1000);
          return new Intl.DateTimeFormat('en-IN', {
            timeZone: timeZone || 'UTC',
            hour: '2-digit', minute: '2-digit'
          }).format(d);
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
  };
}

export function getCandlestickOptions() {
  return {
    upColor: '#26a69a',
    downColor: '#ef5350',
    borderVisible: false,
    wickUpColor: '#26a69a',
    wickDownColor: '#ef5350',
    priceLineVisible: true,
    lastValueVisible: true,
  } as const;
}
