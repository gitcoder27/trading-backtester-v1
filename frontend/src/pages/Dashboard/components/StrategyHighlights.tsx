import React from 'react';
import { Card, LoadingSkeleton, Badge } from '../../../components/ui';
import type { Strategy } from '../../../types';
import { Star, AlertTriangle } from 'lucide-react';

interface StrategyHighlightsProps {
  topStrategies: Strategy[];
  mostTestedStrategies: Strategy[];
  loading?: boolean;
}

const StrategyHighlights: React.FC<StrategyHighlightsProps> = ({ topStrategies, mostTestedStrategies, loading = false }) => {
  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Strategy Highlights</h3>
      </div>

      {loading ? (
        <div className="space-y-3">
          <LoadingSkeleton className="h-5 w-1/2" />
          <LoadingSkeleton className="h-5 w-2/3" />
          <LoadingSkeleton className="h-5 w-1/3" />
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6">
          <div>
            <div className="flex items-center mb-3">
              <Star className="h-4 w-4 text-amber-500 mr-2" />
              <h4 className="font-medium text-gray-900 dark:text-gray-100">Top Performers</h4>
            </div>
            {topStrategies.length ? (
              <ul className="space-y-2">
                {topStrategies.map((s) => (
                  <li key={s.id} className="flex items-center justify-between p-3 rounded-lg bg-gray-50/60 dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700">
                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate mr-3">{s.name}</span>
                    <span className="text-xs text-gray-500 dark:text-gray-400 mr-3">Tests: {s.performance_summary?.total_backtests ?? s.total_backtests ?? 0}</span>
                    <Badge variant="success" size="sm">
                      {Number((s as any).avg_performance ?? 0).toFixed(2)} avg
                    </Badge>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-600 dark:text-gray-400">No performance data yet.</p>
            )}
          </div>

          <div>
            <div className="flex items-center mb-3">
              <AlertTriangle className="h-4 w-4 text-indigo-500 mr-2" />
              <h4 className="font-medium text-gray-900 dark:text-gray-100">Most Tested</h4>
            </div>
            {mostTestedStrategies.length ? (
              <ul className="space-y-2">
                {mostTestedStrategies.map((s) => (
                  <li key={s.id} className="flex items-center justify-between p-3 rounded-lg bg-gray-50/60 dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700">
                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate mr-3">{s.name}</span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">{(s as any).total_backtests ?? s.performance_summary?.total_backtests ?? 0} runs</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-600 dark:text-gray-400">No runs yet.</p>
            )}
          </div>
        </div>
      )}
    </Card>
  );
};

export default StrategyHighlights;
