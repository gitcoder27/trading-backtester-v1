import React from 'react';
import { Search, Filter } from 'lucide-react';

type FilterType = 'all' | 'active' | 'inactive';

interface Props {
  search: string;
  onSearchChange: (val: string) => void;
  filter: FilterType;
  onFilterChange: (val: FilterType) => void;
}

const StrategiesToolbar: React.FC<Props> = ({ search, onSearchChange, filter, onFilterChange }) => {
  return (
    <div className="flex flex-col sm:flex-row gap-4">
      <div className="flex-1 relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search strategies..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
        />
      </div>
      <div className="flex items-center space-x-2">
        <Filter className="h-4 w-4 text-gray-400" />
        <select
          value={filter}
          onChange={(e) => onFilterChange(e.target.value as FilterType)}
          className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
        >
          <option value="all">All Strategies</option>
          <option value="active">Active Only</option>
          <option value="inactive">Inactive Only</option>
        </select>
      </div>
    </div>
  );
};

export default StrategiesToolbar;

