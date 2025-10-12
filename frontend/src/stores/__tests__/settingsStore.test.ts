import { describe, it, expect, beforeEach } from 'vitest';
import { useSettingsStore } from '../../stores/settingsStore';

describe('settingsStore', () => {
  beforeEach(() => {
    // Reset to defaults
    useSettingsStore.getState().resetToDefaults();
  });

  it('updates preferences shallowly and deeply', () => {
    useSettingsStore.getState().updatePreferences({ default_commission: 0.002 });
    expect(useSettingsStore.getState().default_commission).toBe(0.002);

    useSettingsStore.getState().updatePreferences({ default_lot_size: 5 });
    expect(useSettingsStore.getState().default_lot_size).toBe(5);

    useSettingsStore.getState().updatePreferences({ default_daily_profit_target: 45 });
    expect(useSettingsStore.getState().default_daily_profit_target).toBe(45);

    useSettingsStore.getState().updatePreferences({ default_direction_filter: ['long'] });
    expect(useSettingsStore.getState().default_direction_filter).toEqual(['long']);

    useSettingsStore.getState().updatePreferences({ default_weekdays: [1, 3] });
    expect(useSettingsStore.getState().default_weekdays).toEqual([1, 3]);

    useSettingsStore.getState().updatePreferences({ chart_preferences: { show_trades: false } });
    expect(useSettingsStore.getState().chart_preferences.show_trades).toBe(false);
  });

  it('resets to defaults', () => {
    useSettingsStore.getState().updatePreferences({ default_initial_capital: 123 });
    useSettingsStore.getState().updatePreferences({ default_lot_size: 8 });
    useSettingsStore.getState().updatePreferences({ default_direction_filter: ['short'] });
    useSettingsStore.getState().resetToDefaults();
    expect(useSettingsStore.getState().default_initial_capital).toBe(100000);
    expect(useSettingsStore.getState().default_lot_size).toBe(1);
    expect(useSettingsStore.getState().default_direction_filter).toEqual(['long', 'short']);
  });
});

