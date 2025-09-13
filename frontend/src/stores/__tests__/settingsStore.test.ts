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

    useSettingsStore.getState().updatePreferences({ chart_preferences: { show_trades: false } });
    expect(useSettingsStore.getState().chart_preferences.show_trades).toBe(false);
  });

  it('resets to defaults', () => {
    useSettingsStore.getState().updatePreferences({ default_initial_capital: 123 });
    useSettingsStore.getState().resetToDefaults();
    expect(useSettingsStore.getState().default_initial_capital).toBe(100000);
  });
});

