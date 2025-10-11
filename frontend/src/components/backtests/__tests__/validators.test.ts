import { describe, it, expect } from 'vitest';
import { validateBacktestForm } from '../validators';
import { createBacktestConfig, createStrategy } from '../../../test/factories';

describe('validateBacktestForm', () => {
  it('returns valid when config is complete', () => {
    const config = createBacktestConfig();
    const { valid, errors } = validateBacktestForm(
      config,
      createStrategy(),
      { id: 'dataset-1' },
      {}
    );

    expect(valid).toBe(true);
    expect(errors).toEqual({});
  });

  it('captures missing strategy and dataset', () => {
    const { valid, errors } = validateBacktestForm({}, null, null, {});
    expect(valid).toBe(false);
    expect(errors).toMatchObject({
      strategy: 'Please select a strategy',
      dataset: 'Please select a dataset',
    });
  });

  it('validates numeric boundaries', () => {
    const config = createBacktestConfig({
      initial_capital: 100,
      position_size: 0,
      commission: 0.5,
      slippage: 0.5,
    });
    const { valid, errors } = validateBacktestForm(config, createStrategy(), { id: 'dataset-1' }, {});

    expect(valid).toBe(false);
    expect(errors.initial_capital).toBeDefined();
    expect(errors.position_size).toBeDefined();
    expect(errors.commission).toBeDefined();
    expect(errors.slippage).toBeDefined();
  });

  it('validates parameter schema requirements', () => {
    const schema = [
      { name: 'lookback', type: 'int', default: 10, min: 5, max: 50, required: true },
    ];
    const result = validateBacktestForm(
      createBacktestConfig(),
      createStrategy(),
      { id: 'dataset-1' },
      { lookback: 3 },
      schema
    );

    expect(result.valid).toBe(false);
    expect(result.errors.param_lookback).toContain('at least');
  });
});
