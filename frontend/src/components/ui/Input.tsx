import React, { forwardRef } from 'react';
import type { LucideIcon } from 'lucide-react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helpText?: string;
  icon?: LucideIcon;
  iconPosition?: 'left' | 'right';
  variant?: 'default' | 'error' | 'success';
  fullWidth?: boolean;
}

const Input = forwardRef<HTMLInputElement, InputProps>(({
  label,
  error,
  helpText,
  icon: Icon,
  iconPosition = 'left',
  variant = 'default',
  fullWidth = true,
  className = '',
  id,
  ...props
}, ref) => {
  const inputId = id || Math.random().toString(36).substr(2, 9);
  
  // Determine variant based on error state
  const actualVariant = error ? 'error' : variant;
  
  const variantClasses = {
    default: 'input',
    error: 'input-error',
    success: 'input-success'
  };

  const widthClasses = fullWidth ? 'w-full' : '';

  return (
    <div className={`space-y-1 ${widthClasses}`}>
      {label && (
        <label
          htmlFor={inputId}
          className="form-label"
        >
          {label}
        </label>
      )}
      
      <div className="relative">
        {Icon && iconPosition === 'left' && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Icon className="h-4 w-4 text-gray-400" />
          </div>
        )}
        
        <input
          ref={ref}
          id={inputId}
          className={`
            ${variantClasses[actualVariant]}
            ${Icon && iconPosition === 'left' ? 'pl-10' : ''}
            ${Icon && iconPosition === 'right' ? 'pr-10' : ''}
            ${className}
          `}
          {...props}
        />
        
        {Icon && iconPosition === 'right' && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
            <Icon className="h-4 w-4 text-gray-400" />
          </div>
        )}
      </div>
      
      {error && (
        <p className="form-error">{error}</p>
      )}
      {helpText && !error && (
        <p className="form-help">{helpText}</p>
      )}
    </div>
  );
});

Input.displayName = 'Input';

// Textarea component
interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helpText?: string;
  variant?: 'default' | 'error' | 'success';
  fullWidth?: boolean;
  resize?: 'none' | 'vertical' | 'horizontal' | 'both';
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(({
  label,
  error,
  helpText,
  variant = 'default',
  fullWidth = true,
  resize = 'vertical',
  className = '',
  id,
  ...props
}, ref) => {
  const textareaId = id || Math.random().toString(36).substr(2, 9);
  
  // Determine variant based on error state
  const actualVariant = error ? 'error' : variant;
  
  const variantClasses = {
    default: 'input',
    error: 'input-error',
    success: 'input-success'
  };

  const resizeClasses = {
    none: 'resize-none',
    vertical: 'resize-y',
    horizontal: 'resize-x',
    both: 'resize'
  };

  const widthClasses = fullWidth ? 'w-full' : '';

  return (
    <div className={`space-y-1 ${widthClasses}`}>
      {label && (
        <label
          htmlFor={textareaId}
          className="form-label"
        >
          {label}
        </label>
      )}
      
      <textarea
        ref={ref}
        id={textareaId}
        className={`
          ${variantClasses[actualVariant]}
          ${resizeClasses[resize]}
          ${className}
        `}
        {...props}
      />
      
      {error && (
        <p className="form-error">{error}</p>
      )}
      {helpText && !error && (
        <p className="form-help">{helpText}</p>
      )}
    </div>
  );
});

Textarea.displayName = 'Textarea';

// Select component
interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  helpText?: string;
  variant?: 'default' | 'error' | 'success';
  fullWidth?: boolean;
  placeholder?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(({
  label,
  error,
  helpText,
  variant = 'default',
  fullWidth = true,
  placeholder,
  children,
  className = '',
  id,
  ...props
}, ref) => {
  const selectId = id || Math.random().toString(36).substr(2, 9);
  
  // Determine variant based on error state
  const actualVariant = error ? 'error' : variant;
  
  const variantClasses = {
    default: 'input',
    error: 'input-error',
    success: 'input-success'
  };

  const widthClasses = fullWidth ? 'w-full' : '';

  return (
    <div className={`space-y-1 ${widthClasses}`}>
      {label && (
        <label
          htmlFor={selectId}
          className="form-label"
        >
          {label}
        </label>
      )}
      
      <select
        ref={ref}
        id={selectId}
        className={`
          ${variantClasses[actualVariant]}
          ${className}
        `}
        {...props}
      >
        {placeholder && (
          <option value="" disabled>
            {placeholder}
          </option>
        )}
        {children}
      </select>
      
      {error && (
        <p className="form-error">{error}</p>
      )}
      {helpText && !error && (
        <p className="form-help">{helpText}</p>
      )}
    </div>
  );
});

Select.displayName = 'Select';

export default Input;
