import React, { useMemo } from 'react';
import Card from '../../ui/Card';
import Button from '../../ui/Button';
import { useTradeData } from './useTradeData';
import { useExportCSV } from './ExportControls';
import TableHeader from './TableHeader';
import SortableTableHeader from './SortableTableHeader';
import TradeRow from './TradeRow';
import Pagination from './Pagination';
import type { TradeLogTableProps } from './types';

const TradeLogTable: React.FC<TradeLogTableProps> = ({ backtestId, className = '' }) => {
  const {
    data,
    isLoading,
    error,
    refetch,
    page,
    pageSize,
    sortBy,
    sortOrder,
    filterProfitable,
    searchTerm,
    handleSort,
    handleFilterChange,
    handlePageChange,
    handlePageSizeChange,
    handleSearchChange,
  } = useTradeData(backtestId);

  const { exportToCSV } = useExportCSV();

  const filteredTrades = useMemo(() => {
    if (!data?.trades || !searchTerm) return data?.trades || [];
    
    const term = searchTerm.toLowerCase();
    return data.trades.filter(trade => 
      trade.symbol?.toLowerCase().includes(term) ||
      trade.side?.toLowerCase().includes(term) ||
      trade.entry_time?.toLowerCase().includes(term)
    );
  }, [data?.trades, searchTerm]);

  const handleExportCSV = () => {
    if (data?.trades) {
      exportToCSV(data.trades, backtestId);
    }
  };

  if (error) {
    return (
      <Card className={`p-6 ${className}`}>
        <div className="text-center">
          <div className="text-red-500 text-lg font-medium mb-2">
            Failed to load trade data
          </div>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            {error.message}
          </p>
          <Button onClick={() => refetch()} variant="outline">
            Try Again
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <Card className={className}>
      {/* Header with Controls */}
      <TableHeader
        onExportCSV={handleExportCSV}
        hasData={!!data?.trades?.length}
        searchTerm={searchTerm}
        onSearchChange={handleSearchChange}
        filterProfitable={filterProfitable}
        onFilterChange={handleFilterChange}
        totalTrades={data?.total_trades || 0}
        currentPage={page}
        pageSize={pageSize}
        winningTrades={data?.trades.filter(t => t.pnl > 0).length || 0}
        losingTrades={data?.trades.filter(t => t.pnl <= 0).length || 0}
      />

      {/* Table */}
      <div className="overflow-x-auto">
        {isLoading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-2 text-gray-600 dark:text-gray-400">Loading trades...</p>
          </div>
        ) : !filteredTrades?.length ? (
          <div className="p-8 text-center">
            <p className="text-gray-600 dark:text-gray-400">No trades found</p>
          </div>
        ) : (
          <table className="w-full">
            <SortableTableHeader
              columns={[]}
              sortBy={sortBy}
              sortOrder={sortOrder}
              onSort={handleSort}
            />
            <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
              {filteredTrades.map((trade, index) => (
                <TradeRow
                  key={trade.id || index}
                  trade={trade}
                  index={index}
                />
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {data && (
        <Pagination
          currentPage={page}
          totalPages={data.total_pages}
          pageSize={pageSize}
          onPageChange={handlePageChange}
          onPageSizeChange={handlePageSizeChange}
        />
      )}
    </Card>
  );
};

export default TradeLogTable;
