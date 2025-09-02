import React from 'react';
import { Search, Filter } from 'lucide-react';
import Card from '../../ui/Card';
import Input from '../../ui/Input';
import type { JobFiltersProps } from './types';

const JobFilters: React.FC<JobFiltersProps> = ({
  searchTerm,
  onSearchChange,
  statusFilter,
  onStatusFilterChange,
  sortBy,
  sortOrder,
  onSortChange
}) => {
  const handleSortChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const [field, order] = e.target.value.split('-');
    onSortChange(field as 'created_at' | 'status' | 'type', order as 'asc' | 'desc');
  };

  return (
    <Card className="p-4">
      <div className="flex flex-col md:flex-row md:items-center space-y-4 md:space-y-0 md:space-x-4">
        <div className="flex-1">
          <Input
            placeholder="Search jobs..."
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            icon={Search}
          />
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <select
              value={statusFilter}
              onChange={(e) => onStatusFilterChange(e.target.value as any)}
              className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="running">Running</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-500">Sort by:</span>
            <select
              value={`${sortBy}-${sortOrder}`}
              onChange={handleSortChange}
              className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
            >
              <option value="created_at-desc">Newest First</option>
              <option value="created_at-asc">Oldest First</option>
              <option value="status-asc">Status A-Z</option>
              <option value="status-desc">Status Z-A</option>
              <option value="type-asc">Type A-Z</option>
              <option value="type-desc">Type Z-A</option>
            </select>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default JobFilters;
