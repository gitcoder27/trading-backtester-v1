import { describe, it, expect } from 'vitest';
import theme, { combineClasses, getContrastText, getStatusColors, getPerformanceColor, chartColors, spacing, borderRadius, shadows } from '../darkTheme';

describe('darkTheme utils', () => {
  it('combines classes', () => {
    const shouldInclude = false;
    expect(combineClasses('a', shouldInclude ? 'b' : undefined, 'c')).toBe('a c');
  });

  it('returns contrast text based on mode', () => {
    expect(getContrastText(true)).toMatch(/text-slate/);
    expect(getContrastText(false)).toBe('text-gray-900');
  });

  it('returns status colors', () => {
    expect(getStatusColors('success').text).toBe('text-green-400');
    expect(getStatusColors('error').bg).toContain('red');
  });

  it('gets performance color', () => {
    expect(getPerformanceColor(1)).toBe('text-green-400');
    expect(getPerformanceColor(-1)).toBe('text-red-400');
    expect(getPerformanceColor(-1, true)).toBe('text-green-400');
  });

  it('exposes theme and tokens', () => {
    expect(theme.colors).toBeDefined();
    expect(chartColors.primary).toBeDefined();
    expect(spacing.md).toBe('p-6');
    expect(borderRadius.lg).toBe('rounded-xl');
    expect(shadows.sm).toBe('shadow-sm');
  });
});
