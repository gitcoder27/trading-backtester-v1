import React from 'react';
import { Sun, Moon, Monitor } from 'lucide-react';
import { useThemeStore } from '../../stores/themeStore';
import Button from './Button';

interface ThemeToggleProps {
  showLabel?: boolean;
  variant?: 'button' | 'dropdown';
  size?: 'sm' | 'md' | 'lg';
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({
  showLabel = false,
  variant = 'button',
  size = 'md'
}) => {
  const { theme, setTheme, actualTheme } = useThemeStore();

  if (variant === 'button') {
    const Icon = actualTheme === 'dark' ? Sun : Moon;
    
    return (
      <Button
        variant="ghost"
        size={size}
        onClick={() => setTheme(actualTheme === 'dark' ? 'light' : 'dark')}
        icon={Icon}
        aria-label={`Switch to ${actualTheme === 'dark' ? 'light' : 'dark'} mode`}
      >
        {showLabel && (actualTheme === 'dark' ? 'Light' : 'Dark')}
      </Button>
    );
  }

  // Dropdown variant
  return (
    <div className="relative">
      <select
        value={theme}
        onChange={(e) => setTheme(e.target.value as 'light' | 'dark' | 'system')}
        className="input pr-8 appearance-none bg-no-repeat bg-right bg-[length:16px] cursor-pointer"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3e%3c/svg%3e")`
        }}
      >
        <option value="light">Light</option>
        <option value="dark">Dark</option>
        <option value="system">System</option>
      </select>
    </div>
  );
};

// Theme picker with icons
export const ThemePicker: React.FC = () => {
  const { theme, setTheme, actualTheme } = useThemeStore();

  const themes = [
    { value: 'light' as const, label: 'Light', icon: Sun },
    { value: 'dark' as const, label: 'Dark', icon: Moon },
    { value: 'system' as const, label: 'System', icon: Monitor }
  ];

  return (
    <div className="flex space-x-2">
      {themes.map(({ value, label, icon: Icon }) => {
        const isActive = theme === value;
        const isCurrentlyActive = value === 'system' ? true : actualTheme === value;
        
        return (
          <Button
            key={value}
            variant={isActive ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setTheme(value)}
            icon={Icon}
            className={`
              relative
              ${isCurrentlyActive && !isActive ? 'ring-2 ring-primary-200' : ''}
            `}
            aria-label={`Switch to ${label.toLowerCase()} theme`}
          >
            {label}
          </Button>
        );
      })}
    </div>
  );
};

export default ThemeToggle;
