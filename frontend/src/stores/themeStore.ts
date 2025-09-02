import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type Theme = 'light' | 'dark' | 'system';

interface ThemeState {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
  actualTheme: 'light' | 'dark'; // Resolved theme (system -> light/dark)
}

// Helper to get system theme
const getSystemTheme = (): 'light' | 'dark' => {
  if (typeof window === 'undefined') return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
};

// Helper to resolve theme
const resolveTheme = (theme: Theme): 'light' | 'dark' => {
  if (theme === 'system') {
    return getSystemTheme();
  }
  return theme;
};

// Helper to apply theme to document
const applyTheme = (theme: 'light' | 'dark') => {
  if (typeof window === 'undefined') return;
  
  const root = window.document.documentElement;
  
  if (theme === 'dark') {
    root.classList.add('dark');
  } else {
    root.classList.remove('dark');
  }
};

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: 'dark', // Always default to dark theme
      actualTheme: 'dark', // Always default to dark theme
      
      setTheme: (theme: Theme) => {
        const actualTheme = resolveTheme(theme);
        applyTheme(actualTheme);
        set({ theme, actualTheme });
      },
      
      toggleTheme: () => {
        const { actualTheme } = get();
        const newTheme = actualTheme === 'light' ? 'dark' : 'light';
        get().setTheme(newTheme);
      }
    }),
    {
      name: 'theme-storage',
      // Force dark mode on every app load/refresh
      onRehydrateStorage: () => (state) => {
        // Always force dark mode on app initialization, regardless of stored preference
        const forcedDarkTheme = 'dark';
        applyTheme(forcedDarkTheme);
        if (state) {
          state.theme = forcedDarkTheme;
          state.actualTheme = forcedDarkTheme;
        }
        return state;
      }
    }
  )
);

// Listen for system theme changes
if (typeof window !== 'undefined') {
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
  
  mediaQuery.addEventListener('change', (e) => {
    const { theme } = useThemeStore.getState();
    if (theme === 'system') {
      const actualTheme = e.matches ? 'dark' : 'light';
      applyTheme(actualTheme);
      useThemeStore.setState({ actualTheme });
    }
  });
}
