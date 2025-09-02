import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { TradesResponse } from './types';

const fetchTrades = async (
  backtestId: string,
  page: number,
  pageSize: number,
  sortBy: string,
  sortOrder: string,
  filterProfitable?: boolean,
  search?: string
): Promise<TradesResponse> => {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
    sort_by: sortBy,
    sort_order: sortOrder,
  });

  if (filterProfitable !== undefined) {
    params.append('filter_profitable', filterProfitable.toString());
  }

  const response = await fetch(
    `http://localhost:8000/api/v1/analytics/${backtestId}/trades?${params}`
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch trades: ${response.statusText}`);
  }

  return response.json();
};

export const useTradeData = (backtestId: string) => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [sortBy, setSortBy] = useState('entry_time');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [filterProfitable, setFilterProfitable] = useState<boolean | undefined>(undefined);
  const [searchTerm, setSearchTerm] = useState('');

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['trades', backtestId, page, pageSize, sortBy, sortOrder, filterProfitable, searchTerm],
    queryFn: () => fetchTrades(backtestId, page, pageSize, sortBy, sortOrder, filterProfitable, searchTerm),
    enabled: !!backtestId,
  });

  const handleSort = (column: string) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('desc');
    }
    setPage(1); // Reset to first page when sorting
  };

  const handleFilterChange = (profitable?: boolean) => {
    setFilterProfitable(profitable);
    setPage(1);
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  const handlePageSizeChange = (newPageSize: number) => {
    setPageSize(newPageSize);
    setPage(1);
  };

  const handleSearchChange = (term: string) => {
    setSearchTerm(term);
    setPage(1);
  };

  return {
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
  };
};
