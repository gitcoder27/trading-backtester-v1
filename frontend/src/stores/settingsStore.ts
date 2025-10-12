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
  default_lot_size: 1,
  default_fee_per_trade: 0,
  default_daily_profit_target: 30,
  default_option_delta: 0.5,
  default_option_price_per_unit: 1,
  default_intraday_mode: true,
  default_session_close_time: '15:15',
  default_direction_filter: ['long', 'short'],
  default_apply_time_filter: false,
  default_start_hour: 9,
  default_end_hour: 15,
  default_apply_weekday_filter: false,
  default_weekdays: [0, 1, 2, 3, 4],
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
      chart_preferences: { ...defaultPreferences.chart_preferences },
      default_direction_filter: [...defaultPreferences.default_direction_filter],
      default_weekdays: [...defaultPreferences.default_weekdays],
      table_preferences: { ...defaultPreferences.table_preferences },

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
          default_direction_filter: preferences.default_direction_filter
            ? [...preferences.default_direction_filter]
            : state.default_direction_filter,
          default_weekdays: preferences.default_weekdays
            ? [...preferences.default_weekdays]
            : state.default_weekdays,
        })),

      resetToDefaults: () =>
        set(() => ({
          ...defaultPreferences,
          chart_preferences: { ...defaultPreferences.chart_preferences },
          default_direction_filter: [...defaultPreferences.default_direction_filter],
          default_weekdays: [...defaultPreferences.default_weekdays],
          table_preferences: { ...defaultPreferences.table_preferences },
        })),
    }),
    {
      name: 'settings-store',
    }
  )
);
