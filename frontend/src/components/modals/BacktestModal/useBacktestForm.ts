import { useState, useEffect, useCallback } from 'react';
import { showToast } from '../../ui/Toast';
import { apiClient } from '../../../services/api';
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

export const useBacktestForm = (
  isOpen: boolean,
  preselectedStrategyId?: string | number,
  preselectedParameters?: Record<string, any>
) => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [config, setConfig] = useState<EnhancedBacktestConfig>(DEFAULT_CONFIG);

  const loadStrategies = useCallback(async () => {
    try {
      const data = await apiClient.get<{ success: boolean; strategies: Strategy[]; total?: number }>('/strategies/');
      if ((data as any).success !== false) {
        const list = ((data as any).strategies || []) as Strategy[];
        setStrategies(list);
        // Auto-select first strategy if none selected
        if (list.length > 0) {
          setConfig(prev => {
            if (prev.strategy_id || preselectedStrategyId) return prev;
            return { ...prev, strategy_id: (list[0].id as any).toString() };
          });
        }
      }
    } catch (error) {
      console.error('Failed to load strategies:', error);
      showToast.error('Failed to load strategies');
    }
  }, [preselectedStrategyId]);

  const loadDatasets = useCallback(async () => {
    try {
      const data = await apiClient.get<{ success: boolean; datasets: Dataset[]; total?: number }>('/datasets/');
      if ((data as any).success !== false) {
        const list = ((data as any).datasets || []) as Dataset[];
        setDatasets(list);
        // Auto-select first dataset if none selected
        if (list.length > 0) {
          setConfig(prev => {
            if (prev.dataset_id) return prev;
            return { ...prev, dataset_id: (list[0].id as any).toString() };
          });
        }
      }
    } catch (error) {
      console.error('Failed to load datasets:', error);
      showToast.error('Failed to load datasets');
    }
  }, []);

  useEffect(() => {
    if (!isOpen) return;

    if (preselectedStrategyId) {
      setConfig(prev => ({
        ...prev,
        strategy_id: preselectedStrategyId.toString(),
        strategy_params: preselectedParameters || prev.strategy_params
      }));
    }

    void loadStrategies();
    void loadDatasets();
  }, [isOpen, preselectedStrategyId, preselectedParameters, loadStrategies, loadDatasets]);

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
      // Interpret position_size in BaseBacktestConfig as 'lots' to match backend
      position_size: config.lots,
      commission: config.fee_per_trade,
      slippage: config.slippage,
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
