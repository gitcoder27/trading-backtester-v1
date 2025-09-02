import { useState, useEffect } from 'react';

export const useTheme = () => {
  const [isDark, setIsDark] = useState<boolean>(() => {
    // Always default to dark mode - ignore localStorage and system preferences
    return true;
  });

  useEffect(() => {
    const root = window.document.documentElement;
    if (isDark) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    
    // Store preference but always revert to dark on reload
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
  }, [isDark]);

  // Remove system theme listener - we want dark mode always as default
  useEffect(() => {
    // Force dark mode on component mount
    setIsDark(true);
  }, []);

  const toggleTheme = () => setIsDark(!isDark);

  return { isDark, toggleTheme };
};
