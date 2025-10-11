import { describe, it, expect } from 'vitest';
import { formatDuration, formatTradingSessionsDuration, getReturnColor } from '../formatters';

describe('formatDuration', () => {
  it('returns hours and minutes when duration spans hours', () => {
    const result = formatDuration('2024-01-01T00:00:00Z', '2024-01-01T03:30:00Z');
    expect(result).toBe('3h 30m');
  });

  it('returns minutes when duration is less than an hour', () => {
    const result = formatDuration('2024-01-01T00:00:00Z', '2024-01-01T00:45:00Z');
    expect(result).toBe('45m');
  });
});

describe('formatTradingSessionsDuration', () => {
  it('returns em dash for invalid values', () => {
    expect(formatTradingSessionsDuration(undefined)).toBe('—');
    expect(formatTradingSessionsDuration(null)).toBe('—');
    expect(formatTradingSessionsDuration(-5)).toBe('—');
  });

  it('formats days, months, and years appropriately', () => {
    expect(formatTradingSessionsDuration(21)).toBe('21d');
    expect(formatTradingSessionsDuration(120)).toBe('6mo');
    expect(formatTradingSessionsDuration(252)).toBe('12mo');
    expect(formatTradingSessionsDuration(1260)).toBe('5y');
  });
});

describe('getReturnColor', () => {
  it('returns neutral color for N/A', () => {
    expect(getReturnColor('N/A')).toBe('text-gray-400');
  });

  it('returns positive and negative colors', () => {
    expect(getReturnColor('+2.5%')).toBe('text-green-400');
    expect(getReturnColor('-1.0%')).toBe('text-red-400');
  });
});
