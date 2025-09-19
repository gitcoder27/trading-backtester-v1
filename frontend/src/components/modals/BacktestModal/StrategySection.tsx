import React, { useEffect, useState } from 'react';
import { Database } from 'lucide-react';
import StrategyParameterForm from '../../strategies/StrategyParameterForm';
import type { Strategy, Dataset, EnhancedBacktestConfig } from './types';
import type { ParameterSchema } from '../../../types';
import { StrategyService } from '../../../services/strategyService';
import { showToast } from '../../ui/Toast';

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
  const [schema, setSchema] = useState<ParameterSchema[]>([]);
  const [loadingSchema, setLoadingSchema] = useState(false);

  const normalizeSchema = (raw: any): ParameterSchema[] => {
    if (!raw) return [];
    const val = (raw as any).parameters_schema ?? raw;
    if (Array.isArray(val)) {
      return (val as any[]).filter(Boolean) as ParameterSchema[];
    }
    if (typeof val === 'object') {
      return Object.entries(val)
        .filter(([key]) => key !== 'params')
        .map(([name, s]) => {
          const obj = s as any;
          return {
            name,
            type: (obj.type || obj.input_type || 'str') as ParameterSchema['type'],
            default: obj.default,
            min: obj.min,
            max: obj.max,
            options: obj.options,
            description: obj.description || obj.label,
            required: obj.required,
          } as ParameterSchema;
        });
    }
    return [];
  };

  // Load parameter schema for selected strategy
  useEffect(() => {
    const loadSchema = async () => {
      if (!config.strategy_id) {
        setSchema([]);
        return;
      }
      const selected = strategies.find(s => s.id.toString() === String(config.strategy_id));
      if (selected?.parameters_schema && selected.parameters_schema.length > 0) {
        setSchema(normalizeSchema(selected.parameters_schema));
        return;
      }
      try {
        setLoadingSchema(true);
        const params = await StrategyService.getStrategySchema(config.strategy_id);
        setSchema(normalizeSchema(params));
      } catch (e) {
        console.error('Failed to load strategy schema', e);
        showToast.error('Failed to load parameter schema');
        setSchema([]);
      } finally {
        setLoadingSchema(false);
      }
    };
    loadSchema();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [config.strategy_id]);

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
          {strategies.find(s => s.id.toString() === String(config.strategy_id))?.description || 'No description available'}
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
              {dataset.name} ({Number((dataset as any).rows_count ?? (dataset as any).rows ?? 0).toLocaleString()} rows)
            </option>
          ))}
        </select>
        {config.dataset_id && (
          <div className="text-sm text-gray-600 dark:text-gray-400">
            {(() => {
              const dataset = datasets.find(d => d.id.toString() === String(config.dataset_id));
              if (!dataset) return '';
              const dr = (dataset as any).date_range;
              const start = dr?.start || (dataset as any).start_date || '';
              const end = dr?.end || (dataset as any).end_date || '';
              return start && end ? `${start} to ${end}` : '';
            })()}
          </div>
        )}
      </div>

      {/* Strategy Parameters */}
      {config.strategy_id && (
        <div className="border-t pt-4">
          <StrategyParameterForm
            schema={schema}
            initialValues={config.strategy_params}
            onParametersChange={onParametersChange}
            className="mt-2"
          />
          {loadingSchema && (
            <div className="text-sm text-gray-500 dark:text-gray-400 mt-2">Loading parameters…</div>
          )}
        </div>
      )}
    </div>
  );
};

export default StrategySection;
