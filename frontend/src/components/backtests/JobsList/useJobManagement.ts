import { useState, useCallback, useMemo, useEffect } from 'react';
import { JobService } from '../../../services/backtest';
import { showToast } from '../../ui/Toast';
import type { Job, JobStatus } from './types';
import { useJobsQuery } from '../../../hooks/useJobsQuery';

export const useJobManagement = (maxJobs?: number, fetchLimit?: number) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<JobStatus | 'all'>('all');
  const [sortBy, setSortBy] = useState<'created_at' | 'status' | 'type'>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const pageSize = maxJobs ?? 20;
  const queryLimit = fetchLimit ? Math.max(fetchLimit, pageSize) : pageSize;

  const jobsQuery = useJobsQuery(queryLimit);

  useEffect(() => {
    if (jobsQuery.isError && jobsQuery.error) {
      console.error('Failed to load jobs:', jobsQuery.error);
      showToast.error('Failed to load jobs');
    }
  }, [jobsQuery.isError, jobsQuery.error]);

  const allJobs = useMemo<Job[]>(() => {
    if (!jobsQuery.data) return [];
    return jobsQuery.data.jobs;
  }, [jobsQuery.data]);

  const sortedJobs = useMemo(() => {
    const copy = [...allJobs];
    copy.sort((a, b) => {
      const direction = sortOrder === 'asc' ? 1 : -1;
      if (sortBy === 'status') {
        return a.status.localeCompare(b.status) * direction;
      }
      if (sortBy === 'type') {
        const typeA = (a.type ?? 'backtest').toString();
        const typeB = (b.type ?? 'backtest').toString();
        return typeA.localeCompare(typeB) * direction;
      }
      const aDate = a.created_at ? new Date(a.created_at).getTime() : 0;
      const bDate = b.created_at ? new Date(b.created_at).getTime() : 0;
      return (aDate - bDate) * direction;
    });
    return copy;
  }, [allJobs, sortBy, sortOrder]);

  const filteredJobs = useMemo(() => {
    return sortedJobs.filter(job => {
      const matchesSearch = searchTerm.length === 0 ||
        job.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (job.type ?? '').toLowerCase().includes(searchTerm.toLowerCase());

      const matchesStatus = statusFilter === 'all' || job.status === statusFilter;

      return matchesSearch && matchesStatus;
    });
  }, [sortedJobs, searchTerm, statusFilter]);

  const paginatedJobs = useMemo(() => {
    const start = (page - 1) * pageSize;
    const end = start + pageSize;
    return filteredJobs.slice(start, end);
  }, [filteredJobs, page, pageSize]);

  useEffect(() => {
    const maxPage = Math.max(1, Math.ceil(filteredJobs.length / pageSize));
    setTotalPages(maxPage);
    if (page > maxPage) {
      setPage(maxPage);
    }
  }, [filteredJobs.length, pageSize, page]);

  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await jobsQuery.refetch({ cancelRefetch: false });
      showToast.success('Jobs refreshed');
    } catch (error) {
      console.error('Failed to refresh jobs:', error);
      showToast.error('Failed to refresh jobs');
    } finally {
      setIsRefreshing(false);
    }
  }, [jobsQuery]);

  const handleSearch = (value: string) => {
    setSearchTerm(value);
    setPage(1);
  };

  const handleStatusFilterChange = (status: JobStatus | 'all') => {
    setStatusFilter(status);
    setPage(1);
  };

  const handleSortChange = (newSortBy: 'created_at' | 'status' | 'type', newSortOrder: 'asc' | 'desc') => {
    setSortBy(newSortBy);
    setSortOrder(newSortOrder);
    setPage(1);
  };

  const handleCancelJob = async (jobId: string) => {
    try {
      await JobService.cancelJob(jobId);
      await jobsQuery.refetch({ cancelRefetch: false });
      showToast.warning('Job cancelled');
    } catch (error) {
      console.error('Failed to cancel job:', error);
      showToast.error('Failed to cancel job');
    }
  };

  const handleDownloadResults = async (jobId: string) => {
    try {
      const results = await JobService.getJobResults(jobId);
      const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `job-results-${jobId}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showToast.success('Results downloaded');
    } catch (error) {
      console.error('Failed to download results:', error);
      showToast.error('Failed to download results');
    }
  };

  const handleDeleteJob = async (jobId: string) => {
    if (!confirm('Are you sure you want to delete this job?')) return;
    
    try {
      await JobService.deleteJob(jobId);
      await jobsQuery.refetch({ cancelRefetch: false });
      showToast.success('Job deleted successfully');
    } catch (error) {
      console.error('Failed to delete job:', error);
      showToast.error('Failed to delete job');
    }
  };

  return {
    jobs: paginatedJobs,
    totalCount: filteredJobs.length,
    loading: jobsQuery.isLoading,
    isRefreshing: isRefreshing || jobsQuery.isFetching,
    searchTerm,
    statusFilter,
    sortBy,
    sortOrder,
    page,
    totalPages,
    handleRefresh,
    handleSearch,
    handleStatusFilterChange,
    handleSortChange,
    handleCancelJob,
    handleDownloadResults,
    handleDeleteJob,
    setPage
  };
};
