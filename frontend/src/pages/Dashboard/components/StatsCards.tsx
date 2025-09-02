import React from 'react';
import { TrendingUp, TrendingDown, Activity, BarChart3 } from 'lucide-react';
import { Card, Badge, PerformanceBadge } from '../../../components/ui';

interface DashboardStats {
  totalReturn: number;
  activeStrategies: number;
  sharpeRatio: number;
  maxDrawdown: number;
  totalBacktests: number;
}

interface StatsCardsProps {
  stats: DashboardStats;
  loading: boolean;
}

const StatsCards: React.FC<StatsCardsProps> = ({ stats, loading }) => {
  const statItems = [
    {
      label: 'Total Return',
      value: loading ? '--' : `+${stats.totalReturn.toFixed(1)}%`,
      icon: TrendingUp,
      bgColor: 'bg-success-100 dark:bg-success-900',
      iconColor: 'text-success-600 dark:text-success-400',
      badge: !loading && <PerformanceBadge value={stats.totalReturn} format="percentage" />
    },
    {
      label: 'Active Strategies',
      value: loading ? '--' : stats.activeStrategies,
      icon: Activity,
      bgColor: 'bg-primary-100 dark:bg-primary-900',
      iconColor: 'text-primary-600 dark:text-primary-400',
      badge: (
        <Badge variant="primary" size="sm">
          {loading ? '--' : `${stats.activeStrategies} Active`}
        </Badge>
      )
    },
    {
      label: 'Avg Performance',
      value: loading ? '--' : (stats.sharpeRatio || 0).toFixed(2),
      icon: BarChart3,
      bgColor: 'bg-info-100 dark:bg-info-900',
      iconColor: 'text-info-600 dark:text-info-400',
      badge: (
        <Badge variant="success" size="sm">
          {loading ? '--' : 'Based on backtests'}
        </Badge>
      )
    },
    {
      label: 'Total Backtests',
      value: loading ? '--' : stats.totalBacktests,
      icon: TrendingDown,
      bgColor: 'bg-warning-100 dark:bg-warning-900',
      iconColor: 'text-warning-600 dark:text-warning-400',
      badge: (
        <Badge variant="info" size="sm">
          {loading ? '--' : 'All time'}
        </Badge>
      )
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {statItems.map((item, index) => (
        <Card key={index} className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                {item.label}
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {item.value}
              </p>
            </div>
            <div className={`h-12 w-12 ${item.bgColor} rounded-lg flex items-center justify-center`}>
              <item.icon className={`h-6 w-6 ${item.iconColor}`} />
            </div>
          </div>
          <div className="mt-4">
            {item.badge}
          </div>
        </Card>
      ))}
    </div>
  );
};

export default StatsCards;
