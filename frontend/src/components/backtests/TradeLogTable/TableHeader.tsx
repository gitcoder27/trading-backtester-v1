import React from 'react';
import { Download, Filter, Search, TrendingUp, TrendingDown } from 'lucide-react';
import Button from '../../ui/Button';
import type { TableHeaderProps } from './types';

const TableHeader: React.FC<TableHeaderProps> = ({
  onExportCSV,
  hasData,
  searchTerm,
  onSearchChange,
  filterProfitable,
  onFilterChange,
  totalTrades,
  currentPage,
  pageSize,
  winningTrades,
  losingTrades
}) => {
  return (
    <div className="p-6 border-b border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Trade Log
        </h3>
        <div className="flex items-center space-x-2">
          <Button
            onClick={onExportCSV}
            variant="outline"
            size="sm"
            disabled={!hasData}
          >
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-wrap items-center gap-4">
        {/* Search */}
        <div className="relative flex-1 min-w-64">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search trades..."
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 
                       rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                       focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Profit Filter */}
        <div className="flex items-center space-x-2">
          <Filter className="h-4 w-4 text-gray-500" />
          <div className="flex space-x-1">
            <Button
              onClick={() => onFilterChange(undefined)}
              variant={filterProfitable === undefined ? "primary" : "outline"}
              size="sm"
            >
              All
            </Button>
            <Button
              onClick={() => onFilterChange(true)}
              variant={filterProfitable === true ? "primary" : "outline"}
              size="sm"
            >
              <TrendingUp className="h-3 w-3 mr-1" />
              Winners
            </Button>
            <Button
              onClick={() => onFilterChange(false)}
              variant={filterProfitable === false ? "primary" : "outline"}
              size="sm"
            >
              <TrendingDown className="h-3 w-3 mr-1" />
              Losers
            </Button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="flex items-center justify-between mt-4 text-sm text-gray-600 dark:text-gray-400">
        <span>
          Showing {((currentPage - 1) * pageSize) + 1}-{Math.min(currentPage * pageSize, totalTrades)} of {totalTrades} trades
        </span>
        <div className="flex items-center space-x-4">
          <span>Winners: {winningTrades}</span>
          <span>Losers: {losingTrades}</span>
        </div>
      </div>
    </div>
  );
};

export default TableHeader;
