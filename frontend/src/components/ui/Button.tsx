import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'success' | 'nav' | 'action';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  icon?: LucideIcon;
  iconPosition?: 'left' | 'right';
  loading?: boolean;
  fullWidth?: boolean;
  iconOnly?: boolean;
  children?: React.ReactNode;
}

const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  icon: Icon,
  iconPosition = 'left',
  loading = false,
  fullWidth = false,
  iconOnly = false,
  children,
  className = '',
  disabled,
  ...props
}) => {
  const baseClasses = 'btn';
  const variantClasses = `btn-${variant}`;
  const sizeClasses = `btn-${size}`;
  const widthClasses = fullWidth ? 'w-full' : '';
  const iconOnlyClasses = iconOnly ? 'btn-icon-only' : '';

  const iconSize = {
    xs: 'h-3 w-3',
    sm: 'h-4 w-4', 
    md: 'h-4 w-4',
    lg: 'h-5 w-5',
    xl: 'h-6 w-6'
  }[size];

  const LoadingSpinner = () => (
    <div className={`spinner-${size === 'xs' ? 'sm' : size === 'sm' ? 'sm' : 'md'} ${iconPosition === 'left' ? 'mr-2' : 'ml-2'}`} />
  );

  const ButtonIcon = Icon && !loading ? (
    <Icon className={`${iconSize} ${iconPosition === 'left' && children && !iconOnly ? 'mr-2' : iconPosition === 'right' && children && !iconOnly ? 'ml-2' : ''}`} />
  ) : null;

  // Separate event handlers so we can enhance keyboard accessibility
  const { onClick, onKeyDown, ...rest } = props;

  const handleKeyDown: React.KeyboardEventHandler<HTMLButtonElement> = (e) => {
    // Trigger click on Enter/Space for better a11y in tests/JSDOM
    if ((e.key === 'Enter' || e.key === ' ') && !disabled && !loading) {
      onClick?.(e as unknown as React.MouseEvent<HTMLButtonElement, MouseEvent>);
    }
    onKeyDown?.(e);
  };

  return (
    <button
      className={`${baseClasses} ${variantClasses} ${sizeClasses} ${widthClasses} ${iconOnlyClasses} ${className}`}
      disabled={disabled || loading}
      onKeyDown={handleKeyDown}
      onClick={onClick}
      {...rest}
    >
      {loading && iconPosition === 'left' && <LoadingSpinner />}
      {!loading && iconPosition === 'left' && ButtonIcon}
      {!iconOnly && children}
      {loading && iconPosition === 'right' && <LoadingSpinner />}
      {!loading && iconPosition === 'right' && ButtonIcon}
    </button>
  );
};

export default Button;
