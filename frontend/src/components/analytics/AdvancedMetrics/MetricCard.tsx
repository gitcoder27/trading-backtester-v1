import React from 'react';
import type { MetricCardProps } from './types';

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  color = 'text-gray-600 dark:text-gray-400',
  bgColor = 'bg-gray-100 dark:bg-gray-800/50',
  format = 'number'
}) => {
  const formatValue = (val: number): string => {
    switch (format) {
      case 'percentage':
        return `${val.toFixed(2)}%`;
      case 'currency':
        return `₹${val.toFixed(2)}`;
      case 'ratio':
        return val.toFixed(3);
      case 'number':
      default:
        return Number.isInteger(val) ? val.toString() : val.toFixed(2);
    }
  };

  return (
    <div className="flex items-start space-x-3">
      <div className={`p-2 rounded-lg ${bgColor}`}>
        <Icon className={`h-5 w-5 ${color}`} />
      </div>
      <div>
        <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{title}</p>
        <p className="text-lg font-bold text-gray-900 dark:text-gray-100">{formatValue(value)}</p>
        {subtitle && (
          <p className="text-xs text-gray-500 dark:text-gray-400">{subtitle}</p>
        )}
      </div>
    </div>
  );
};

export default MetricCard;
