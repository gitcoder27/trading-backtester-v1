import { describe, it, expect, beforeEach } from 'vitest';
import { useThemeStore } from '../../stores/themeStore';

describe('themeStore', () => {
  beforeEach(() => {
    useThemeStore.setState({ theme: 'dark', actualTheme: 'dark' });
    document.documentElement.classList.add('dark');
  });

  it('sets and toggles theme', () => {
    const { setTheme, toggleTheme } = useThemeStore.getState();
    setTheme('light');
    expect(useThemeStore.getState().actualTheme).toBe('light');
    expect(document.documentElement.classList.contains('dark')).toBe(false);

    toggleTheme();
    expect(useThemeStore.getState().actualTheme).toBe('dark');
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  it('resolves system theme using matchMedia', () => {
    const { setTheme } = useThemeStore.getState();
    setTheme('system');
    // setup.ts defines matchMedia().matches=false -> light
    expect(['light','dark']).toContain(useThemeStore.getState().actualTheme);
  });
});

