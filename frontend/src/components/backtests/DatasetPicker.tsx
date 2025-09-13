import React, { useMemo, useState } from 'react';
import { Search, CheckCircle } from 'lucide-react';

interface DatasetItem {
  id: number | string;
  name: string;
  symbol?: string | null;
  timeframe?: string;
  rows_count?: number;
  start_date?: string;
  end_date?: string;
}

interface Props {
  datasets: DatasetItem[];
  value: DatasetItem | null;
  onSelect: (dataset: DatasetItem) => void;
  error?: string;
}

const DatasetPicker: React.FC<Props> = ({ datasets, value, onSelect, error }) => {
  const [search, setSearch] = useState('');
  const [open, setOpen] = useState(false);

  const filtered = useMemo(
    () =>
      datasets.filter(
        (d) =>
          d.name.toLowerCase().includes(search.toLowerCase()) ||
          (d.symbol && d.symbol.toLowerCase().includes(search.toLowerCase()))
      ),
    [datasets, search]
  );

  return (
    <div className="space-y-3">
      <div className="relative">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search datasets..."
            value={value ? `${value.name} (${value.symbol})` : search}
            onChange={(e) => setSearch(e.target.value)}
            onFocus={() => setOpen(true)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
          />
        </div>
        {open && (
          <div className="absolute z-10 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-lg max-h-60 overflow-auto">
            {filtered.length === 0 ? (
              <div className="p-3 text-gray-500 dark:text-gray-400 text-sm">No datasets found</div>
            ) : (
              filtered.map((dataset) => (
                <div
                  key={dataset.id}
                  onClick={() => {
                    onSelect(dataset);
                    setOpen(false);
                    setSearch('');
                  }}
                  className="p-3 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer border-b border-gray-100 dark:border-gray-700 last:border-b-0"
                >
                  <div>
                    <div className="font-medium text-gray-900 dark:text-gray-100">{dataset.name}</div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {dataset.symbol || 'No Symbol'} • {dataset.timeframe} • {dataset.rows_count?.toLocaleString?.()}
                      {dataset.rows_count != null ? ' records' : ''}
                    </div>
                    <div className="text-xs text-gray-400 dark:text-gray-500">
                      {dataset.start_date} to {dataset.end_date}
                    </div>
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
            <span className="text-sm font-medium text-green-800 dark:text-green-200">
              Selected: {value.name} ({value.symbol})
            </span>
          </div>
        </div>
      )}

      {error && <div className="text-red-600 text-sm">{error}</div>}
    </div>
  );
};

export default DatasetPicker;

