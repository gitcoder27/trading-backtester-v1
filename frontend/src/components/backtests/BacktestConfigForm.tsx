import React, { useState, useEffect } from 'react';
import { Search, AlertCircle, CheckCircle, Settings, Calendar, DollarSign } from 'lucide-react';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import type { BacktestConfig } from '../../types';
import { StrategyService } from '../../services/strategyService';
import { DatasetService } from '../../services/dataset';
import { showToast } from '../ui/Toast';

interface Strategy {
  id: string;
  name: string;
  description?: string;
  is_active: boolean;
  parameters_schema?: Array<{
    name: string;
    type: 'int' | 'float' | 'bool' | 'str' | 'select';
    default: any;
    min?: number;
    max?: number;
    options?: any[];
    description?: string;
    required?: boolean;
  }>;
}

interface Dataset {
  id: number | string;
  name: string;
  symbol?: string | null;
  timeframe: string;
  rows_count: number;
  start_date: string;
  end_date: string;
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
  
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [strategySearchTerm, setStrategySearchTerm] = useState('');
  const [datasetSearchTerm, setDatasetSearchTerm] = useState('');
  const [showStrategyDropdown, setShowStrategyDropdown] = useState(false);
  const [showDatasetDropdown, setShowDatasetDropdown] = useState(false);
  const [parameters, setParameters] = useState<Record<string, any>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    loadStrategies();
    loadDatasets();
  }, []);

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

  const loadStrategies = async () => {
    try {
      const strategies = await StrategyService.getStrategies();
      setStrategies(strategies || []);
    } catch (error) {
      console.error('Failed to load strategies:', error);
      showToast.error('Failed to load strategies');
    }
  };

  const loadDatasets = async () => {
    try {
      const response = await DatasetService.listDatasets();
      // The API returns { success: true, datasets: [...], total: 14 }
      // but we expect { items: [...], total: 14 }
      const datasets = (response as any).datasets || response.items || [];
      setDatasets(datasets);
    } catch (error) {
      console.error('Failed to load datasets:', error);
      showToast.error('Failed to load datasets');
    }
  };

  const filteredStrategies = strategies.filter(strategy =>
    strategy.is_active && 
    strategy.name.toLowerCase().includes(strategySearchTerm.toLowerCase())
  );

  const filteredDatasets = datasets.filter(dataset =>
    dataset.name.toLowerCase().includes(datasetSearchTerm.toLowerCase()) ||
    (dataset.symbol && dataset.symbol.toLowerCase().includes(datasetSearchTerm.toLowerCase()))
  );

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!selectedStrategy) {
      newErrors.strategy = 'Please select a strategy';
    }

    if (!selectedDataset) {
      newErrors.dataset = 'Please select a dataset';
    }

    if (!config.initial_capital || config.initial_capital < 1000) {
      newErrors.initial_capital = 'Initial capital must be at least 1,000';
    }

    if (!config.position_size || config.position_size < 1 || config.position_size > 100) {
      newErrors.position_size = 'Position size must be between 1 and 100 lots';
    }

    if (config.commission !== undefined && (config.commission < 0 || config.commission > 0.1)) {
      newErrors.commission = 'Commission must be between 0% and 10%';
    }

    if (config.slippage !== undefined && (config.slippage < 0 || config.slippage > 0.1)) {
      newErrors.slippage = 'Slippage must be between 0% and 10%';
    }

    // Validate strategy parameters
    if (selectedStrategy?.parameters_schema) {
      selectedStrategy.parameters_schema.forEach(param => {
        const value = parameters[param.name];
        
        if (param.required && (value === undefined || value === null || value === '')) {
          newErrors[`param_${param.name}`] = `${param.name} is required`;
        }

        if (param.type === 'int' || param.type === 'float') {
          const numValue = Number(value);
          if (!isNaN(numValue)) {
            if (param.min !== undefined && numValue < param.min) {
              newErrors[`param_${param.name}`] = `${param.name} must be at least ${param.min}`;
            }
            if (param.max !== undefined && numValue > param.max) {
              newErrors[`param_${param.name}`] = `${param.name} must be at most ${param.max}`;
            }
          }
        }
      });
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
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

  const renderParameterField = (param: any) => {
    const value = parameters[param.name];
    const error = errors[`param_${param.name}`];

    switch (param.type) {
      case 'bool':
        return (
          <div key={param.name} className="space-y-2">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={value || false}
                onChange={(e) => setParameters(prev => ({
                  ...prev,
                  [param.name]: e.target.checked
                }))}
                className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {param.name}
              </span>
            </label>
            {param.description && (
              <p className="text-xs text-gray-500 dark:text-gray-400">{param.description}</p>
            )}
            {error && <p className="text-xs text-red-500">{error}</p>}
          </div>
        );

      case 'select':
        return (
          <div key={param.name} className="space-y-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              {param.name}
              {param.required && <span className="text-red-500 ml-1">*</span>}
            </label>
            <select
              value={value || ''}
              onChange={(e) => setParameters(prev => ({
                ...prev,
                [param.name]: e.target.value
              }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white"
            >
              <option value="">Select {param.name}</option>
              {(param.options || []).map((option: any) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            {param.description && (
              <p className="text-xs text-gray-500 dark:text-gray-400">{param.description}</p>
            )}
            {error && <p className="text-xs text-red-500">{error}</p>}
          </div>
        );

      default:
        return (
          <div key={param.name} className="space-y-2">
            <Input
              label={param.name}
              type={param.type === 'int' || param.type === 'float' ? 'number' : 'text'}
              value={value || ''}
              onChange={(e) => {
                let newValue: any = e.target.value;
                if (param.type === 'int') {
                  newValue = newValue === '' ? '' : parseInt(newValue);
                } else if (param.type === 'float') {
                  newValue = newValue === '' ? '' : parseFloat(newValue);
                }
                setParameters(prev => ({
                  ...prev,
                  [param.name]: newValue
                }));
              }}
              placeholder={`Enter ${param.name}`}
              min={param.min}
              max={param.max}
              step={param.type === 'float' ? 'any' : '1'}
              required={param.required}
              error={error}
              helpText={param.description}
            />
          </div>
        );
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl mx-auto">
      {/* Strategy Selection */}
      <Card className="p-6">
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <Settings className="w-5 h-5 text-blue-500" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Strategy Selection
            </h3>
          </div>

          <div className="relative">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search strategies..."
                value={selectedStrategy ? selectedStrategy.name : strategySearchTerm}
                onChange={(e) => {
                  setStrategySearchTerm(e.target.value);
                  if (selectedStrategy) {
                    setSelectedStrategy(null);
                  }
                }}
                onFocus={() => setShowStrategyDropdown(true)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
              />
            </div>
            
            {showStrategyDropdown && (
              <div className="absolute z-10 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-lg max-h-60 overflow-auto">
                {filteredStrategies.length === 0 ? (
                  <div className="p-3 text-gray-500 dark:text-gray-400 text-sm">
                    No strategies found
                  </div>
                ) : (
                  filteredStrategies.map((strategy) => (
                    <div
                      key={strategy.id}
                      onClick={() => {
                        setSelectedStrategy(strategy);
                        setShowStrategyDropdown(false);
                        setStrategySearchTerm('');
                      }}
                      className="p-3 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer border-b border-gray-100 dark:border-gray-700 last:border-b-0"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium text-gray-900 dark:text-gray-100">
                            {strategy.name}
                          </div>
                          {strategy.description && (
                            <div className="text-sm text-gray-500 dark:text-gray-400">
                              {strategy.description}
                            </div>
                          )}
                        </div>
                        <Badge variant="success" size="sm">
                          Active
                        </Badge>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          {selectedStrategy && (
            <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md">
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-green-600" />
                <span className="text-sm font-medium text-green-800 dark:text-green-200">
                  Selected: {selectedStrategy.name}
                </span>
              </div>
            </div>
          )}

          {errors.strategy && (
            <div className="flex items-center space-x-2 text-red-600">
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm">{errors.strategy}</span>
            </div>
          )}
        </div>
      </Card>

      {/* Dataset Selection */}
      <Card className="p-6">
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <Calendar className="w-5 h-5 text-blue-500" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Dataset Selection
            </h3>
          </div>

          <div className="relative">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search datasets..."
                value={selectedDataset ? `${selectedDataset.name} (${selectedDataset.symbol})` : datasetSearchTerm}
                onChange={(e) => {
                  setDatasetSearchTerm(e.target.value);
                  if (selectedDataset) {
                    setSelectedDataset(null);
                  }
                }}
                onFocus={() => setShowDatasetDropdown(true)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
              />
            </div>
            
            {showDatasetDropdown && (
              <div className="absolute z-10 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-lg max-h-60 overflow-auto">
                {filteredDatasets.length === 0 ? (
                  <div className="p-3 text-gray-500 dark:text-gray-400 text-sm">
                    No datasets found
                  </div>
                ) : (
                  filteredDatasets.map((dataset) => (
                    <div
                      key={dataset.id}
                      onClick={() => {
                        setSelectedDataset(dataset);
                        setShowDatasetDropdown(false);
                        setDatasetSearchTerm('');
                      }}
                      className="p-3 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer border-b border-gray-100 dark:border-gray-700 last:border-b-0"
                    >
                      <div>
                        <div className="font-medium text-gray-900 dark:text-gray-100">
                          {dataset.name}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {dataset.symbol || 'No Symbol'} • {dataset.timeframe} • {dataset.rows_count.toLocaleString()} records
                        </div>
                        <div className="text-xs text-gray-400 dark:text-gray-500">
                          {dataset.start_date} to {dataset.end_date}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          {selectedDataset && (
            <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md">
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-green-600" />
                <span className="text-sm font-medium text-green-800 dark:text-green-200">
                  Selected: {selectedDataset.name} ({selectedDataset.symbol})
                </span>
              </div>
            </div>
          )}

          {errors.dataset && (
            <div className="flex items-center space-x-2 text-red-600">
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm">{errors.dataset}</span>
            </div>
          )}
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

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Initial Capital"
              type="number"
              value={config.initial_capital || ''}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                initial_capital: Number(e.target.value)
              }))}
              placeholder="100000"
              min="1000"
              step="1"
              required
              error={errors.initial_capital}
            />

            <Input
              label="Position Size (Lots)"
              type="number"
              value={config.position_size || ''}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                position_size: Number(e.target.value)
              }))}
              placeholder="2"
              min="1"
              max="100"
              step="1"
              required
              error={errors.position_size}
            />

            <Input
              label="Commission (%)"
              type="number"
              value={config.commission ? (config.commission * 100).toFixed(4) : ''}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                commission: Number(e.target.value) / 100
              }))}
              placeholder="0.01"
              min="0"
              max="10"
              step="0.001"
              error={errors.commission}
            />

            <Input
              label="Slippage (%)"
              type="number"
              value={config.slippage ? (config.slippage * 100).toFixed(4) : ''}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                slippage: Number(e.target.value) / 100
              }))}
              placeholder="0.01"
              min="0"
              max="10"
              step="0.001"
              error={errors.slippage}
            />

            <Input
              label="Start Date (Optional)"
              type="date"
              value={config.start_date || ''}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                start_date: e.target.value
              }))}
            />

            <Input
              label="End Date (Optional)"
              type="date"
              value={config.end_date || ''}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                end_date: e.target.value
              }))}
            />
          </div>
        </div>
      </Card>

      {/* Strategy Parameters */}
      {selectedStrategy?.parameters_schema && selectedStrategy.parameters_schema.length > 0 && (
        <Card className="p-6">
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Strategy Parameters
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {selectedStrategy.parameters_schema.map(renderParameterField)}
            </div>
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
