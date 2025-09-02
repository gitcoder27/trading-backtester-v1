import React from 'react';
import { Target, Clock, HelpCircle } from 'lucide-react';
import type { EnhancedBacktestConfig } from './types';

interface ExecutionSectionProps {
  config: EnhancedBacktestConfig;
  onConfigChange: (key: keyof EnhancedBacktestConfig, value: any) => void;
}

const ExecutionSection: React.FC<ExecutionSectionProps> = ({
  config,
  onConfigChange
}) => {
  return (
    <div className="space-y-6">
      {/* Portfolio Settings */}
      <div className="space-y-4">
        <h4 className="font-medium text-gray-900 dark:text-white flex items-center">
          <Target className="w-4 h-4 mr-2" />
          Portfolio & Risk Settings
        </h4>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Initial Cash
            </label>
            <input
              type="number"
              value={config.initial_capital}
              onChange={(e) => onConfigChange('initial_capital', parseFloat(e.target.value))}
              min={1000}
              step={1000}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Daily Profit Target
            </label>
            <input
              type="number"
              value={config.daily_profit_target}
              onChange={(e) => onConfigChange('daily_profit_target', parseFloat(e.target.value))}
              min={0}
              step={10}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            />
          </div>
        </div>
      </div>

      {/* Option Settings */}
      <div className="space-y-4">
        <h4 className="font-medium text-gray-900 dark:text-white">Option Trading Settings</h4>
        
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              <span className="flex items-center">
                Option Delta
                <div className="group relative ml-1">
                  <HelpCircle className="w-3 h-3 text-gray-400 cursor-help" />
                  <div className="absolute left-0 bottom-full mb-1 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
                    0.5 for ATM, 0.7 for ITM
                  </div>
                </div>
              </span>
            </label>
            <input
              type="number"
              value={config.option_delta}
              onChange={(e) => onConfigChange('option_delta', parseFloat(e.target.value))}
              min={0.1}
              max={1.0}
              step={0.05}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Lots (1 lot = 75 units)
            </label>
            <input
              type="number"
              value={config.lots}
              onChange={(e) => onConfigChange('lots', parseInt(e.target.value))}
              min={1}
              max={100}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Price Per Unit
            </label>
            <input
              type="number"
              value={config.option_price_per_unit}
              onChange={(e) => onConfigChange('option_price_per_unit', parseFloat(e.target.value))}
              min={0.1}
              step={0.1}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            />
          </div>
        </div>
      </div>

      {/* Trading Session */}
      <div className="space-y-4">
        <h4 className="font-medium text-gray-900 dark:text-white flex items-center">
          <Clock className="w-4 h-4 mr-2" />
          Trading Session
        </h4>
        
        <div className="flex items-center space-x-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={config.intraday_mode}
              onChange={(e) => onConfigChange('intraday_mode', e.target.checked)}
              className="mr-2"
            />
            <span className="text-sm text-gray-700 dark:text-gray-300">
              Intraday mode (auto-exit at session close)
            </span>
          </label>
          
          {config.intraday_mode && (
            <div className="flex items-center space-x-2">
              <label className="text-sm text-gray-700 dark:text-gray-300">Session close:</label>
              <input
                type="time"
                value={config.session_close_time}
                onChange={(e) => onConfigChange('session_close_time', e.target.value)}
                className="px-2 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm dark:bg-gray-700 dark:text-white"
              />
            </div>
          )}
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Fee Per Trade
          </label>
          <input
            type="number"
            value={config.fee_per_trade}
            onChange={(e) => onConfigChange('fee_per_trade', parseFloat(e.target.value))}
            min={0}
            step={1}
            className="w-32 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
          />
        </div>
      </div>
    </div>
  );
};

export default ExecutionSection;
