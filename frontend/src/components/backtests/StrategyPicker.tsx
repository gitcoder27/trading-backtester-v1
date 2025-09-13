import React, { useMemo, useState } from 'react';
import { Search, CheckCircle } from 'lucide-react';
import Badge from '../ui/Badge';
import type { Strategy } from '../../types';

interface Props {
  strategies: Strategy[];
  value: Strategy | null;
  onSelect: (strategy: Strategy) => void;
  error?: string;
}

const StrategyPicker: React.FC<Props> = ({ strategies, value, onSelect, error }) => {
  const [search, setSearch] = useState('');
  const [open, setOpen] = useState(false);

  const filtered = useMemo(
    () => strategies.filter((s) => s.is_active && s.name.toLowerCase().includes(search.toLowerCase())),
    [strategies, search]
  );

  return (
    <div className="space-y-3">
      <div className="relative">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search strategies..."
            value={value ? value.name : search}
            onChange={(e) => {
              setSearch(e.target.value);
            }}
            onFocus={() => setOpen(true)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
          />
        </div>
        {open && (
          <div className="absolute z-10 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-lg max-h-60 overflow-auto">
            {filtered.length === 0 ? (
              <div className="p-3 text-gray-500 dark:text-gray-400 text-sm">No strategies found</div>
            ) : (
              filtered.map((strategy) => (
                <div
                  key={strategy.id}
                  onClick={() => {
                    onSelect(strategy);
                    setOpen(false);
                    setSearch('');
                  }}
                  className="p-3 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer border-b border-gray-100 dark:border-gray-700 last:border-b-0"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-gray-900 dark:text-gray-100">{strategy.name}</div>
                      {strategy.description && (
                        <div className="text-sm text-gray-500 dark:text-gray-400">{strategy.description}</div>
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

      {value && (
        <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md">
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-4 h-4 text-green-600" />
            <span className="text-sm font-medium text-green-800 dark:text-green-200">Selected: {value.name}</span>
          </div>
        </div>
      )}

      {error && (
        <div className="text-red-600 text-sm">{error}</div>
      )}
    </div>
  );
};

export default StrategyPicker;

