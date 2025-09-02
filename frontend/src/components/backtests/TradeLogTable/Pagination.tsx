import React from 'react';
import Button from '../../ui/Button';
import type { PaginationProps } from './types';

const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  pageSize,
  onPageChange,
  onPageSizeChange
}) => {
  if (totalPages <= 1) return null;

  return (
    <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600 dark:text-gray-400">Page size:</span>
          <select
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            className="border border-gray-300 dark:border-gray-600 rounded px-2 py-1 text-sm
                       bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
          >
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
            <option value={200}>200</option>
          </select>
        </div>

        <div className="flex items-center space-x-2">
          <Button
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage <= 1}
            variant="outline"
            size="sm"
          >
            Previous
          </Button>
          
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Page {currentPage} of {totalPages}
          </span>
          
          <Button
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage >= totalPages}
            variant="outline"
            size="sm"
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Pagination;
