import React from 'react';
import { Database } from 'lucide-react';
import StrategyParameters from '../../strategies/StrategyParameters';
import type { Strategy, Dataset, EnhancedBacktestConfig } from './types';

interface StrategySectionProps {
  strategies: Strategy[];
  datasets: Dataset[];
  config: EnhancedBacktestConfig;
  onConfigChange: (key: keyof EnhancedBacktestConfig, value: any) => void;
  onParametersChange: (parameters: Record<string, any>) => void;
}

const StrategySection: React.FC<StrategySectionProps> = ({
  strategies,
  datasets,
  config,
  onConfigChange,
  onParametersChange
}) => {
  return (
    <div className="space-y-6">
      {/* Strategy Selection */}
      <div className="space-y-3">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          <Database className="w-4 h-4 inline mr-2" />
          Strategy
        </label>
        <select
          value={config.strategy_id}
          onChange={(e) => onConfigChange('strategy_id', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
        >
          <option value="">Select a strategy...</option>
          {strategies.map(strategy => (
            <option key={strategy.id} value={strategy.id}>
              {strategy.name}
            </option>
          ))}
        </select>
        {config.strategy_id && (
          <div className="text-sm text-gray-600 dark:text-gray-400">
            {strategies.find(s => s.id.toString() === config.strategy_id)?.description || 'No description available'}
          </div>
        )}
      </div>

      {/* Dataset Selection */}
      <div className="space-y-3">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          <Database className="w-4 h-4 inline mr-2" />
          Dataset
        </label>
        <select
          value={config.dataset_id}
          onChange={(e) => onConfigChange('dataset_id', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
        >
          <option value="">Select a dataset...</option>
          {datasets.map(dataset => (
            <option key={dataset.id} value={dataset.id}>
              {dataset.name} ({dataset.rows_count.toLocaleString()} rows)
            </option>
          ))}
        </select>
        {config.dataset_id && (
          <div className="text-sm text-gray-600 dark:text-gray-400">
            {(() => {
              const dataset = datasets.find(d => d.id.toString() === config.dataset_id);
              return dataset ? `${dataset.date_range.start} to ${dataset.date_range.end}` : '';
            })()}
          </div>
        )}
      </div>

      {/* Strategy Parameters */}
      {config.strategy_id && (
        <div className="border-t pt-4">
          <StrategyParameters
            strategyId={config.strategy_id}
            initialParameters={config.strategy_params}
            onParametersChange={onParametersChange}
          />
        </div>
      )}
    </div>
  );
};

export default StrategySection;
