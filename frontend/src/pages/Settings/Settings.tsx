import React, { useEffect, useMemo, useState } from 'react';
import { Layers, Database, Trash2, SlidersHorizontal, Settings as SettingsIcon, Clock } from 'lucide-react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import Modal from '../../components/ui/Modal';
import { showToast } from '../../components/ui/Toast';
import { useSettingsStore } from '../../stores/settingsStore';
import { AdminService, type MaintenanceResponse } from '../../services/admin';

type DefaultsFormField =
  | 'default_initial_capital'
  | 'default_lot_size'
  | 'default_commission'
  | 'default_fee_per_trade'
  | 'default_slippage'
  | 'default_daily_profit_target'
  | 'default_option_delta'
  | 'default_option_price_per_unit'
  | 'default_start_hour'
  | 'default_end_hour';

interface DefaultsFormState {
  default_initial_capital: string;
  default_lot_size: string;
  default_commission: string;
  default_fee_per_trade: string;
  default_slippage: string;
  default_daily_profit_target: string;
  default_option_delta: string;
  default_option_price_per_unit: string;
  default_intraday_mode: boolean;
  default_session_close_time: string;
  default_direction_filter: Array<'long' | 'short'>;
  default_apply_time_filter: boolean;
  default_start_hour: string;
  default_end_hour: string;
  default_apply_weekday_filter: boolean;
  default_weekdays: number[];
}

type MaintenanceActionKey = 'backtests' | 'datasets' | 'jobs';

interface MaintenanceAction {
  key: MaintenanceActionKey;
  title: string;
  description: string;
  buttonLabel: string;
  icon: React.ComponentType<{ className?: string }>;
  confirmMessage: string;
  execute: () => Promise<MaintenanceResponse>;
  emphasis?: 'primary' | 'warning';
}

const numericFormatter = new Intl.NumberFormat('en-IN');

const SettingsPage: React.FC = () => {
  const {
    default_initial_capital,
    default_lot_size,
    default_commission,
    default_fee_per_trade,
    default_slippage,
    default_daily_profit_target,
    default_option_delta,
    default_option_price_per_unit,
    default_intraday_mode,
    default_session_close_time,
    default_direction_filter,
    default_apply_time_filter,
    default_start_hour,
    default_end_hour,
    default_apply_weekday_filter,
    default_weekdays,
    updatePreferences,
    resetToDefaults,
  } = useSettingsStore();

  const [formState, setFormState] = useState<DefaultsFormState>({
    default_initial_capital: default_initial_capital.toString(),
    default_lot_size: default_lot_size.toString(),
    default_commission: default_commission.toString(),
    default_fee_per_trade: default_fee_per_trade.toString(),
    default_slippage: default_slippage.toString(),
    default_daily_profit_target: default_daily_profit_target.toString(),
    default_option_delta: default_option_delta.toString(),
    default_option_price_per_unit: default_option_price_per_unit.toString(),
    default_intraday_mode: default_intraday_mode,
    default_session_close_time: default_session_close_time,
    default_direction_filter: [...default_direction_filter],
    default_apply_time_filter: default_apply_time_filter,
    default_start_hour: default_start_hour.toString(),
    default_end_hour: default_end_hour.toString(),
    default_apply_weekday_filter: default_apply_weekday_filter,
    default_weekdays: [...default_weekdays],
  });

  const [isSaving, setIsSaving] = useState(false);
  const [pendingAction, setPendingAction] = useState<MaintenanceAction | null>(null);
  const [isProcessingAction, setIsProcessingAction] = useState(false);

  useEffect(() => {
    setFormState({
      default_initial_capital: default_initial_capital.toString(),
      default_lot_size: default_lot_size.toString(),
      default_commission: default_commission.toString(),
      default_fee_per_trade: default_fee_per_trade.toString(),
      default_slippage: default_slippage.toString(),
      default_daily_profit_target: default_daily_profit_target.toString(),
      default_option_delta: default_option_delta.toString(),
      default_option_price_per_unit: default_option_price_per_unit.toString(),
      default_intraday_mode: default_intraday_mode,
      default_session_close_time: default_session_close_time,
      default_direction_filter: [...default_direction_filter],
      default_apply_time_filter: default_apply_time_filter,
      default_start_hour: default_start_hour.toString(),
      default_end_hour: default_end_hour.toString(),
      default_apply_weekday_filter: default_apply_weekday_filter,
      default_weekdays: [...default_weekdays],
    });
  }, [
    default_initial_capital,
    default_lot_size,
    default_commission,
    default_fee_per_trade,
    default_slippage,
    default_daily_profit_target,
    default_option_delta,
    default_option_price_per_unit,
    default_intraday_mode,
    default_session_close_time,
    default_direction_filter,
    default_apply_time_filter,
    default_start_hour,
    default_end_hour,
    default_apply_weekday_filter,
    default_weekdays,
  ]);

  const handleFieldChange = (field: DefaultsFormField) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setFormState((prev) => ({
      ...prev,
      [field]: event.target.value,
    }));
  };

  const handleToggleIntraday = (checked: boolean) => {
    setFormState((prev) => ({
      ...prev,
      default_intraday_mode: checked,
    }));
  };

  const handleSessionCloseTimeChange = (value: string) => {
    setFormState((prev) => ({
      ...prev,
      default_session_close_time: value,
    }));
  };

  const handleToggleDirection = (direction: 'long' | 'short') => {
    setFormState((prev) => {
      const exists = prev.default_direction_filter.includes(direction);
      const next = exists
        ? prev.default_direction_filter.filter((item) => item !== direction)
        : [...prev.default_direction_filter, direction];
      return {
        ...prev,
        default_direction_filter: next,
      };
    });
  };

  const handleToggleTimeFilter = (checked: boolean) => {
    setFormState((prev) => ({
      ...prev,
      default_apply_time_filter: checked,
    }));
  };

  const handleToggleWeekdayFilter = (checked: boolean) => {
    setFormState((prev) => ({
      ...prev,
      default_apply_weekday_filter: checked,
      default_weekdays: checked && prev.default_weekdays.length === 0 ? [0, 1, 2, 3, 4] : prev.default_weekdays,
    }));
  };

  const handleToggleWeekday = (weekday: number) => {
    setFormState((prev) => {
      const exists = prev.default_weekdays.includes(weekday);
      const next = exists
        ? prev.default_weekdays.filter((day) => day !== weekday)
        : [...prev.default_weekdays, weekday];
      return {
        ...prev,
        default_weekdays: next,
      };
    });
  };

  const parsedDefaults = useMemo(() => {
    const capital = Number(formState.default_initial_capital);
    const lots = Number(formState.default_lot_size);
    const commission = Number(formState.default_commission);
    const feePerTrade = Number(formState.default_fee_per_trade);
    const slippage = Number(formState.default_slippage);
    const dailyProfit = Number(formState.default_daily_profit_target);
    const optionDelta = Number(formState.default_option_delta);
    const optionPricePerUnit = Number(formState.default_option_price_per_unit);
    const startHour = Number(formState.default_start_hour);
    const endHour = Number(formState.default_end_hour);

    const timeFilterInvalid = formState.default_apply_time_filter && (
      Number.isNaN(startHour) ||
      Number.isNaN(endHour) ||
      startHour < 0 ||
      endHour < 0 ||
      startHour > 23 ||
      endHour > 23 ||
      endHour < startHour
    );

    const directionInvalid = formState.default_direction_filter.length === 0;
    const weekdayInvalid = formState.default_apply_weekday_filter && formState.default_weekdays.length === 0;

    return {
      capital,
      lots,
      commission,
      feePerTrade,
      slippage,
      dailyProfit,
      optionDelta,
      optionPricePerUnit,
      startHour,
      endHour,
      hasInvalid:
        Number.isNaN(capital) ||
        Number.isNaN(lots) ||
        Number.isNaN(commission) ||
        Number.isNaN(feePerTrade) ||
        Number.isNaN(slippage) ||
        Number.isNaN(dailyProfit) ||
        Number.isNaN(optionDelta) ||
        Number.isNaN(optionPricePerUnit) ||
        capital <= 0 ||
        lots <= 0 ||
        optionDelta <= 0 ||
        optionPricePerUnit <= 0 ||
        dailyProfit < 0 ||
        feePerTrade < 0 ||
        slippage < 0 ||
        timeFilterInvalid || directionInvalid || weekdayInvalid,
    };
  }, [formState]);

  const handleSaveDefaults = async () => {
    if (parsedDefaults.hasInvalid) {
      showToast.error('Please review your defaults. Ensure numeric values are valid and required selections are set.');
      return;
    }

    try {
      setIsSaving(true);
      const normalizedWeekdays = [...formState.default_weekdays].sort((a, b) => a - b);
      updatePreferences({
        default_initial_capital: parsedDefaults.capital,
        default_lot_size: parsedDefaults.lots,
        default_commission: parsedDefaults.commission,
        default_fee_per_trade: parsedDefaults.feePerTrade,
        default_slippage: parsedDefaults.slippage,
        default_daily_profit_target: parsedDefaults.dailyProfit,
        default_option_delta: parsedDefaults.optionDelta,
        default_option_price_per_unit: parsedDefaults.optionPricePerUnit,
        default_intraday_mode: formState.default_intraday_mode,
        default_session_close_time: formState.default_session_close_time,
        default_direction_filter: [...formState.default_direction_filter],
        default_apply_time_filter: formState.default_apply_time_filter,
        default_start_hour: parsedDefaults.startHour,
        default_end_hour: parsedDefaults.endHour,
        default_apply_weekday_filter: formState.default_apply_weekday_filter,
        default_weekdays: normalizedWeekdays,
      });
      showToast.success('Backtesting defaults updated.');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to update defaults';
      showToast.error(message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleResetDefaults = () => {
    resetToDefaults();
    showToast.success('Defaults restored.');
  };

  const maintenanceActions: MaintenanceAction[] = useMemo(
    () => [
      {
        key: 'backtests',
        title: 'Clear Backtests',
        description: 'Remove all stored backtest runs, metrics, and trade logs. Use this before starting with a new dataset or strategy.',
        buttonLabel: 'Clear Backtests',
        icon: Layers,
        confirmMessage:
          'This will permanently delete all backtest results, metrics, and trade logs. This action cannot be undone. Proceed?',
        execute: AdminService.clearBacktests,
        emphasis: 'warning',
      },
      {
        key: 'datasets',
        title: 'Clear Datasets',
        description: 'Delete every dataset record and associated files stored on disk to free up space.',
        buttonLabel: 'Clear Datasets',
        icon: Database,
        confirmMessage:
          'All dataset metadata and local files will be removed. Make sure you have backups before continuing.',
        execute: AdminService.clearDatasets,
        emphasis: 'warning',
      },
      {
        key: 'jobs',
        title: 'Clear Job Queue',
        description: 'Remove historical background jobs and reset the queue of completed, failed, or pending backtests.',
        buttonLabel: 'Clear Jobs',
        icon: Trash2,
        confirmMessage:
          'This will remove all background job entries. Running jobs will not be stopped automatically. Are you sure?',
        execute: AdminService.clearJobs,
      },
    ],
    []
  );

  const handleExecuteMaintenance = async () => {
    if (!pendingAction) return;
    try {
      setIsProcessingAction(true);
      const response = await pendingAction.execute();
      const message = response.message ?? `${pendingAction.title} completed.`;
      showToast.success(message);
    } catch (error) {
      const message = error instanceof Error ? error.message : `Failed to ${pendingAction.buttonLabel.toLowerCase()}`;
      showToast.error(message);
    } finally {
      setIsProcessingAction(false);
      setPendingAction(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Settings</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Configure default backtesting parameters and manage maintenance tasks.
          </p>
        </div>
      </div>

      <Card className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <SlidersHorizontal className="h-5 w-5 text-primary-400" />
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Backtesting Defaults</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              These values pre-fill new backtest configurations. Adjust them to match your typical session setup.
            </p>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <Input
            label="Initial Capital"
            type="number"
            min="1"
            step="1000"
            value={formState.default_initial_capital}
            onChange={handleFieldChange('default_initial_capital')}
            helpText={`Current default: ₹${numericFormatter.format(default_initial_capital)}`}
          />
          <Input
            label="Lot Size"
            type="number"
            min="1"
            step="1"
            value={formState.default_lot_size}
            onChange={handleFieldChange('default_lot_size')}
            helpText={`Current default: ${numericFormatter.format(default_lot_size)} lot(s)`}
          />
          <Input
            label="Per-trade Fee (absolute)"
            type="number"
            min="0"
            step="0.1"
            value={formState.default_fee_per_trade}
            onChange={handleFieldChange('default_fee_per_trade')}
            helpText={`Current default: ${default_fee_per_trade}`}
          />
          <Input
            label="Slippage"
            type="number"
            min="0"
            step="0.0001"
            value={formState.default_slippage}
            onChange={handleFieldChange('default_slippage')}
            helpText={`Current default: ${default_slippage}`}
          />
          <Input
            label="Commission (%)"
            type="number"
            min="0"
            step="0.0001"
            value={formState.default_commission}
            onChange={handleFieldChange('default_commission')}
            helpText={`Current default: ${default_commission}`}
          />
          <Input
            label="Daily Profit Target"
            type="number"
            min="0"
            step="1"
            value={formState.default_daily_profit_target}
            onChange={handleFieldChange('default_daily_profit_target')}
            helpText={`Current default: ${default_daily_profit_target}`}
          />
        </div>

        <div className="mt-6">
          <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-2 mb-4">
            <SettingsIcon className="h-4 w-4" /> Option Defaults
          </h3>
          <div className="grid gap-4 md:grid-cols-2">
            <Input
              label="Option Delta"
              type="number"
              min="0.1"
              max="1"
              step="0.05"
              value={formState.default_option_delta}
              onChange={handleFieldChange('default_option_delta')}
              helpText={`Current default: ${default_option_delta}`}
            />
            <Input
              label="Option Price per Unit"
              type="number"
              min="0.1"
              step="0.1"
              value={formState.default_option_price_per_unit}
              onChange={handleFieldChange('default_option_price_per_unit')}
              helpText={`Current default: ${default_option_price_per_unit}`}
            />
          </div>
        </div>

        <div className="mt-6 space-y-4">
          <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-2">
            <Clock className="h-4 w-4" /> Session Behaviour
          </h3>
          <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
            <input
              type="checkbox"
              checked={formState.default_intraday_mode}
              onChange={(e) => handleToggleIntraday(e.target.checked)}
            />
            Intraday mode (auto exit at session close)
          </label>
          {formState.default_intraday_mode && (
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-600 dark:text-gray-400">Session close time:</span>
              <input
                type="time"
                value={formState.default_session_close_time}
                onChange={(e) => handleSessionCloseTimeChange(e.target.value)}
                className="rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-2 py-1 text-sm text-gray-800 dark:text-gray-100"
              />
            </div>
          )}

          <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
            <input
              type="checkbox"
              checked={formState.default_apply_time_filter}
              onChange={(e) => handleToggleTimeFilter(e.target.checked)}
            />
            Apply trading hours filter
          </label>
          {formState.default_apply_time_filter && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pl-6">
              <Input
                label="Start hour"
                type="number"
                min="0"
                max="23"
                step="1"
                value={formState.default_start_hour}
                onChange={handleFieldChange('default_start_hour')}
                helpText="0 - 23"
              />
              <Input
                label="End hour"
                type="number"
                min="0"
                max="23"
                step="1"
                value={formState.default_end_hour}
                onChange={handleFieldChange('default_end_hour')}
                helpText="Must be greater than start hour"
              />
            </div>
          )}
        </div>

        <div className="mt-6 space-y-3">
          <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200">Direction Filter</h3>
          <div className="flex flex-wrap gap-4">
            {(['long', 'short'] as Array<'long' | 'short'>).map((direction) => {
              const checked = formState.default_direction_filter.includes(direction);
              return (
                <label key={direction} className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => handleToggleDirection(direction)}
                  />
                  {direction.toUpperCase()}
                </label>
              );
            })}
          </div>
          {formState.default_direction_filter.length === 0 && (
            <p className="text-xs text-red-500">Select at least one direction.</p>
          )}
        </div>

        <div className="mt-6 space-y-3">
          <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
            <input
              type="checkbox"
              checked={formState.default_apply_weekday_filter}
              onChange={(e) => handleToggleWeekdayFilter(e.target.checked)}
            />
            Apply weekday filter
          </label>
          {formState.default_apply_weekday_filter && (
            <div className="pl-6 space-y-2">
              <div className="text-xs text-gray-500 dark:text-gray-400">Select active trading days</div>
              <div className="flex flex-wrap gap-3">
                {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((label, index) => {
                  const checked = formState.default_weekdays.includes(index);
                  return (
                    <label key={label} className="flex items-center gap-1 text-sm text-gray-700 dark:text-gray-300">
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => handleToggleWeekday(index)}
                      />
                      {label}
                    </label>
                  );
                })}
              </div>
              {formState.default_weekdays.length === 0 && (
                <p className="text-xs text-red-500">Choose at least one weekday.</p>
              )}
            </div>
          )}
        </div>

        <div className="mt-6 flex flex-wrap items-center gap-3">
          <Button
            variant="primary"
            size="md"
            onClick={handleSaveDefaults}
            disabled={isSaving}
          >
            {isSaving ? 'Saving…' : 'Save Defaults'}
          </Button>
          <Button
            variant="outline"
            size="md"
            onClick={handleResetDefaults}
          >
            Restore Defaults
          </Button>
        </div>
      </Card>

      <Card className="p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">Data Maintenance</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
          Clean up stored records to keep the workspace light. These operations are irreversible, so proceed with caution.
        </p>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {maintenanceActions.map((action) => {
            const Icon = action.icon;
            return (
              <div
                key={action.key}
                className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-5 shadow-sm"
              >
                <div className="flex items-start gap-3">
                  <div className="rounded-lg bg-primary-500/10 p-2 text-primary-500 dark:text-primary-300">
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100">{action.title}</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{action.description}</p>
                  </div>
                </div>
                <Button
                  variant={action.emphasis === 'warning' ? 'danger' : 'outline'}
                  size="sm"
                  className="mt-4"
                  onClick={() => setPendingAction(action)}
                >
                  {action.buttonLabel}
                </Button>
              </div>
            );
          })}
        </div>
      </Card>

      <Modal
        isOpen={pendingAction !== null}
        onClose={() => (isProcessingAction ? undefined : setPendingAction(null))}
        title={pendingAction?.title ?? ''}
      >
        <p className="text-sm text-gray-600 dark:text-gray-300">{pendingAction?.confirmMessage}</p>
        <div className="mt-6 flex justify-end gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPendingAction(null)}
            disabled={isProcessingAction}
          >
            Cancel
          </Button>
          <Button
            variant="danger"
            size="sm"
            onClick={handleExecuteMaintenance}
            disabled={isProcessingAction}
          >
            {isProcessingAction ? 'Processing…' : 'Confirm'}
          </Button>
        </div>
      </Modal>
    </div>
  );
};

export default SettingsPage;
