import { afterEach, describe, expect, it, vi } from 'vitest';

import * as chartOptions from '../chartOptions';

const { formatTimeInZone, getChartOptions, getCandlestickOptions } = chartOptions;

describe('formatTimeInZone', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('formats unix timestamps in UTC by default', () => {
    const timestamp = Math.floor(Date.UTC(2023, 9, 5, 12, 34, 0) / 1000);
    const formatted = formatTimeInZone(timestamp);

    expect(formatted).toContain('2023');
    expect(formatted.toLowerCase()).toContain('oct');
    expect(formatted).toMatch(/05/);
    expect(formatted).toMatch(/12/);
    expect(formatted).toMatch(/34/);
  });

  it('formats business date objects', () => {
    const formatted = formatTimeInZone({ year: 2022, month: 1, day: 2 } as any);
    expect(formatted).toContain('2022');
    expect(formatted.toLowerCase()).toContain('jan');
    expect(formatted).toMatch(/02/);
  });

  it('falls back to ISO string when Intl fails', () => {
    const timestamp = Math.floor(Date.UTC(2024, 0, 1, 0, 0, 0) / 1000);
    expect(formatTimeInZone(timestamp, 'Invalid/Zone')).toBe(
      new Date(timestamp * 1000).toISOString()
    );
  });
});

describe('getChartOptions', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns dark theme layout defaults', () => {
    const options = getChartOptions('dark');
    expect(options.layout?.background?.color).toBe('#0a0e16');
    expect(options.layout?.textColor).toBe('#d1d5db');
    expect(options.rightPriceScale?.borderColor).toBe('#374151');
    expect(options.timeScale?.rightBarStaysOnScroll).toBe(false);
    expect(options.handleScroll?.mouseWheel).toBe(true);
  });

  it('returns light theme grid and crosshair styles', () => {
    const options = getChartOptions('light');
    expect(options.grid?.vertLines?.color).toBe('#e5e7eb');
    expect(options.grid?.horzLines?.color).toBe('#e5e7eb');
    expect(options.crosshair?.vertLine?.style).toBe(3);
    expect(options.crosshair?.horzLine?.width).toBe(1);
  });

  it('formats prices with 4 decimals under 1 and 2 decimals otherwise', () => {
    const { localization } = getChartOptions('light');
    const priceFormatter = localization?.priceFormatter as (value: number) => string;
    expect(priceFormatter(0.001)).toBe('0.0010');
    expect(priceFormatter(-0.25)).toBe('-0.2500');
    expect(priceFormatter(1)).toBe('1.00');
    expect(priceFormatter(1234.567)).toBe('1234.57');
  });

  it('delegates timeFormatter to formatTimeInZone', () => {
    const timestamp = Math.floor(Date.UTC(2023, 0, 1, 0, 0, 0) / 1000);
    const zone = 'Asia/Kolkata';
    const expected = formatTimeInZone(timestamp, zone);
    const options = getChartOptions('dark', zone);
    const formatted = options.localization?.timeFormatter?.(timestamp as never);
    expect(formatted).toBe(expected);
  });

  it('tickMarkFormatter falls back to raw value on Intl failure', () => {
    const timestamp = Math.floor(Date.UTC(2023, 9, 5, 12, 0, 0) / 1000);
    const good = getChartOptions('light', 'UTC').timeScale?.tickMarkFormatter?.(timestamp as never);
    expect(good).toMatch(/\d{2}/);

    const bad = getChartOptions('light', 'Invalid/Zone').timeScale?.tickMarkFormatter?.(timestamp as never);
    expect(bad).toBe(String(timestamp));
  });
});

describe('getCandlestickOptions', () => {
  it('returns immutable candlestick styling', () => {
    const options = getCandlestickOptions();
    expect(options).toMatchObject({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      priceLineVisible: true,
      lastValueVisible: true,
    });

    (options as any).upColor = 'changed';
    expect(getCandlestickOptions().upColor).toBe('#26a69a');
  });
});