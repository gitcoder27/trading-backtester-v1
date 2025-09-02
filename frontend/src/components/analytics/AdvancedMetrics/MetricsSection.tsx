import React from 'react';
import Card from '../../ui/Card';
import Badge from '../../ui/Badge';
import MetricCard from './MetricCard';
import type { MetricsSectionProps } from './types';

const MetricsSection: React.FC<MetricsSectionProps> = ({
  title,
  badgeText,
  badgeVariant,
  metrics,
  className = ''
}) => {
  return (
    <Card className={`p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          {title}
        </h3>
        <Badge variant={badgeVariant} size="sm">{badgeText}</Badge>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {metrics.map((metric, index) => (
          <MetricCard key={index} {...metric} />
        ))}
      </div>
    </Card>
  );
};

export default MetricsSection;
