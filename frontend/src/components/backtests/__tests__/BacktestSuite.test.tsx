import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';

import BacktestCard from '../BacktestCard';
import BacktestFilterTabs from '../BacktestFilterTabs';
import BacktestStatsRow from '../BacktestStatsRow';
import CapitalRiskFields from '../CapitalRiskFields';
import ParametersGrid from '../ParametersGrid';
import StrategyPicker from '../StrategyPicker';
import DatasetPicker from '../DatasetPicker';
import BacktestConfigForm from '../BacktestConfigForm';

import { createBacktestDisplay, createStrategy } from '../../../test/factories';

const toastMock = vi.hoisted(() => ({
  success: vi.fn(),
  error: vi.fn(),
  warning: vi.fn(),
  info: vi.fn(),
  loading: vi.fn(),
  dismiss: vi.fn(),
}));

vi.mock('../../../hooks/useStrategies', () => ({
  useStrategies: vi.fn(() => ({
    strategies: [
      createStrategy({
        id: 'strategy-1',
        name: 'Sample Strategy',
        description: 'Simple mean reversion',
        parameters_schema: [
          { name: 'lookback', type: 'int', default: 10, min: 5, max: 20, required: true },
          { name: 'use_stop', type: 'bool', default: true },
          { name: 'mode', type: 'select', default: 'aggressive', options: ['aggressive', 'conservative'] },
        ],
      }),
    ],
    loading: false,
    error: null,
  })),
}));

const mockDatasets = [
  {
    id: 'dataset-1',
    name: 'EURUSD Hourly',
    symbol: 'EURUSD',
    timeframe: '1H',
    rows_count: 5000,
    start_date: '2024-01-01',
    end_date: '2024-02-01',
  },
  {
    id: 'dataset-2',
    name: 'GBPUSD Hourly',
    symbol: 'GBPUSD',
    timeframe: '1H',
    rows_count: 4800,
    start_date: '2024-01-01',
    end_date: '2024-02-01',
  },
];

vi.mock('../../../hooks/useDatasets', () => ({
  useDatasets: vi.fn(() => ({ datasets: mockDatasets, loading: false, error: null })),
}));

vi.mock('../../ui/Toast', () => ({
  showToast: toastMock,
  ToastProvider: () => null,
  default: () => null,
}));

describe('Backtests UI suite', () => {
  beforeEach(() => {
    Object.values(toastMock).forEach((fn) => fn.mockReset());
  });

  it('renders BacktestCard and triggers callbacks', () => {
    const backtest = createBacktestDisplay();
    const onView = vi.fn();
    const onDownload = vi.fn();
    const onDelete = vi.fn();

    render(
      <BacktestCard
        backtest={backtest}
        onView={onView}
        onDownload={onDownload}
        onDelete={onDelete}
      />
    );

    expect(screen.getByText(backtest.strategy)).toBeInTheDocument();
    expect(screen.getByText(/Return/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /View/ }));
    fireEvent.click(screen.getByRole('button', { name: /Download/ }));
    fireEvent.click(screen.getByRole('button', { name: /Delete/ }));

    expect(onView).toHaveBeenCalledWith(backtest.id);
    expect(onDownload).toHaveBeenCalledWith(backtest.id);
    expect(onDelete).toHaveBeenCalledWith(backtest.id);
  });

  it('handles BacktestFilterTabs selections', () => {
    const onChange = vi.fn();
    render(
      <BacktestFilterTabs
        selected="all"
        counts={{ all: 5, completed: 2, running: 1, failed: 2 }}
        onChange={onChange}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /Completed/ }));
    expect(onChange).toHaveBeenCalledWith('completed');
  });

  it('renders BacktestStatsRow data', () => {
    render(
      <BacktestStatsRow
        totalBacktests={10}
        completedBacktests={7}
        runningJobs={2}
        avgReturn={12.5}
      />
    );

    expect(screen.getByText('10')).toBeInTheDocument();
    expect(screen.getByText('+12.5%')).toBeInTheDocument();
  });

  it('triggers CapitalRiskFields onChange handlers', () => {
    const handleChange = vi.fn();
    render(
      <CapitalRiskFields
        config={{
          initial_capital: 100000,
          position_size: 2,
          commission: 0.0005,
          slippage: 0.0002,
          start_date: '2024-01-01',
          end_date: '2024-02-01',
        }}
        errors={{}}
        onChange={handleChange}
      />
    );

    fireEvent.change(screen.getByLabelText('Initial Capital'), { target: { value: '200000' } });
    fireEvent.change(screen.getByLabelText('Position Size (Lots)'), { target: { value: '3' } });
    fireEvent.change(screen.getByLabelText('Commission (%)'), { target: { value: '0.5' } });
    fireEvent.change(screen.getByLabelText('Slippage (%)'), { target: { value: '0.25' } });

    expect(handleChange).toHaveBeenCalledWith('initial_capital', 200000);
    expect(handleChange).toHaveBeenCalledWith('position_size', 3);
    expect(handleChange).toHaveBeenCalledWith('commission', 0.005);
    expect(handleChange).toHaveBeenCalledWith('slippage', 0.0025);
  });

  it('updates ParametersGrid entries', () => {
    const handleParamsChange = vi.fn();
    const schema = [
      { name: 'lookback', type: 'int', default: 10, min: 5, max: 30 },
      { name: 'use_stop', type: 'bool', default: false },
      { name: 'mode', type: 'select', default: 'aggressive', options: ['aggressive', 'conservative'] },
    ];

    render(
      <ParametersGrid
        schema={schema as any}
        parameters={{ lookback: 10, use_stop: false, mode: 'aggressive' }}
        errors={{}}
        onChange={handleParamsChange}
      />
    );

    fireEvent.change(screen.getByLabelText('lookback'), { target: { value: '12' } });
    fireEvent.click(screen.getByLabelText('use_stop'));
    const modeSelect = screen.getByRole('combobox');
    fireEvent.change(modeSelect, { target: { value: 'conservative' } });

    expect(handleParamsChange).toHaveBeenCalledTimes(3);
  });

  it('filters and selects StrategyPicker option', () => {
    const handleSelect = vi.fn();
    render(<StrategyPicker strategies={[createStrategy({ name: 'Momentum', is_active: true })]} value={null} onSelect={handleSelect} />);

    const input = screen.getByPlaceholderText('Search strategies...');
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'Mom' } });
    fireEvent.click(screen.getByText('Momentum'));

    expect(handleSelect).toHaveBeenCalled();
  });

  it('filters and selects DatasetPicker option', () => {
    const handleSelect = vi.fn();
    render(<DatasetPicker datasets={mockDatasets} value={null} onSelect={handleSelect} />);

    const input = screen.getByPlaceholderText('Search datasets...');
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'GBP' } });
    fireEvent.click(screen.getByText('GBPUSD Hourly'));

    expect(handleSelect).toHaveBeenCalledWith(mockDatasets[1]);
  });

  it('submits BacktestConfigForm successfully', () => {
    const handleSubmit = vi.fn();
    const handleCancel = vi.fn();

    render(<BacktestConfigForm onSubmit={handleSubmit} onCancel={handleCancel} />);

    const strategyInput = screen.getByPlaceholderText('Search strategies...');
    fireEvent.focus(strategyInput);
    fireEvent.click(screen.getByText('Sample Strategy'));

    const datasetInput = screen.getByPlaceholderText('Search datasets...');
    fireEvent.focus(datasetInput);
    fireEvent.click(screen.getByText('EURUSD Hourly'));

    fireEvent.change(screen.getByLabelText('lookback'), { target: { value: '12' } });

    fireEvent.click(screen.getByRole('button', { name: /Start Backtest/ }));

    expect(handleSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        strategy_id: 'strategy-1',
        dataset_id: 'dataset-1',
        parameters: expect.objectContaining({ lookback: 12 }),
      })
    );
  });

  it('shows validation error when submitting incomplete form', () => {
    const handleSubmit = vi.fn();
    render(<BacktestConfigForm onSubmit={handleSubmit} onCancel={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: /Start Backtest/ }));

    expect(handleSubmit).not.toHaveBeenCalled();
    expect(toastMock.error).toHaveBeenCalled();
  });
});
