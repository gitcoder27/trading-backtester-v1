import React from 'react';
import { ChevronUp, ChevronDown, Calendar } from 'lucide-react';
import type { SortConfig } from './types';

interface SortableTableHeaderProps extends SortConfig {
  columns: Array<{
    key: string;
    label: string;
    align?: 'left' | 'right';
    sortable?: boolean;
    icon?: React.ComponentType<{ className?: string }>;
  }>;
}

const SortIcon: React.FC<{ column: string; sortBy: string; sortOrder: 'asc' | 'desc' }> = ({ 
  column, 
  sortBy, 
  sortOrder 
}) => {
  if (sortBy !== column) {
    return <ChevronUp className="h-4 w-4 text-gray-400" />;
  }
  return sortOrder === 'asc' ? 
    <ChevronUp className="h-4 w-4 text-blue-500" /> : 
    <ChevronDown className="h-4 w-4 text-blue-500" />;
};

const SortableTableHeader: React.FC<SortableTableHeaderProps> = ({
  columns,
  sortBy,
  sortOrder,
  onSort
}) => {
  const defaultColumns = [
    { key: 'entry_time', label: 'Entry Time', align: 'left' as const, sortable: true, icon: Calendar },
    { key: 'exit_time', label: 'Exit Time', align: 'left' as const, sortable: true, icon: Calendar },
    { key: 'symbol', label: 'Symbol', align: 'left' as const, sortable: false },
    { key: 'side', label: 'Side', align: 'left' as const, sortable: false },
    { key: 'entry_price', label: 'Entry Price', align: 'right' as const, sortable: true },
    { key: 'exit_price', label: 'Exit Price', align: 'right' as const, sortable: true },
    { key: 'quantity', label: 'Qty', align: 'right' as const, sortable: true },
    { key: 'pnl', label: 'P&L', align: 'right' as const, sortable: true },
    { key: 'duration', label: 'Duration', align: 'right' as const, sortable: true },
  ];

  const columnsToUse = columns.length > 0 ? columns : defaultColumns;

  return (
    <thead className="bg-gray-50 dark:bg-gray-800/50">
      <tr>
        {columnsToUse.map((column) => (
          <th 
            key={column.key}
            className={`px-6 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider ${
              column.align === 'right' ? 'text-right' : 'text-left'
            } ${
              column.sortable ? 'cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700' : ''
            }`}
            onClick={column.sortable ? () => onSort(column.key) : undefined}
          >
            <div className={`flex items-center space-x-1 ${
              column.align === 'right' ? 'justify-end' : 'justify-start'
            }`}>
              {column.icon && <column.icon className="h-3 w-3" />}
              <span>{column.label}</span>
              {column.sortable && (
                <SortIcon column={column.key} sortBy={sortBy} sortOrder={sortOrder} />
              )}
            </div>
          </th>
        ))}
      </tr>
    </thead>
  );
};

export default SortableTableHeader;
