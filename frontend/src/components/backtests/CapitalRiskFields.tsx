import React from 'react';
import Input from '../ui/Input';
import type { BacktestConfig } from '../../types';

interface Props {
  config: Partial<BacktestConfig>;
  errors: Record<string, string>;
  onChange: (key: keyof BacktestConfig, value: any) => void;
}

const CapitalRiskFields: React.FC<Props> = ({ config, errors, onChange }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Input
        label="Initial Capital"
        type="number"
        value={config.initial_capital || ''}
        onChange={(e) => onChange('initial_capital', Number(e.target.value))}
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
        onChange={(e) => onChange('position_size', Number(e.target.value))}
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
        onChange={(e) => onChange('commission', Number(e.target.value) / 100)}
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
        onChange={(e) => onChange('slippage', Number(e.target.value) / 100)}
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
        onChange={(e) => onChange('start_date', e.target.value)}
      />

      <Input
        label="End Date (Optional)"
        type="date"
        value={config.end_date || ''}
        onChange={(e) => onChange('end_date', e.target.value)}
      />
    </div>
  );
};

export default CapitalRiskFields;

