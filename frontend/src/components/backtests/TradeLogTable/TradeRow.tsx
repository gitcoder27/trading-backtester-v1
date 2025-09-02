import React from 'react';
import { format } from 'date-fns';
import Badge from '../../ui/Badge';
import type { Trade } from './types';

interface TradeRowProps {
  trade: Trade;
  index: number;
}

const TradeRow: React.FC<TradeRowProps> = ({ trade, index }) => {
  return (
    <tr 
      key={trade.id || index}
      className="hover:bg-gray-50 dark:hover:bg-gray-800/50"
    >
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
        {trade.entry_time ? format(new Date(trade.entry_time), 'MMM dd, HH:mm') : '-'}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
        {trade.exit_time ? format(new Date(trade.exit_time), 'MMM dd, HH:mm') : '-'}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">
        {trade.symbol || '-'}
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <Badge 
          variant={trade.side === 'buy' ? 'success' : 'danger'}
          size="sm"
        >
          {trade.side ? trade.side.toUpperCase() : '-'}
        </Badge>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900 dark:text-gray-100">
        {trade.entry_price ? `₹${trade.entry_price.toFixed(2)}` : '-'}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900 dark:text-gray-100">
        {trade.exit_price ? `₹${trade.exit_price.toFixed(2)}` : '-'}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900 dark:text-gray-100">
        {trade.quantity || '-'}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium">
        <span className={trade.pnl > 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
          {trade.pnl ? `₹${trade.pnl.toFixed(2)}` : '-'}
        </span>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900 dark:text-gray-100">
        {trade.duration ? `${Math.round(trade.duration)}m` : '-'}
      </td>
    </tr>
  );
};

export default TradeRow;
