import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useTheme } from '../useTheme';

describe('useTheme', () => {
  it('defaults to dark and toggles', () => {
    const { result } = renderHook(() => useTheme());
    expect(result.current.isDark).toBe(true);
    act(() => result.current.toggleTheme());
    expect(result.current.isDark).toBe(false);
    act(() => result.current.toggleTheme());
    expect(result.current.isDark).toBe(true);
  });
});

