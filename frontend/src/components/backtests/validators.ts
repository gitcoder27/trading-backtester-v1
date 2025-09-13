import type { BacktestConfig, Strategy } from '../../types';

export function validateBacktestForm(
  config: Partial<BacktestConfig>,
  selectedStrategy: Strategy | null,
  selectedDataset: { id: string | number } | null,
  parameters: Record<string, any>,
  parameterSchema?: Array<{
    name: string;
    type: 'int' | 'float' | 'bool' | 'str' | 'select';
    default: any;
    min?: number;
    max?: number;
    options?: any[];
    description?: string;
    required?: boolean;
  }>
): { valid: boolean; errors: Record<string, string> } {
  const newErrors: Record<string, string> = {};

  if (!selectedStrategy) newErrors.strategy = 'Please select a strategy';
  if (!selectedDataset) newErrors.dataset = 'Please select a dataset';

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

  if (parameterSchema && parameterSchema.length > 0) {
    parameterSchema.forEach(param => {
      const value = parameters[param.name];
      if (param.required && (value === undefined || value === null || value === '')) {
        newErrors[`param_${param.name}`] = `${param.name} is required`;
        return;
      }
      if (param.type === 'int' || param.type === 'float') {
        const numValue = Number(value);
        if (!Number.isNaN(numValue)) {
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

  return { valid: Object.keys(newErrors).length === 0, errors: newErrors };
}

