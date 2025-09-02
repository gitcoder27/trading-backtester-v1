import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'info' | 'gray';
  size?: 'sm' | 'md' | 'lg';
  icon?: LucideIcon;
  iconPosition?: 'left' | 'right';
  dot?: boolean;
  className?: string;
}

const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'gray',
  size = 'md',
  icon: Icon,
  iconPosition = 'left',
  dot = false,
  className = ''
}) => {
  const baseClasses = 'badge';
  const variantClasses = `badge-${variant}`;
  
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-0.5 text-xs',
    lg: 'px-3 py-1 text-sm'
  };

  const iconSize = {
    sm: 'h-3 w-3',
    md: 'h-3 w-3',
    lg: 'h-4 w-4'
  }[size];

  const dotSize = {
    sm: 'h-1.5 w-1.5',
    md: 'h-2 w-2',
    lg: 'h-2.5 w-2.5'
  }[size];

  return (
    <span className={`${baseClasses} ${variantClasses} ${sizeClasses[size]} ${className}`}>
      {dot && (
        <span className={`${dotSize} rounded-full bg-current mr-1.5`} />
      )}
      {Icon && iconPosition === 'left' && !dot && (
        <Icon className={`${iconSize} mr-1`} />
      )}
      {children}
      {Icon && iconPosition === 'right' && !dot && (
        <Icon className={`${iconSize} ml-1`} />
      )}
    </span>
  );
};

// Status badges for common use cases
interface StatusBadgeProps {
  status: 'active' | 'inactive' | 'pending' | 'completed' | 'failed' | 'cancelled' | 'running';
  size?: 'sm' | 'md' | 'lg';
  showDot?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = 'md',
  showDot = true
}) => {
  const statusConfig = {
    active: { variant: 'success' as const, label: 'Active' },
    inactive: { variant: 'gray' as const, label: 'Inactive' },
    pending: { variant: 'warning' as const, label: 'Pending' },
    completed: { variant: 'success' as const, label: 'Completed' },
    failed: { variant: 'danger' as const, label: 'Failed' },
    cancelled: { variant: 'gray' as const, label: 'Cancelled' },
    running: { variant: 'primary' as const, label: 'Running' }
  };

  const config = statusConfig[status];

  return (
    <Badge 
      variant={config.variant} 
      size={size}
      dot={showDot}
    >
      {config.label}
    </Badge>
  );
};

// Performance badge for trading metrics
interface PerformanceBadgeProps {
  value: number;
  format?: 'percentage' | 'currency' | 'number';
  size?: 'sm' | 'md' | 'lg';
  showSign?: boolean;
}

export const PerformanceBadge: React.FC<PerformanceBadgeProps> = ({
  value,
  format = 'percentage',
  size = 'md',
  showSign = true
}) => {
  const isPositive = value > 0;
  const isNegative = value < 0;
  
  let variant: 'success' | 'danger' | 'gray' = 'gray';
  if (isPositive) variant = 'success';
  if (isNegative) variant = 'danger';

  const formatValue = (val: number) => {
    const absValue = Math.abs(val);
    const sign = showSign && val !== 0 ? (val > 0 ? '+' : '-') : '';
    
    switch (format) {
      case 'percentage':
        return `${sign}${absValue.toFixed(2)}%`;
      case 'currency':
        return `${sign}$${absValue.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
      case 'number':
        return `${sign}${absValue.toLocaleString()}`;
      default:
        return `${sign}${absValue}`;
    }
  };

  return (
    <Badge variant={variant} size={size}>
      {formatValue(value)}
    </Badge>
  );
};

export default Badge;
