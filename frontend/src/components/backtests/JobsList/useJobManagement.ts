import { useState, useEffect, useCallback } from 'react';
import { JobService } from '../../../services/backtest';
import { showToast } from '../../ui/Toast';
import type { Job, JobStatus } from './types';

export const useJobManagement = (maxJobs?: number) => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<JobStatus | 'all'>('all');
  const [sortBy, setSortBy] = useState<'created_at' | 'status' | 'type'>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadJobs = useCallback(async () => {
    try {
      setLoading(true);
      const params = {
        page,
        size: maxJobs || 20,
        sort: sortBy,
        order: sortOrder,
        search: searchTerm || undefined,
        ...(statusFilter !== 'all' && { status: statusFilter })
      };

      const response = await JobService.listJobs(params);
      // The API returns { success: true, jobs: [...], total: 14 }
      // but we expect { items: [...], total: 14 }
      const jobs = (response as any).jobs || response.items || [];
      setJobs(jobs);
      setTotalPages((response as any).total ? Math.ceil((response as any).total / (maxJobs || 20)) : 1);
    } catch (error) {
      console.error('Failed to load jobs:', error);
      showToast.error('Failed to load jobs');
    } finally {
      setLoading(false);
    }
  }, [page, maxJobs, sortBy, sortOrder, searchTerm, statusFilter]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await loadJobs();
    setIsRefreshing(false);
    showToast.success('Jobs refreshed');
  };

  const handleSearch = (value: string) => {
    setSearchTerm(value);
    if (value.length === 0 || value.length >= 3) {
      setPage(1);
      void loadJobs();
    }
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
      setJobs(prev => prev.map(job => 
        job.id === jobId ? { ...job, status: 'cancelled' } : job
      ));
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
      setJobs(prev => prev.filter(job => job.id !== jobId));
      showToast.success('Job deleted successfully');
    } catch (error) {
      console.error('Failed to delete job:', error);
      showToast.error('Failed to delete job');
    }
  };

  const filteredJobs = jobs.filter(job => {
    const matchesSearch = searchTerm.length === 0 || 
      job.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      job.type.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || job.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  useEffect(() => {
    loadJobs();
  }, [loadJobs]);

  return {
    jobs: filteredJobs,
    loading,
    isRefreshing,
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
