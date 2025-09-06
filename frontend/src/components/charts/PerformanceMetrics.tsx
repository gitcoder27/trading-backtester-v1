import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { TrendingUp, TrendingDown, Activity, Target, DollarSign, Clock } from 'lucide-react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import { AnalyticsService } from '../../services/analytics';

interface PerformanceMetricsProps {
  backtestId: string;
  className?: string;
}

interface MetricCardProps {
  label: string;
  value: string;
  icon: React.ElementType;
  color: string;
  bgColor: string;
  description?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ 
  label, 
  value, 
  icon: Icon, 
  color, 
  bgColor, 
  description 
}) => (
  <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
    <div className="flex items-center justify-between">
      <div className="flex items-center space-x-3">
        <div className={`p-2 rounded-lg ${bgColor}`}>
          <Icon className={`h-5 w-5 ${color}`} />
        </div>
        <div>
          <p className="text-sm text-gray-600 dark:text-gray-400">{label}</p>
          <p className="text-xl font-semibold text-gray-900 dark:text-gray-100">{value}</p>
          {description && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{description}</p>
          )}
        </div>
      </div>
    </div>
  </div>
);

const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({ backtestId, className = '' }) => {
  const {
    data: performanceData,
    isLoading,
    error
  } = useQuery({
    queryKey: ['performance-metrics', backtestId],
    queryFn: () => AnalyticsService.getPerformanceSummary(backtestId),
    enabled: !!backtestId,
    staleTime: 5 * 60 * 1000,
  });

  if (isLoading) {
    return (
      <Card className={`p-6 ${className}`}>
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 dark:bg-gray-700 rounded"></div>
            ))}
          </div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={`p-6 ${className}`}>
        <div className="text-center text-red-500">
          Failed to load performance metrics: {error.message}
        </div>
      </Card>
    );
  }

  // Backend response shape: { success, backtest_id, performance: { basic_metrics, advanced_analytics, risk_metrics, ... } }
  const base = (performanceData as any)?.performance?.basic_metrics || {};
  const adv = (performanceData as any)?.performance?.advanced_analytics || {};
  const risk = (performanceData as any)?.performance?.risk_metrics || {};
  const metrics = { ...base, ...adv, ...risk };
  if (!metrics) {
    return (
      <Card className={`p-6 ${className}`}>
        <div className="text-center text-gray-500 dark:text-gray-400">
          No performance data available
        </div>
      </Card>
    );
  }

  const formatPercent = (value: number) => `${(value).toFixed(2)}%`;
  const formatNumber = (value: number) => (Number.isFinite(value) ? value.toFixed(2) : '0.00');

  return (
    <Card className={`p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Performance Metrics
        </h3>
        <Badge variant="primary" size="sm">
          <Activity className="h-3 w-3 mr-1" />
          Live Data
        </Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <MetricCard
          label="Total Return"
          value={formatPercent((metrics.total_return_pct ?? (metrics.total_return ?? 0) * 100) as number)}
          icon={TrendingUp}
          color={metrics.total_return > 0 ? "text-success-600 dark:text-success-400" : "text-danger-600 dark:text-danger-400"}
          bgColor={metrics.total_return > 0 ? "bg-success-100 dark:bg-success-900/50" : "bg-danger-100 dark:bg-danger-900/50"}
          description="Overall portfolio return"
        />

        <MetricCard
          label="Sharpe Ratio"
          value={formatNumber(metrics.sharpe_ratio || 0)}
          icon={Activity}
          color="text-primary-600 dark:text-primary-400"
          bgColor="bg-primary-100 dark:bg-primary-900/50"
          description="Risk-adjusted return"
        />

        <MetricCard
          label="Max Drawdown"
          value={formatPercent(Math.abs((metrics.max_drawdown_pct ?? (metrics.max_drawdown ?? 0) * 100) as number))}
          icon={TrendingDown}
          color="text-danger-600 dark:text-danger-400"
          bgColor="bg-danger-100 dark:bg-danger-900/50"
          description="Largest peak-to-trough decline"
        />

        <MetricCard
          label="Win Rate"
          value={formatPercent((metrics.win_rate ?? 0) as number)}
          icon={Target}
          color={metrics.win_rate > 0.5 ? "text-success-600 dark:text-success-400" : "text-warning-600 dark:text-warning-400"}
          bgColor={metrics.win_rate > 0.5 ? "bg-success-100 dark:bg-success-900/50" : "bg-warning-100 dark:bg-warning-900/50"}
          description="Percentage of profitable trades"
        />

        <MetricCard
          label="Profit Factor"
          value={formatNumber(metrics.profit_factor || 0)}
          icon={DollarSign}
          color={metrics.profit_factor > 1 ? "text-success-600 dark:text-success-400" : "text-danger-600 dark:text-danger-400"}
          bgColor={metrics.profit_factor > 1 ? "bg-success-100 dark:bg-success-900/50" : "bg-danger-100 dark:bg-danger-900/50"}
          description="Gross profit / Gross loss"
        />

        <MetricCard
          label="Avg Trade Duration"
          value={`${(metrics.avg_trade_duration || 0).toFixed(1)} days`}
          icon={Clock}
          color="text-gray-600 dark:text-gray-400"
          bgColor="bg-gray-100 dark:bg-gray-800"
          description="Average holding period"
        />
      </div>

      {/* Additional metrics in a more compact format */}
      <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
        <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-4">Additional Metrics</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-600 dark:text-gray-400">Total Trades:</span>
            <span className="ml-2 font-medium text-gray-900 dark:text-gray-100">
              {metrics.total_trades || 0}
            </span>
          </div>
          <div>
            <span className="text-gray-600 dark:text-gray-400">Volatility:</span>
            <span className="ml-2 font-medium text-gray-900 dark:text-gray-100">
              {formatPercent(((metrics.volatility_annualized ?? metrics.volatility) ?? 0) as number)}
            </span>
          </div>
          <div>
            <span className="text-gray-600 dark:text-gray-400">Calmar Ratio:</span>
            <span className="ml-2 font-medium text-gray-900 dark:text-gray-100">
              {formatNumber((metrics.calmar_ratio ?? 0) as number)}
            </span>
          </div>
          <div>
            <span className="text-gray-600 dark:text-gray-400">Sortino Ratio:</span>
            <span className="ml-2 font-medium text-gray-900 dark:text-gray-100">
              {formatNumber((metrics.sortino_ratio ?? 0) as number)}
            </span>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default PerformanceMetrics;
