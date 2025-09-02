import React from 'react';
import { Filter } from 'lucide-react';
import type { EnhancedBacktestConfig } from './types';

interface FiltersSectionProps {
  config: EnhancedBacktestConfig;
  onConfigChange: (key: keyof EnhancedBacktestConfig, value: any) => void;
}

const FiltersSection: React.FC<FiltersSectionProps> = ({
  config,
  onConfigChange
}) => {
  return (
    <div className="space-y-6">
      {/* Direction Filter */}
      <div className="space-y-3">
        <h4 className="font-medium text-gray-900 dark:text-white flex items-center">
          <Filter className="w-4 h-4 mr-2" />
          Direction Filter
        </h4>
        <div className="flex space-x-4">
          {['long', 'short'].map(direction => (
            <label key={direction} className="flex items-center">
              <input
                type="checkbox"
                checked={config.direction_filter.includes(direction)}
                onChange={(e) => {
                  if (e.target.checked) {
                    onConfigChange('direction_filter', [...config.direction_filter, direction]);
                  } else {
                    onConfigChange('direction_filter', config.direction_filter.filter(d => d !== direction));
                  }
                }}
                className="mr-2"
              />
              <span className="text-sm text-gray-700 dark:text-gray-300 capitalize">{direction}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Time Filter */}
      <div className="space-y-3">
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={config.apply_time_filter}
            onChange={(e) => onConfigChange('apply_time_filter', e.target.checked)}
            className="mr-2"
          />
          <span className="font-medium text-gray-900 dark:text-white">Trading Hours Filter</span>
        </label>
        
        {config.apply_time_filter && (
          <div className="flex items-center space-x-4 ml-6">
            <div>
              <label className="block text-sm text-gray-700 dark:text-gray-300 mb-1">Start Hour</label>
              <input
                type="number"
                value={config.start_hour}
                onChange={(e) => onConfigChange('start_hour', parseInt(e.target.value))}
                min={0}
                max={23}
                className="w-20 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm dark:bg-gray-700 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-700 dark:text-gray-300 mb-1">End Hour</label>
              <input
                type="number"
                value={config.end_hour}
                onChange={(e) => onConfigChange('end_hour', parseInt(e.target.value))}
                min={0}
                max={23}
                className="w-20 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm dark:bg-gray-700 dark:text-white"
              />
            </div>
          </div>
        )}
      </div>

      {/* Weekday Filter */}
      <div className="space-y-3">
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={config.apply_weekday_filter}
            onChange={(e) => onConfigChange('apply_weekday_filter', e.target.checked)}
            className="mr-2"
          />
          <span className="font-medium text-gray-900 dark:text-white">Weekday Filter</span>
        </label>
        
        {config.apply_weekday_filter && (
          <div className="ml-6 space-y-2">
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">Select trading days:</div>
            <div className="flex flex-wrap gap-2">
              {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day, index) => (
                <label key={day} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={config.weekdays.includes(index)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        onConfigChange('weekdays', [...config.weekdays, index]);
                      } else {
                        onConfigChange('weekdays', config.weekdays.filter(d => d !== index));
                      }
                    }}
                    className="mr-1"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">{day}</span>
                </label>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FiltersSection;
