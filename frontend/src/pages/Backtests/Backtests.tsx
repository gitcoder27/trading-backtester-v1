import React, { useState, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useLocation, useNavigate } from 'react-router-dom';
import { Play, Activity } from 'lucide-react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Modal from '../../components/ui/Modal';
import EnhancedBacktestModal from '../../components/modals/BacktestModal';
import { JobsList } from '../../components/backtests';
import { BacktestService, JobService } from '../../services/backtest';
import type { BacktestConfig, Job } from '../../types';
import { showToast } from '../../components/ui/Toast';
import { useBacktestsList } from '../../hooks/useBacktestsList';
import { useBacktestStats } from '../../hooks/useBacktestStats';
import { useRecentJobs } from '../../hooks/useRecentJobs';
import BacktestStatsRow from '../../components/backtests/BacktestStatsRow';
import BacktestFilterTabs from '../../components/backtests/BacktestFilterTabs';
import BacktestCard from '../../components/backtests/BacktestCard';

// Data and stats are now provided by hooks

const Backtests: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [showNewBacktestModal, setShowNewBacktestModal] = useState(false);
  const [preselectedStrategyId, setPreselectedStrategyId] = useState<string | number | undefined>(undefined);
  const [preselectedParameters, setPreselectedParameters] = useState<Record<string, any> | undefined>(undefined);
  const [showJobsModal, setShowJobsModal] = useState(false);
  const [selectedFilter, setSelectedFilter] = useState<'all' | 'completed' | 'running' | 'failed'>('all');
  const { backtests, loading, refetch, removeBacktestLocally } = useBacktestsList();
  const stats = useBacktestStats(backtests);
  const { recentJobs, refetch: refetchRecentJobs } = useRecentJobs(5);
  const [submittingBacktest, setSubmittingBacktest] = useState(false);
  const [notifiedJobs, setNotifiedJobs] = useState<Set<string>>(new Set());
  const queryClient = useQueryClient();
  
  useEffect(() => {
    // Load data only once when component mounts
    // hooks auto-fetch on mount
    
    // Check if we came from strategy page with modal request
    if (location.state?.openConfigModal) {
      const st: any = location.state;
      setPreselectedStrategyId(st?.preselectedStrategyId);
      setPreselectedParameters(st?.parameters);
      setShowNewBacktestModal(true);
      // Clear the navigation state to prevent reopening modal on refresh
      window.history.replaceState({}, '', location.pathname);
    }
  }, []); // Empty dependency array - only run once on mount

  // Stats are computed via useBacktestStats


  const handleNewBacktest = async (config: BacktestConfig) => {
    try {
      setSubmittingBacktest(true);
      
      // Submit as background job for better UX
      await JobService.submitBackgroundJob(config);
      
      showToast.success('Backtest job submitted successfully!');
      setShowNewBacktestModal(false);
      
      // Refresh data to show the new job
      await Promise.all([refetch(), refetchRecentJobs()]);
      
      // Show the jobs modal to track progress
      setShowJobsModal(true);
    } catch (error) {
      console.error('Failed to submit backtest:', error);
      showToast.error('Failed to submit backtest job');
    } finally {
      setSubmittingBacktest(false);
    }
  };

  const handleJobComplete = (job: Job) => {
    // Prevent duplicate notifications for the same job
    if (notifiedJobs.has(job.id)) {
      return;
    }
    setNotifiedJobs(prev => new Set(prev).add(job.id));
    showToast.success(`Job ${job.id} completed successfully!`);
    
    // Don't reload data immediately to prevent infinite loop
    // loadData() will be called by the regular polling mechanism
  };

  const handleJobClick = async (job: Job) => {
    try {
      if (job.status === 'running' || job.status === 'pending') {
        showToast.info('Job still in progress. Please wait to view details.');
        return;
      }
      // Navigate to detail page using job ID; detail will fallback to job results if needed
      navigate(`/backtests/${job.id}`);
    } catch (err) {
      console.error('Failed to open backtest from job:', err);
      showToast.error('Failed to load backtest details for this job');
    }
  };

  const handleRefresh = async () => {
    const toastId = showToast.loading('Refreshing...');
    try {
      await Promise.all([
        refetch(),
        refetchRecentJobs(),
        queryClient.invalidateQueries({ queryKey: ['jobs-stats'] }),
      ]);
      showToast.success('Refreshed');
    } catch (e) {
      console.error('Failed to refresh:', e);
      showToast.error('Refresh failed');
    } finally {
      showToast.dismiss(toastId as any);
    }
  };

  const filteredBacktests = selectedFilter === 'all' 
    ? backtests 
    : backtests.filter(bt => bt.status === selectedFilter);

  // Status and formatting helpers moved to utils/status and utils/formatters

  const handleViewBacktest = (id: string) => {
    navigate(`/backtests/${id}`);
  };

  const handleDeleteBacktest = async (id: string) => {
    if (!confirm('Are you sure you want to delete this backtest?')) return;
    
    try {
      await BacktestService.deleteBacktest(id);
      removeBacktestLocally(id);
      showToast.success('Backtest deleted successfully');
    } catch (error) {
      console.error('Failed to delete backtest:', error);
      showToast.error('Failed to delete backtest');
    }
  };

  const handleDownloadReport = async (id: string) => {
    const toastId = showToast.loading('Preparing report...');
    try {
      const result = await BacktestService.getBacktestResults(id);
      const metrics: Record<string, any> = (result as any)?.results?.metrics
        ?? (result as any)?.results
        ?? (result as any)?.metrics
        ?? {};

      if (!metrics || Object.keys(metrics).length === 0) {
        showToast.warning('No metrics available to download');
        return;
      }

      const rows = Object.entries(metrics).map(([k, v]) => ({ metric: k, value: v }));
      const header = 'metric,value\n';
      const body = rows.map(r => `${r.metric},${r.value}`).join('\n');
      const csv = header + body;

      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `backtest-${id}-metrics.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      showToast.success('Report downloaded');
    } catch (err) {
      console.error('Failed to download report:', err);
      showToast.error('Failed to download report');
    } finally {
      showToast.dismiss(toastId as any);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 dark:bg-gray-700 rounded"></div>
            ))}
          </div>
          <div className="space-y-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 dark:bg-gray-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Backtest History</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            View and manage your backtest results and running jobs
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Button variant="outline" onClick={handleRefresh} size="sm">Refresh</Button>
          <Button
            variant="secondary"
            icon={Activity}
            onClick={() => setShowJobsModal(true)}
          >
            Background Jobs
          </Button>
          <Button
            icon={Play}
            onClick={() => setShowNewBacktestModal(true)}
            className="shadow-sm"
          >
            New Backtest
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <BacktestStatsRow
        totalBacktests={stats.totalBacktests}
        completedBacktests={stats.completedBacktests}
        runningJobs={stats.runningJobs}
        avgReturn={stats.avgReturn}
      />

      {/* Recent Jobs */}
      {recentJobs.length > 0 && (
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Recent Background Jobs
            </h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowJobsModal(true)}
            >
              View All
            </Button>
          </div>
          <JobsList 
            compact={true} 
            maxJobs={3} 
            onJobComplete={handleJobComplete}
            onJobClick={handleJobClick}
          />
        </Card>
      )}

      {/* Filter Tabs */}
      <BacktestFilterTabs
        selected={selectedFilter}
        onChange={setSelectedFilter}
        counts={{
          all: backtests.length,
          completed: backtests.filter(b => b.status === 'completed').length,
          running: backtests.filter(b => b.status === 'running').length,
          failed: backtests.filter(b => b.status === 'failed').length,
        }}
      />

      {/* Backtests List */}
      <div className="space-y-4">
        {filteredBacktests.map((backtest) => (
          <BacktestCard
            key={backtest.id}
            backtest={backtest}
            onView={handleViewBacktest}
            onDownload={handleDownloadReport}
            onDelete={handleDeleteBacktest}
          />
        ))}

        {filteredBacktests.length === 0 && (
          <Card className="p-12">
            <div className="text-center">
              {/* Icon intentionally omitted to keep this lean */}
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                No backtests found
              </h3>
              <p className="text-gray-500 dark:text-gray-400 mb-6">
                {selectedFilter === 'all' 
                  ? 'Get started by creating your first backtest.'
                  : `No backtests with status "${selectedFilter}" found.`
                }
              </p>
              <Button
                icon={Play}
                onClick={() => setShowNewBacktestModal(true)}
              >
                Create First Backtest
              </Button>
            </div>
          </Card>
        )}
      </div>

      {/* Enhanced Backtest Modal */}
      <EnhancedBacktestModal
        isOpen={showNewBacktestModal}
        onClose={() => { 
          setShowNewBacktestModal(false);
          // Clear preselected values after use
          setPreselectedStrategyId(undefined);
          setPreselectedParameters(undefined);
        }}
        onSubmit={handleNewBacktest}
        isSubmitting={submittingBacktest}
        preselectedStrategyId={preselectedStrategyId}
        preselectedParameters={preselectedParameters}
      />

      {/* Background Jobs Modal */}
      <Modal
        isOpen={showJobsModal}
        onClose={() => setShowJobsModal(false)}
        title="Background Jobs"
        size="xl"
      >
        <div className="max-h-[70vh] overflow-auto">
          <JobsList onJobComplete={handleJobComplete} onJobClick={handleJobClick} />
        </div>
      </Modal>
    </div>
  );
};

export default Backtests;
