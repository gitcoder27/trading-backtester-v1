import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  shadow?: 'none' | 'sm' | 'md' | 'lg';
}

const Card: React.FC<CardProps> = ({
  children,
  className = '',
  padding = 'md',
  shadow = 'md',
}) => {
  const paddingClasses = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  const shadowClasses = {
    none: '',
    sm: 'shadow-sm',
    md: 'shadow-soft',
    lg: 'shadow-soft-lg',
  };

  return (
    <div
      className={`bg-white dark:bg-gray-900/95 rounded-xl border border-gray-200 dark:border-gray-600 shadow-md dark:shadow-xl ${paddingClasses[padding]} ${shadowClasses[shadow]} ${className}`}
    >
      {children}
    </div>
  );
};

export default Card;
