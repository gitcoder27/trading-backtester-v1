import React from 'react';
import type { SortField, SortOrder } from './TradeList.types';

type Alignment = 'left' | 'right';

type HeaderItem = {
  label: string;
  field: SortField;
  align?: Alignment;
};

const HEADERS: HeaderItem[] = [
  { label: 'Entry Time', field: 'entry_time' },
  { label: 'Exit Time', field: 'exit_time' },
  { label: 'Side', field: 'side' },
  { label: 'Qty', field: 'quantity', align: 'right' },
  { label: 'Entry', field: 'entry_price', align: 'right' },
  { label: 'Exit', field: 'exit_price', align: 'right' },
  { label: 'P&L', field: 'pnl', align: 'right' },
];

interface TradeListHeaderProps {
  sortField: SortField;
  sortOrder: SortOrder;
  onSort: (field: SortField) => void;
}

const TradeListHeader: React.FC<TradeListHeaderProps> = ({ sortField, sortOrder, onSort }) => {
  const renderIndicator = (field: SortField): string => {
    if (sortField !== field) return '';
    return sortOrder === 'asc' ? '↑' : '↓';
  };

  return (
    <thead className="bg-gray-50 dark:bg-gray-800">
      <tr>
        {HEADERS.map(({ label, field, align = 'left' }) => {
          const indicator = renderIndicator(field);
          const alignmentClasses = align === 'right' ? 'justify-end text-right' : 'justify-start text-left';

          return (
            <th
              key={field}
              className={`px-4 py-2 font-semibold text-gray-600 dark:text-gray-300 ${align === 'right' ? 'text-right' : 'text-left'}`}
            >
              <button
                type="button"
                onClick={() => onSort(field)}
                className={`flex items-center gap-1 w-full focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 ${alignmentClasses}`}
              >
                <span>{label}</span>
                {indicator && <span className="text-xs text-primary-500">{indicator}</span>}
              </button>
            </th>
          );
        })}
      </tr>
    </thead>
  );
};

export default TradeListHeader;
