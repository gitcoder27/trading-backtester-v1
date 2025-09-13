import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeToggle, ThemePicker } from '../ui/ThemeToggle';
import { useThemeStore } from '../../stores/themeStore';

describe('ThemeToggle', () => {
  it('toggles theme in button variant', () => {
    useThemeStore.setState({ theme: 'dark', actualTheme: 'dark' });
    render(<ThemeToggle showLabel variant="button" />);
    const btn = screen.getByRole('button');
    expect(btn).toHaveAccessibleName(/switch to light/i);
    fireEvent.click(btn);
    // actualTheme flipped in store
    expect(useThemeStore.getState().theme).toBe('light');
  });

  it('select dropdown changes theme', () => {
    useThemeStore.setState({ theme: 'dark', actualTheme: 'dark' });
    render(<ThemeToggle variant="dropdown" />);
    const select = screen.getByDisplayValue('Dark') as HTMLSelectElement;
    fireEvent.change(select, { target: { value: 'light' } });
    expect(useThemeStore.getState().theme).toBe('light');
  });
});

describe('ThemePicker', () => {
  it('renders options and updates theme', () => {
    useThemeStore.setState({ theme: 'dark', actualTheme: 'dark' });
    render(<ThemePicker />);
    const lightBtn = screen.getByRole('button', { name: /light/i });
    fireEvent.click(lightBtn);
    expect(useThemeStore.getState().theme).toBe('light');
  });
});

