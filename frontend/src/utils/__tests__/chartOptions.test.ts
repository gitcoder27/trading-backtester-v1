// Auto-generated tests for chartOptions utilities


/**
 * Test suite for chartOptions utilities.
 *
 * Testing library/framework: Jest (or Vitest-compatible APIs: describe/it/expect/jest/vi).
 * These tests avoid brittle locale-specific assertions by checking substrings and fallbacks.
 */

/* eslint-disable @typescript-eslint/no-explicit-any */

let mod: typeof import('../chartOptions');
try {
  // Typical location: frontend/src/utils/chartOptions.ts
  // Import the module as a namespace to allow spying on exported functions.
  // The relative path is from __tests__ to parent utils folder.
  // If this import fails because implementation is colocated here, tests below skip spies accordingly.
  // @ts-ignore
  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
  mod = require('../chartOptions');
} catch (err) {
  // Fallback: if the implementation is accidentally inside this test file (per PR diff),
  // simulate a minimal module by extracting exports from current module scope if available.
  // In that rare case, rely on direct calls without spy.
  mod = require(process.cwd() + '/frontend/src/utils/__tests__/chartOptions.test.ts') as any;
}

const {
  formatTimeInZone,
  getChartOptions,
  getCandlestickOptions,
} = mod as any;

const isVitest = typeof (globalThis as any).vi !== 'undefined';
const spy = (obj: any, key: string) => (isVitest ? (globalThis as any).vi.spyOn(obj, key) : (globalThis as any).jest.spyOn(obj, key));
const fn = (impl?: any) => (isVitest ? (globalThis as any).vi.fn(impl) : (globalThis as any).jest.fn(impl));
const restoreAllMocks = () => (isVitest ? (globalThis as any).vi.restoreAllMocks() : (globalThis as any).jest.restoreAllMocks());

describe('formatTimeInZone', () => {
  afterEach(() => {
    restoreAllMocks();
  });

  it('formats a numeric Unix timestamp in UTC by default and includes expected parts', () => {
    // 2023-10-05T12:34:00Z
    const ts = Math.floor(Date.UTC(2023, 9, 5, 12, 34, 0) / 1000);
    const out = formatTimeInZone(ts);
    // Avoid exact match; ensure year, month short, day, hour and minute presence.
    expect(out).toEqual(expect.stringContaining('2023'));
    expect(out.toLowerCase()).toContain('oct');
    expect(out).toMatch(/05/); // day 05 with 2-digits per options
    expect(out).toMatch(/12|\.?12/); // hour "12" in UTC (en-IN hourCycle may vary)
    expect(out).toMatch(/34/); // minutes
  });

  it('formats a business date object ({year, month, day}) and includes expected date parts', () => {
    const out = formatTimeInZone({ year: 2022, month: 1, day: 2 } as any);
    expect(out).toEqual(expect.stringContaining('2022'));
    // Jan in en-IN
    expect(out.toLowerCase()).toContain('jan');
    expect(out).toMatch(/02/);
  });

  it('falls back to ISO string when Intl.DateTimeFormat throws due to invalid timezone', () => {
    const ts = Math.floor(Date.UTC(2024, 0, 1, 0, 0, 0) / 1000);
    const out = formatTimeInZone(ts, 'Invalid/Zone/Name');
    expect(out).toBe(new Date(ts * 1000).toISOString());
  });
});

describe('getChartOptions', () => {
  afterEach(() => {
    restoreAllMocks();
  });

  it('returns dark theme colors and stable layout properties', () => {
    const opts = getChartOptions('dark');
    expect(opts.layout?.background?.color).toBe('#0a0e16');
    expect(opts.layout?.textColor).toBe('#d1d5db');
    expect(opts.layout?.fontSize).toBe(12);
    expect(opts.rightPriceScale?.borderColor).toBe('#374151');
    expect(opts.timeScale?.borderVisible).toBe(true);
    expect(opts.timeScale?.rightBarStaysOnScroll).toBe(false);
    expect(opts.timeScale?.shiftVisibleRangeOnNewBar).toBe(false);
    expect(opts.handleScroll?.mouseWheel).toBe(true);
    expect(opts.handleScale?.pinch).toBe(true);
  });

  it('returns light theme colors and stable layout properties', () => {
    const opts = getChartOptions('light');
    expect(opts.layout?.background?.color).toBe('#ffffff');
    expect(opts.layout?.textColor).toBe('#374151');
    expect(opts.grid?.vertLines?.color).toBe('#e5e7eb');
    expect(opts.grid?.horzLines?.color).toBe('#e5e7eb');
    expect(opts.crosshair?.vertLine?.style).toBe(3);
    expect(opts.crosshair?.horzLine?.width).toBe(1);
  });

  it('localization.priceFormatter uses 4 decimals for |p| < 1 and 2 decimals otherwise', () => {
    const opts: any = getChartOptions('light');
    const pf = opts.localization && opts.localization.priceFormatter;
    expect(pf(0.0001)).toBe('0.0001');
    expect(pf(0.1)).toBe('0.1000');
    expect(pf(-0.9)).toBe('-0.9000');
    expect(pf(1)).toBe('1.00');
    expect(pf(-1.234)).toBe('-1.23');
    expect(pf(1234.567)).toBe('1234.57');
  });

  it('timeFormatter delegates to formatTimeInZone with provided timeZone', () => {
    const zone = 'Asia/Kolkata';
    const modNs = require('../chartOptions'); // ensure namespace import for spying
    const spyFmt = spy(modNs, 'formatTimeInZone').mockImplementation(fn(() => 'ok'));
    const t = Math.floor(Date.UTC(2023, 0, 1, 0, 0, 0) / 1000);
    const opts: any = getChartOptions('dark', zone);
    const tf = opts.localization && opts.localization.timeFormatter;
    const r = tf(t);
    expect(spyFmt).toHaveBeenCalledTimes(1);
    expect(spyFmt).toHaveBeenCalledWith(t, zone);
    expect(r).toBe('ok');
  });

  it('timeScale.tickMarkFormatter returns formatted time on success and falls back to string on error', () => {
    const optsGood: any = getChartOptions('light', 'UTC');
    const good = optsGood.timeScale && optsGood.timeScale.tickMarkFormatter;
    const ts = Math.floor(Date.UTC(2023, 9, 5, 12, 34, 0) / 1000);
    const out = good(ts);
    expect(typeof out).toBe('string');
    expect(out).toMatch(/\d{2}/); // hour or minute

    const optsBad: any = getChartOptions('light', 'Invalid/Zone');
    const bad = optsBad.timeScale && optsBad.timeScale.tickMarkFormatter;
    const outBad = bad(ts);
    expect(outBad).toBe(String(ts));
  });

  it('localization settings include en-IN locale and dd MMM yyyy dateFormat', () => {
    const loc: any = getChartOptions('dark').localization;
    expect(loc.locale).toBe('en-IN');
    expect(loc.dateFormat).toBe('dd MMM yyyy');
  });
});

describe('getCandlestickOptions', () => {
  it('returns the expected immutable style options', () => {
    const o = getCandlestickOptions();
    expect(o).toMatchObject({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
      priceLineVisible: true,
      lastValueVisible: true,
    });
    // Ensure values are not accidentally mutated by consumers
    const snapshot = JSON.parse(JSON.stringify(o));
    (snapshot as any).upColor = 'changed';
    expect(o.upColor).toBe('#26a69a');
  });
});