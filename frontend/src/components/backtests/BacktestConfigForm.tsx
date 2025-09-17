import React, { useState, useEffect } from 'react';
import { Settings, Calendar, DollarSign } from 'lucide-react';
import Button from '../ui/Button';
import Card from '../ui/Card';
import type { BacktestConfig, Strategy, ParameterSchema } from '../../types';
import { useStrategies } from '../../hooks/useStrategies';
import { useDatasets } from '../../hooks/useDatasets';
import { showToast } from '../ui/Toast';
import { validateBacktestForm } from './validators';
import CapitalRiskFields from './CapitalRiskFields';
import ParametersGrid from './ParametersGrid';
import StrategyPicker from './StrategyPicker';
import DatasetPicker from './DatasetPicker';
// Dataset shape used by this form (normalized by useDatasets hook)
interface DatasetItem {
  id: number | string;
  name: string;
  symbol?: string | null;
  timeframe?: string;
  rows_count?: number;
  start_date?: string;
  end_date?: string;
  filename?: string;
  file_size?: number;
  data_quality_score?: number;
}

interface BacktestConfigFormProps {
  onSubmit: (config: BacktestConfig) => void;
  onCancel: () => void;
  isSubmitting?: boolean;
  preselectedStrategyId?: string;
  preselectedParameters?: Record<string, any>;
}

const BacktestConfigForm: React.FC<BacktestConfigFormProps> = ({
  onSubmit,
  onCancel,
  isSubmitting = false,
  preselectedStrategyId,
  preselectedParameters
}) => {
  const [config, setConfig] = useState<Partial<BacktestConfig>>({
    initial_capital: 100000,  // Same as Streamlit default
    position_size: 2,         // Same as Streamlit lots default  
    commission: 0.0001,       // 0.01% as decimal
    slippage: 0.0001          // 0.01% as decimal
  });
  
  const { strategies } = useStrategies({ activeOnly: true });
  const { datasets } = useDatasets();
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);
  const [selectedDataset, setSelectedDataset] = useState<DatasetItem | null>(null);
  const [parameters, setParameters] = useState<Record<string, any>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Auto-select preselected strategy when strategies are loaded
  useEffect(() => {
    if (preselectedStrategyId && strategies.length > 0 && !selectedStrategy) {
      const preselectedStrategy = strategies.find(s => s.id === preselectedStrategyId);
      if (preselectedStrategy) {
        setSelectedStrategy(preselectedStrategy);
        setStrategySearchTerm(preselectedStrategy.name);
        setConfig(prev => ({ ...prev, strategy_id: preselectedStrategy.id }));
        
        // Set preselected parameters if provided
        if (preselectedParameters) {
          setParameters(preselectedParameters);
        }
      }
    }
  }, [strategies, preselectedStrategyId, preselectedParameters, selectedStrategy]);

  useEffect(() => {
    if (selectedStrategy?.parameters_schema) {
      const defaultParams: Record<string, any> = {};
      selectedStrategy.parameters_schema.forEach(param => {
        defaultParams[param.name] = param.default;
      });
      // Only set default params if we don't have preselected parameters
      if (!preselectedParameters) {
        setParameters(defaultParams);
      }
    }
  }, [selectedStrategy, preselectedParameters]);

  // Datasets and strategies are loaded via hooks above

  // Filtering is handled inside pickers

  const validateForm = (): boolean => {
    const { valid, errors } = validateBacktestForm(
      config,
      selectedStrategy,
      selectedDataset,
      parameters,
      selectedStrategy?.parameters_schema as any
    );
    setErrors(errors);
    return valid;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      showToast.error('Please fix the errors before submitting');
      return;
    }

    const finalConfig: BacktestConfig = {
      strategy_id: selectedStrategy!.id,
      dataset_id: selectedDataset!.id.toString(),
      initial_capital: config.initial_capital!,
      position_size: config.position_size!,
      commission: config.commission || 0,
      slippage: config.slippage || 0,
      start_date: config.start_date,
      end_date: config.end_date,
      parameters: Object.keys(parameters).length > 0 ? parameters : undefined
    };

    onSubmit(finalConfig);
  };

  // Parameter field rendering moved to ParametersGrid

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl mx-auto">
      {/* Strategy Selection */}
      <Card className="p-6">
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <Settings className="w-5 h-5 text-blue-500" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Strategy Selection</h3>
          </div>
          <StrategyPicker
            strategies={strategies}
            value={selectedStrategy}
            onSelect={(strategy) => {
              setSelectedStrategy(strategy);
              setConfig(prev => ({ ...prev, strategy_id: strategy.id }));
            }}
            error={errors.strategy}
          />
        </div>
      </Card>

      {/* Dataset Selection */}
      <Card className="p-6">
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <Calendar className="w-5 h-5 text-blue-500" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Dataset Selection</h3>
          </div>
          <DatasetPicker
            datasets={datasets}
            value={selectedDataset}
            onSelect={(dataset) => {
              setSelectedDataset(dataset);
              setConfig(prev => ({ ...prev, dataset_id: dataset.id.toString() }));
            }}
            error={errors.dataset}
          />
        </div>
      </Card>

      {/* Backtest Configuration */}
      <Card className="p-6">
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <DollarSign className="w-5 h-5 text-blue-500" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Backtest Configuration
            </h3>
          </div>

          <CapitalRiskFields
            config={config}
            errors={errors}
            onChange={(key, value) => setConfig(prev => ({ ...prev, [key]: value }))}
          />
        </div>
      </Card>

      {/* Strategy Parameters */}
      {selectedStrategy?.parameters_schema && selectedStrategy.parameters_schema.length > 0 && (
        <Card className="p-6">
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Strategy Parameters
            </h3>
            <ParametersGrid
              schema={selectedStrategy.parameters_schema as ParameterSchema[]}
              parameters={parameters}
              errors={errors}
              onChange={(next) => setParameters(next)}
            />
          </div>
        </Card>
      )}

      {/* Action Buttons */}
      <div className="flex justify-end space-x-3">
        <Button
          type="button"
          variant="secondary"
          onClick={onCancel}
          disabled={isSubmitting}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          loading={isSubmitting}
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Starting Backtest...' : 'Start Backtest'}
        </Button>
      </div>
    </form>
  );
};

export default BacktestConfigForm;
