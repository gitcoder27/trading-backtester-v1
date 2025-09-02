export interface Trade {
  id?: number;
  entry_time: string;
  exit_time: string;
  symbol: string;
  side: 'buy' | 'sell';
  entry_price: number;
  exit_price: number;
  quantity: number;
  pnl: number;
  pnl_pct?: number;
  duration?: number;
  fees?: number;
}

export interface TradesResponse {
  success: boolean;
  trades: Trade[];
  total_trades: number;
  page: number;
  page_size: number;
  total_pages: number;
  sort_by: string;
  sort_order: string;
  filter_profitable?: boolean;
}

export interface TradeLogTableProps {
  backtestId: string;
  className?: string;
}

export interface TableHeaderProps {
  onExportCSV: () => void;
  hasData: boolean;
  searchTerm: string;
  onSearchChange: (term: string) => void;
  filterProfitable?: boolean;
  onFilterChange: (profitable?: boolean) => void;
  totalTrades: number;
  currentPage: number;
  pageSize: number;
  winningTrades: number;
  losingTrades: number;
}

export interface SortConfig {
  sortBy: string;
  sortOrder: 'asc' | 'desc';
  onSort: (column: string) => void;
}

export interface PaginationProps {
  currentPage: number;
  totalPages: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
}
