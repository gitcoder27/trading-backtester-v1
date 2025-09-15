import React from 'react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import { Target, CheckCircle, Clock, Edit3, Play, AlertTriangle, Plus } from 'lucide-react';
import StrategyDiscovery from './StrategyDiscovery';
import type { Strategy } from '../../types';

interface Props {
  strategies: Strategy[];
  allCount: number;
  onClick: (id: string) => void;
  onEdit: (id: string) => void;
  onRunBacktest: (id: string) => void;
  onDiscoverClick?: (ids: string[]) => void;
  onCreate?: () => void;
}

const StrategiesGrid: React.FC<Props> = ({ strategies, allCount, onClick, onEdit, onRunBacktest, onDiscoverClick, onCreate }) => {
  if (!strategies || strategies.length === 0) {
    return (
      <Card className="text-center py-12">
        <AlertTriangle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
          {allCount === 0 ? 'No Strategies Found' : 'No Matching Strategies'}
        </h3>
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          {allCount === 0
            ? 'Start by discovering existing strategies or creating a new one.'
            : 'Try adjusting your search or filter criteria.'}
        </p>
        {allCount === 0 && (
          <div className="flex justify-center space-x-3">
            <StrategyDiscovery onStrategiesRegistered={onDiscoverClick || (() => {})} />
            <Button icon={Plus} onClick={onCreate || (() => {})}>
              Create Strategy
            </Button>
          </div>
        )}
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {strategies.map((strategy) => (
        <div
          key={strategy.id}
          className="p-6 hover:shadow-lg transition-all duration-200 cursor-pointer bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-soft"
          onClick={() => onClick(strategy.id)}
        >
          <div className="space-y-4">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-primary-100 dark:bg-primary-900/50 rounded-lg">
                  <Target className="h-5 w-5 text-primary-600 dark:text-primary-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                    {strategy.name || 'Unnamed Strategy'}
                  </h3>
                  <div className="flex items-center space-x-2 mt-1">
                    <Badge variant={strategy.is_active ? 'success' : 'danger'} size="sm">
                      <CheckCircle className="h-3 w-3 mr-1" />
                      {strategy.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                    {strategy.performance_summary && (
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {strategy.performance_summary.total_backtests || 0} runs
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
              {strategy.description || 'No description available'}
            </p>

            {strategy.performance_summary ? (
              <div className="grid grid-cols-2 gap-4 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Avg Performance</p>
                  <p
                    className={`font-semibold ${
                      (strategy.performance_summary.avg_return || 0) >= 0
                        ? 'text-success-600 dark:text-success-400'
                        : 'text-danger-600 dark:text-danger-400'
                    }`}
                  >
                    {(strategy.performance_summary.avg_return || 0).toFixed(2)}%
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Last Run</p>
                  <div className="flex items-center space-x-1">
                    <Clock className="h-3 w-3 text-gray-400" />
                    <p className="text-xs font-medium text-gray-700 dark:text-gray-300">
                      {strategy.last_backtest_at
                        ? new Date(strategy.last_backtest_at).toLocaleDateString()
                        : 'Never'}
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg text-center">
                <p className="text-xs text-gray-500 dark:text-gray-400">No backtest data available</p>
              </div>
            )}

            <div className="flex space-x-2 pt-2">
              <Button
                variant="nav"
                size="sm"
                icon={Edit3}
                onClick={(e) => {
                  e.stopPropagation();
                  onEdit(strategy.id);
                }}
                className="flex-1"
              >
                Edit
              </Button>
              <Button
                variant="action"
                size="sm"
                icon={Play}
                onClick={(e) => {
                  e.stopPropagation();
                  onRunBacktest(strategy.id);
                }}
                className="flex-1"
                disabled={!strategy.is_active}
              >
                Run Backtest
              </Button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default StrategiesGrid;
