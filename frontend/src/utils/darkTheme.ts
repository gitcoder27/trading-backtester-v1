/**
 * Dark-First Theme Utilities
 * 
 * This file provides utilities and constants for consistent dark theme implementation
 * across the entire application. All components should use these utilities to ensure
 * proper dark theme support.
 */

// ========================
// DARK THEME COLOR PALETTE
// ========================

export const darkTheme = {
  // Background Colors
  bg: {
    primary: 'bg-slate-900',       // Main app background
    secondary: 'bg-slate-800',     // Card backgrounds
    tertiary: 'bg-slate-700',      // Elevated elements
    accent: 'bg-slate-600',        // Hover states
    muted: 'bg-slate-800/50',      // Subtle backgrounds
  },
  
  // Text Colors
  text: {
    primary: 'text-slate-50',      // Main text
    secondary: 'text-slate-200',   // Secondary text
    tertiary: 'text-slate-300',    // Tertiary text
    muted: 'text-slate-400',       // Muted text
    disabled: 'text-slate-500',    // Disabled text
  },
  
  // Border Colors
  border: {
    primary: 'border-slate-700',   // Main borders
    secondary: 'border-slate-600', // Interactive borders
    muted: 'border-slate-800',     // Subtle borders
  },
  
  // Ring/Focus Colors
  ring: {
    primary: 'ring-primary-500/50 ring-offset-slate-900',
    secondary: 'ring-slate-400/50 ring-offset-slate-900',
  }
} as const;

// ========================
// COMPONENT CLASS BUILDERS
// ========================

/**
 * Builds dark-first class names for card components
 */
export const cardClasses = {
  base: `${darkTheme.bg.secondary} ${darkTheme.border.primary} border rounded-xl shadow-lg`,
  elevated: `${darkTheme.bg.secondary} ${darkTheme.border.primary} border rounded-xl shadow-xl hover:shadow-2xl transition-shadow`,
  muted: `${darkTheme.bg.muted} ${darkTheme.border.muted} border rounded-lg`,
  interactive: `${darkTheme.bg.secondary} ${darkTheme.border.primary} border rounded-xl shadow-lg hover:shadow-xl hover:${darkTheme.border.secondary} transition-all duration-200 cursor-pointer`,
};

/**
 * Builds dark-first class names for text elements
 */
export const textClasses = {
  heading: `${darkTheme.text.primary} font-bold`,
  subheading: `${darkTheme.text.secondary} font-semibold`,
  body: `${darkTheme.text.secondary}`,
  caption: `${darkTheme.text.muted}`,
  label: `${darkTheme.text.tertiary} font-medium`,
  error: 'text-red-400',
  success: 'text-green-400',
  warning: 'text-yellow-400',
  info: 'text-blue-400',
};

/**
 * Builds dark-first class names for button variants
 */
export const buttonClasses = {
  primary: `bg-primary-600 hover:bg-primary-700 active:bg-primary-800 text-white border-transparent shadow-sm ${darkTheme.ring.primary}`,
  secondary: `${darkTheme.bg.tertiary} hover:${darkTheme.bg.accent} active:bg-slate-500 ${darkTheme.text.primary} ${darkTheme.border.primary} border`,
  outline: `bg-transparent hover:${darkTheme.bg.muted} active:${darkTheme.bg.tertiary} ${darkTheme.text.primary} ${darkTheme.border.primary} border`,
  ghost: `bg-transparent hover:${darkTheme.bg.muted} active:${darkTheme.bg.tertiary} ${darkTheme.text.primary}`,
  danger: 'bg-red-600 hover:bg-red-700 active:bg-red-800 text-white border-transparent shadow-sm',
  success: 'bg-green-600 hover:bg-green-700 active:bg-green-800 text-white border-transparent shadow-sm',
};

/**
 * Builds dark-first class names for input elements
 */
export const inputClasses = {
  base: `${darkTheme.bg.tertiary} ${darkTheme.border.primary} border rounded-lg px-3 py-2 ${darkTheme.text.primary} placeholder:${darkTheme.text.muted} focus:${darkTheme.border.secondary} focus:ring-1 focus:ring-primary-500/50 focus:ring-offset-0 transition-colors`,
  error: `${darkTheme.bg.tertiary} border-red-500 text-red-100 placeholder:text-red-300 focus:border-red-400 focus:ring-red-500/50`,
  success: `${darkTheme.bg.tertiary} border-green-500 text-green-100 placeholder:text-green-300 focus:border-green-400 focus:ring-green-500/50`,
};

/**
 * Builds dark-first class names for modal/overlay elements
 */
export const overlayClasses = {
  backdrop: 'bg-black/50 backdrop-blur-sm',
  modal: `${darkTheme.bg.secondary} ${darkTheme.border.primary} border rounded-xl shadow-2xl`,
  dropdown: `${darkTheme.bg.secondary} ${darkTheme.border.primary} border rounded-lg shadow-xl`,
};

// ========================
// UTILITY FUNCTIONS
// ========================

/**
 * Combines dark theme classes with custom classes
 */
export function combineClasses(...classes: (string | undefined | false)[]): string {
  return classes.filter(Boolean).join(' ');
}

/**
 * Gets the appropriate text color based on background
 */
export function getContrastText(isDark = true): string {
  return isDark ? darkTheme.text.primary : 'text-gray-900';
}

/**
 * Gets status-specific colors for badges and indicators
 */
export function getStatusColors(status: 'success' | 'error' | 'warning' | 'info' | 'pending') {
  const statusMap = {
    success: {
      bg: 'bg-green-900/50',
      text: 'text-green-400',
      border: 'border-green-800',
    },
    error: {
      bg: 'bg-red-900/50', 
      text: 'text-red-400',
      border: 'border-red-800',
    },
    warning: {
      bg: 'bg-yellow-900/50',
      text: 'text-yellow-400',
      border: 'border-yellow-800',
    },
    info: {
      bg: 'bg-blue-900/50',
      text: 'text-blue-400', 
      border: 'border-blue-800',
    },
    pending: {
      bg: 'bg-gray-900/50',
      text: 'text-gray-400',
      border: 'border-gray-800',
    },
  };
  
  return statusMap[status];
}

/**
 * Performance-based color utilities
 */
export function getPerformanceColor(value: number, isInverted = false) {
  const isPositive = isInverted ? value < 0 : value > 0;
  return isPositive 
    ? 'text-green-400' 
    : 'text-red-400';
}

/**
 * Chart/data visualization colors optimized for dark theme
 */
export const chartColors = {
  primary: '#3b82f6',     // blue-500
  secondary: '#10b981',   // green-500  
  tertiary: '#f59e0b',    // yellow-500
  quaternary: '#ef4444',  // red-500
  accent: '#8b5cf6',      // purple-500
  muted: '#6b7280',       // gray-500
  
  // Gradient sets for complex charts
  gradients: {
    profit: ['#10b981', '#059669'],      // green gradient
    loss: ['#ef4444', '#dc2626'],        // red gradient
    neutral: ['#6b7280', '#4b5563'],     // gray gradient
    primary: ['#3b82f6', '#2563eb'],     // blue gradient
  }
};

// ========================
// LAYOUT UTILITIES
// ========================

/**
 * Standard spacing scales optimized for trading interfaces
 */
export const spacing = {
  xs: 'p-2',
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
  xl: 'p-12',
  
  // Component-specific spacing
  card: 'p-6',
  modal: 'p-8',
  sidebar: 'p-4',
  header: 'px-6 py-4',
};

/**
 * Standard border radius for consistent UI
 */
export const borderRadius = {
  sm: 'rounded-md',
  md: 'rounded-lg', 
  lg: 'rounded-xl',
  xl: 'rounded-2xl',
  full: 'rounded-full',
};

/**
 * Shadow scales optimized for dark theme
 */
export const shadows = {
  sm: 'shadow-sm',
  md: 'shadow-lg', 
  lg: 'shadow-xl',
  xl: 'shadow-2xl',
  
  // Colored shadows for emphasis
  primary: 'shadow-lg shadow-primary-500/25',
  success: 'shadow-lg shadow-green-500/25',
  danger: 'shadow-lg shadow-red-500/25',
};

// ========================
// ANIMATION UTILITIES
// ========================

/**
 * Standard transitions for smooth interactions
 */
export const transitions = {
  fast: 'transition-all duration-150',
  normal: 'transition-all duration-200',
  slow: 'transition-all duration-300',
  
  // Property-specific transitions
  colors: 'transition-colors duration-200',
  transform: 'transition-transform duration-200',
  opacity: 'transition-opacity duration-200',
  shadow: 'transition-shadow duration-200',
};

// ========================
// RESPONSIVE UTILITIES
// ========================

/**
 * Responsive grid patterns for trading interfaces
 */
export const grids = {
  auto: 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6',
  cards: 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6',
  metrics: 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4',
  sidebar: 'grid grid-cols-1 lg:grid-cols-4 gap-6',
};

/**
 * Standard breakpoint helpers
 */
export const breakpoints = {
  mobile: 'block md:hidden',
  tablet: 'hidden md:block lg:hidden', 
  desktop: 'hidden lg:block',
  responsive: 'block',
};

// ========================
// EXPORTS
// ========================

/**
 * Main theme object for easy access
 */
export const theme = {
  colors: darkTheme,
  components: {
    card: cardClasses,
    text: textClasses,
    button: buttonClasses,
    input: inputClasses,
    overlay: overlayClasses,
  },
  layout: {
    spacing,
    borderRadius,
    shadows,
    grids,
    breakpoints,
  },
  animation: transitions,
  chart: chartColors,
  utils: {
    combineClasses,
    getContrastText,
    getStatusColors,
    getPerformanceColor,
  },
} as const;

export default theme;
