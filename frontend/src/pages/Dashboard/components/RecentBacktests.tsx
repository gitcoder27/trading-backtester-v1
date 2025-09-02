import React from 'react';
import { BarChart3 } from 'lucide-react';
import { Card, Button, StatusBadge, PerformanceBadge, LoadingSkeleton } from '../../../components/ui';

interface RecentBacktestsProps {
  recentBacktests: any[];
  loading: boolean;
}

const RecentBacktests: React.FC<RecentBacktestsProps> = ({ recentBacktests, loading }) => {
  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Recent Backtests
        </h3>
        <Button variant="ghost" size="sm">
          View All
        </Button>
      </div>
      
      <div className="space-y-4">
        {loading ? (
          <div className="space-y-4">
            <LoadingSkeleton height="h-16" />
            <LoadingSkeleton height="h-16" />
            <LoadingSkeleton height="h-16" />
          </div>
        ) : recentBacktests.length > 0 ? (
          recentBacktests.slice(0, 3).map((backtest) => (
            <div 
              key={backtest.id}
              className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700"
            >
              <div className="flex-1">
                <div className="flex items-center space-x-3">
                  <h4 className="font-medium text-gray-900 dark:text-gray-100">
                    Strategy: {backtest.strategy_id}
                  </h4>
                  <StatusBadge status={backtest.status} size="sm" />
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {new Date(backtest.created_at).toLocaleDateString()}
                </p>
              </div>
              
              {backtest.status === 'completed' && backtest.results && (
                <div className="text-right">
                  <PerformanceBadge value={backtest.results.total_return * 100} format="percentage" size="sm" />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Sharpe: {backtest.results.sharpe_ratio.toFixed(2)}
                  </p>
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <BarChart3 className="h-12 w-12 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
            <p>No backtests found</p>
            <p className="text-sm">Run your first backtest to see results here</p>
          </div>
        )}
      </div>
    </Card>
  );
};

export default RecentBacktests;
