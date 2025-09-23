import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { UserPreferences } from '../types';

type PreferencesUpdate = Partial<Omit<UserPreferences, 'chart_preferences' | 'table_preferences'>> & {
  chart_preferences?: Partial<UserPreferences['chart_preferences']>;
  table_preferences?: Partial<UserPreferences['table_preferences']>;
};

interface SettingsState extends UserPreferences {
  // Actions
  updatePreferences: (preferences: PreferencesUpdate) => void;
  resetToDefaults: () => void;
}

const defaultPreferences: UserPreferences = {
  theme: 'light',
  default_commission: 0.001,
  default_slippage: 0.0005,
  default_initial_capital: 100000,
  chart_preferences: {
    show_trades: true,
    show_signals: true,
    chart_type: 'candlestick',
  },
  table_preferences: {
    page_size: 50,
    auto_refresh: false,
    refresh_interval: 30,
  },
};

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      ...defaultPreferences,

      updatePreferences: (preferences) =>
        set((state) => ({
          ...state,
          ...preferences,
          chart_preferences: {
            ...state.chart_preferences,
            ...preferences.chart_preferences,
          },
          table_preferences: {
            ...state.table_preferences,
            ...preferences.table_preferences,
          },
        })),

      resetToDefaults: () => set(defaultPreferences),
    }),
    {
      name: 'settings-store',
    }
  )
);
