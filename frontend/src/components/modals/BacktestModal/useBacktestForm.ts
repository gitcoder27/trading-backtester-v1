import { useState, useEffect } from 'react';
import { showToast } from '../../ui/Toast';
import type { EnhancedBacktestConfig, Strategy, Dataset } from './types';
import type { BacktestConfig as BaseBacktestConfig } from '../../../types';

const DEFAULT_CONFIG: EnhancedBacktestConfig = {
  strategy_id: '',
  dataset_id: '',
  initial_capital: 100000,
  position_size: 75, // 1 lot = 75 units
  commission: 0.0,
  slippage: 0.0,
  parameters: {},
  strategy_params: {},
  option_delta: 0.5,
  lots: 2,
  option_price_per_unit: 1.0,
  fee_per_trade: 0.0,
  daily_profit_target: 30.0,
  intraday_mode: true,
  session_close_time: '15:15',
  direction_filter: ['long', 'short'],
  apply_time_filter: false,
  start_hour: 9,
  end_hour: 15,
  apply_weekday_filter: false,
  weekdays: [0, 1, 2, 3, 4] // Mon-Fri
};

export const useBacktestForm = (isOpen: boolean) => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [config, setConfig] = useState<EnhancedBacktestConfig>(DEFAULT_CONFIG);

  useEffect(() => {
    if (isOpen) {
      loadStrategies();
      loadDatasets();
    }
  }, [isOpen]);

  const loadStrategies = async () => {
    try {
      const response = await fetch('/api/v1/strategies/');
      const data = await response.json();
      if (data.success) {
        setStrategies(data.strategies);
        // Auto-select first strategy if none selected
        if (data.strategies.length > 0 && !config.strategy_id) {
          setConfig(prev => ({ ...prev, strategy_id: data.strategies[0].id.toString() }));
        }
      }
    } catch (error) {
      console.error('Failed to load strategies:', error);
      showToast.error('Failed to load strategies');
    }
  };

  const loadDatasets = async () => {
    try {
      const response = await fetch('/api/v1/datasets/');
      const data = await response.json();
      if (data.success) {
        setDatasets(data.datasets);
        // Auto-select first dataset if none selected
        if (data.datasets.length > 0 && !config.dataset_id) {
          setConfig(prev => ({ ...prev, dataset_id: data.datasets[0].id.toString() }));
        }
      }
    } catch (error) {
      console.error('Failed to load datasets:', error);
      showToast.error('Failed to load datasets');
    }
  };

  const handleConfigChange = (key: keyof EnhancedBacktestConfig, value: any) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  const handleParametersChange = (parameters: Record<string, any>) => {
    setConfig(prev => ({ ...prev, strategy_params: parameters }));
  };

  const validateAndConvertConfig = (): BaseBacktestConfig | null => {
    // Validation
    if (!config.strategy_id) {
      showToast.error('Please select a strategy');
      return null;
    }
    if (!config.dataset_id) {
      showToast.error('Please select a dataset');
      return null;
    }

    // Convert enhanced config to base config
    const baseConfig: BaseBacktestConfig = {
      strategy_id: config.strategy_id,
      dataset_id: config.dataset_id,
      initial_capital: config.initial_capital,
      position_size: config.lots * 75, // Convert lots to position size
      commission: config.fee_per_trade,
      slippage: 0.0,
      parameters: {
        ...config.strategy_params,
        // Add enhanced parameters to the parameters object for backend processing
        option_delta: config.option_delta,
        option_price_per_unit: config.option_price_per_unit,
        daily_profit_target: config.daily_profit_target,
        intraday_mode: config.intraday_mode,
        session_close_time: config.session_close_time,
        direction_filter: config.direction_filter,
        apply_time_filter: config.apply_time_filter,
        start_hour: config.start_hour,
        end_hour: config.end_hour,
        apply_weekday_filter: config.apply_weekday_filter,
        weekdays: config.weekdays
      }
    };

    return baseConfig;
  };

  const resetForm = () => {
    setConfig(DEFAULT_CONFIG);
  };

  return {
    strategies,
    datasets,
    config,
    handleConfigChange,
    handleParametersChange,
    validateAndConvertConfig,
    resetForm
  };
};
