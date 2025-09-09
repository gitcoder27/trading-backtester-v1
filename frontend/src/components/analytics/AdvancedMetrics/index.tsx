import React from 'react';
import Card from '../../ui/Card';
import { usePerformanceData } from './usePerformanceData';
import MetricsSection from './MetricsSection';
import { getCoreMetrics, getAdvancedMetrics, getTradeMetrics, getRiskMetrics, getDailyTargetMetrics } from './metricsConfig';
import type { AdvancedMetricsProps } from './types';

const AdvancedMetrics: React.FC<AdvancedMetricsProps> = ({ backtestId, className = '' }) => {
  const { data, isLoading, error, performance } = usePerformanceData(backtestId);

  if (isLoading) {
    return (
      <div className={`space-y-6 ${className}`}>
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="p-6">
            <div className="animate-pulse">
              <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-4"></div>
              <div className="grid grid-cols-2 gap-4">
                {[...Array(4)].map((_, j) => (
                  <div key={j} className="h-16 bg-gray-200 dark:bg-gray-700 rounded"></div>
                ))}
              </div>
            </div>
          </Card>
        ))}
      </div>
    );
  }

  if (error || !data?.success) {
    return (
      <Card className={`p-6 ${className}`}>
        <div className="text-center">
          <div className="text-red-500 text-lg font-medium mb-2">
            Failed to load performance data
          </div>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            {error?.message || 'Unknown error occurred'}
          </p>
        </div>
      </Card>
    );
  }

  if (!performance) {
    return (
      <Card className={`p-6 ${className}`}>
        <div className="text-center">
          <p className="text-gray-600 dark:text-gray-400">
            No performance data available
          </p>
        </div>
      </Card>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Core Performance Metrics */}
      <MetricsSection
        title="Core Performance Metrics"
        badgeText="Updated"
        badgeVariant="primary"
        metrics={getCoreMetrics(performance)}
      />

      {/* Advanced Analytics */}
      <MetricsSection
        title="Advanced Analytics"
        badgeText="Statistical"
        badgeVariant="info"
        metrics={getAdvancedMetrics(performance)}
      />

      {/* Trade Analysis */}
      <MetricsSection
        title="Trade Analysis"
        badgeText="Detailed"
        badgeVariant="success"
        metrics={getTradeMetrics(performance)}
      />

      {/* Daily Target Stats */}
      {performance.daily_target_stats && (
        <MetricsSection
          title="Daily Target Stats"
          badgeText="Daily"
          badgeVariant="info"
          metrics={getDailyTargetMetrics(performance)}
        />
      )}

      {/* Risk Metrics */}
      <MetricsSection
        title="Risk Metrics"
        badgeText="Risk"
        badgeVariant="warning"
        metrics={getRiskMetrics(performance)}
      />
    </div>
  );
};

export default AdvancedMetrics;
