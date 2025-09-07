import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Play, Clock, CheckCircle, XCircle, Eye, Trash2, Download, TrendingUp, BarChart3, Activity } from 'lucide-react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import Modal from '../../components/ui/Modal';
import EnhancedBacktestModal from '../../components/modals/BacktestModal';
import { JobsList } from '../../components/backtests';
import { BacktestService, JobService } from '../../services/backtest';
import type { BacktestConfig, Job } from '../../types';
import { showToast } from '../../components/ui/Toast';

// Local interface for display purposes
interface BacktestDisplay {
  id: string;
  jobId?: string; // Add job_id field
  strategy: string;
  dataset: string;
  status: 'completed' | 'running' | 'failed' | 'pending';
  totalReturn: string;
  sharpeRatio: number;
  maxDrawdown: string;
  totalTrades: number;
  winRate: string;
  createdAt: string;
  createdAtTs: number; // for robust sorting
  duration: string;
}

const Backtests: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [showNewBacktestModal, setShowNewBacktestModal] = useState(false);
  const [showJobsModal, setShowJobsModal] = useState(false);
  const [selectedFilter, setSelectedFilter] = useState<'all' | 'completed' | 'running' | 'failed'>('all');
  const [backtests, setBacktests] = useState<BacktestDisplay[]>([]);
  const [recentJobs, setRecentJobs] = useState<Job[]>([]);
  const [stats, setStats] = useState({
    totalBacktests: 0,
    completedBacktests: 0,
    runningJobs: 0,
    avgReturn: 0
  });
  const [loading, setLoading] = useState(true);
  const [submittingBacktest, setSubmittingBacktest] = useState(false);
  const [notifiedJobs, setNotifiedJobs] = useState<Set<string>>(new Set());
  
  const extractJobIdNumber = (jobId?: string): number => {
    if (!jobId) return -Infinity;
    // Try direct number
    const asNum = Number(jobId);
    if (!Number.isNaN(asNum)) return asNum;
    // Extract last number sequence from string like "job-123"
    const match = jobId.match(/(\d+)/g);
    if (match && match.length > 0) {
      const last = match[match.length - 1];
      const n = Number(last);
      if (!Number.isNaN(n)) return n;
    }
    return -Infinity;
  };

  useEffect(() => {
    console.log("[DEBUG] Backtests useEffect triggered");
    // Load data only once when component mounts
    loadData();
    
    // Check if we came from strategy page with modal request
    if (location.state?.openConfigModal) {
      setShowNewBacktestModal(true);
      // Clear the navigation state to prevent reopening modal on refresh
      window.history.replaceState({}, '', location.pathname);
    }
  }, []); // Empty dependency array - only run once on mount

  const loadData = async () => {
    try {
      setLoading(true);
      await Promise.all([
        loadBacktests(),
        loadRecentJobs(),
      ]);
    } catch (error) {
      console.error('Failed to load data:', error);
      showToast.error('Failed to load backtest data');
    } finally {
      setLoading(false);
    }
  };

  const loadBacktests = async () => {
    try {
      // Fetch all backtests across pages to show a complete list
      const pageSize = 100; // backend allows up to 100
      const first = await BacktestService.listBacktests({ page: 1, size: pageSize });
      let items: any[] = [];
      let total = 0;
      if ((first as any).results) {
        items = (first as any).results;
        total = (first as any).total || items.length;
      } else if ((first as any).data) {
        items = (first as any).data;
        total = (first as any).total || items.length;
      } else if ((first as any).items) {
        items = (first as any).items;
        total = (first as any).total || items.length;
      }
      const pages = Math.max(1, Math.ceil(total / pageSize));
      const rest: any[] = [];
      for (let p = 2; p <= pages; p++) {
        try {
          const res = await BacktestService.listBacktests({ page: p, size: pageSize });
          if ((res as any).results) rest.push(...(res as any).results);
          else if ((res as any).data) rest.push(...(res as any).data);
          else if ((res as any).items) rest.push(...(res as any).items);
        } catch (e) {
          console.warn(`[WARN] Failed to fetch backtests page ${p}:`, e);
          break;
        }
      }
      const backtestItems = [...items, ...rest];
      console.log('[DEBUG] Processed backtest items (aggregated):', backtestItems);
      
      const backtestDisplays: BacktestDisplay[] = backtestItems.map((bt: any) => {
        // Extract metrics from the nested results structure
        const metrics = bt.results?.metrics || bt.metrics || {};
        
        // Clean up strategy name for display
        const strategyName = bt.strategy_name || bt.strategy_id || 'Unknown Strategy';
        const cleanStrategyName = strategyName.includes('.') 
          ? strategyName.split('.').pop() || strategyName
          : strategyName;

        // Normalize return percent with sign for consistent coloring
        const deriveReturnPercent = (): string => {
          let pct: number | null = null;
          if (typeof metrics.total_return_percent === 'number') {
            pct = metrics.total_return_percent;
          } else if (typeof metrics.total_return === 'number') {
            // If backend provided a fraction, convert to percentage
            pct = Math.abs(metrics.total_return) <= 1 ? metrics.total_return * 100 : metrics.total_return;
          }
          if (pct === null || Number.isNaN(pct)) return 'N/A';
          const sign = pct > 0 ? '+' : '';
          return `${sign}${pct.toFixed(2)}%`;
        };
        
        return {
          id: bt.id,
          jobId: (bt.job_id ?? bt.backtest_job_id)?.toString(), // Normalize to string
          strategy: cleanStrategyName,
          dataset: bt.dataset_name && bt.dataset_name !== 'Unknown Dataset' 
            ? bt.dataset_name 
            : 'NIFTY Aug 2025 (1min)',
          status: (bt.status === 'error' ? 'failed' : bt.status) || 'pending',
          totalReturn: deriveReturnPercent(),
          sharpeRatio: metrics.sharpe_ratio || 0,
          maxDrawdown: metrics.max_drawdown_percent
            ? `${metrics.max_drawdown_percent.toFixed(2)}%`
            : metrics.max_drawdown 
            ? `${(metrics.max_drawdown * 100).toFixed(2)}%` 
            : 'N/A',
          totalTrades: metrics.total_trades || 0,
          // Backend returns win_rate as percentage (0–100). Do not multiply again.
          winRate: typeof metrics.win_rate === 'number' ? `${metrics.win_rate.toFixed(1)}%` : 'N/A',
          createdAt: new Date(bt.created_at).toLocaleDateString(),
          createdAtTs: new Date(bt.created_at).getTime(),
          duration: bt.completed_at 
            ? formatDuration(bt.created_at, bt.completed_at)
            : bt.status === 'running' ? 'In Progress' : 'Pending'
        };
      });
      
      // Sort by jobId descending (most recent on top); fallback to created_at
      const sorted = [...backtestDisplays].sort((a, b) => {
        const aNum = extractJobIdNumber(a.jobId);
        const bNum = extractJobIdNumber(b.jobId);
        if (aNum !== bNum) return bNum - aNum;
        // Fallback to createdAt date desc if no jobId or equal
        const aDate = a.createdAtTs;
        const bDate = b.createdAtTs;
        return bDate - aDate;
      });

      console.log('[DEBUG] Final backtest displays (sorted):', sorted);
      setBacktests(sorted);
    } catch (error) {
      console.error('Failed to load backtests:', error);
      showToast.error('Failed to load backtests from server');
      // Set empty array instead of mock data to clearly show the API issue
      setBacktests([]);
    }
  };

  const loadRecentJobs = async () => {
    try {
      const response = await JobService.listJobs({ page: 1, size: 5 });
      // Handle API response format: {success: true, jobs: [...], total: N}
      const jobs = (response as any).jobs || response.items || [];
      setRecentJobs(jobs);
    } catch (error) {
      console.error('Failed to load recent jobs:', error);
      setRecentJobs([]);
    }
  };

  // Recalculate stats whenever backtests change and fetch running job count
  useEffect(() => {
    const completed = backtests.filter(bt => bt.status === 'completed');
    const avgReturn = completed.length > 0
      ? completed.reduce((acc, bt) => {
          const value = parseFloat(bt.totalReturn.replace('%', '').replace('+', ''));
          return acc + (Number.isNaN(value) ? 0 : value);
        }, 0) / completed.length
      : 0;

    // Set base stats from backtests
    setStats(prev => ({
      ...prev,
      totalBacktests: backtests.length,
      completedBacktests: completed.length,
      avgReturn
    }));

    // Then update running jobs from the jobs stats endpoint
    (async () => {
      try {
        const res = await JobService.getJobStats();
        const running = (res as any)?.stats?.running ?? 0;
        setStats(prev => ({ ...prev, runningJobs: running }));
      } catch (e) {
        // Fallback: estimate running jobs from backtests list
        const running = backtests.filter(bt => bt.status === 'running').length;
        setStats(prev => ({ ...prev, runningJobs: running }));
      }
    })();
  }, [backtests]);

  const formatDuration = (startTime: string, endTime: string) => {
    const start = new Date(startTime);
    const end = new Date(endTime);
    const duration = end.getTime() - start.getTime();
    
    const hours = Math.floor(duration / (1000 * 60 * 60));
    const minutes = Math.floor((duration % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  const handleNewBacktest = async (config: BacktestConfig) => {
    try {
      setSubmittingBacktest(true);
      
      // Submit as background job for better UX
      await JobService.submitBackgroundJob(config);
      
      showToast.success('Backtest job submitted successfully!');
      setShowNewBacktestModal(false);
      
      // Refresh data to show the new job
      await loadData();
      
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
      console.log(`[DEBUG] Job ${job.id} already notified, skipping...`);
      return;
    }
    
    console.log(`[DEBUG] Job ${job.id} completed, first notification`);
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

  const filteredBacktests = selectedFilter === 'all' 
    ? backtests 
    : backtests.filter(bt => bt.status === selectedFilter);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return CheckCircle;
      case 'running': return Play;
      case 'failed': return XCircle;
      default: return Clock;
    }
  };

  const getStatusVariant = (status: string): 'success' | 'primary' | 'danger' | 'warning' => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'primary';
      case 'failed': return 'danger';
      default: return 'warning';
    }
  };

  const getReturnColor = (returnStr: string) => {
    if (returnStr === 'N/A') return 'text-gray-400';
    const isPositive = returnStr.startsWith('+');
    return isPositive ? 'text-green-400' : 'text-red-400';
  };

  const handleViewBacktest = (id: string) => {
    navigate(`/backtests/${id}`);
  };

  const handleDeleteBacktest = async (id: string) => {
    if (!confirm('Are you sure you want to delete this backtest?')) return;
    
    try {
      await BacktestService.deleteBacktest(id);
      setBacktests(backtests.filter(bt => bt.id !== id));
      showToast.success('Backtest deleted successfully');
    } catch (error) {
      console.error('Failed to delete backtest:', error);
      showToast.error('Failed to delete backtest');
    }
  };

  const handleDownloadReport = (id: string) => {
    showToast.success(`Downloading report for backtest ${id}`);
    // TODO: Implement report download
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
          <Button
            variant="outline"
            onClick={() => loadData()}
            size="sm"
          >
            Refresh
          </Button>
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
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Backtests</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{stats.totalBacktests}</p>
            </div>
            <div className="p-3 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
              <BarChart3 className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Completed</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{stats.completedBacktests}</p>
            </div>
            <div className="p-3 bg-green-100 dark:bg-green-900/20 rounded-lg">
              <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Running Jobs</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{stats.runningJobs}</p>
            </div>
            <div className="p-3 bg-yellow-100 dark:bg-yellow-900/20 rounded-lg">
              <Clock className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Avg Return</p>
              <p className={`text-2xl font-bold ${stats.avgReturn >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {stats.avgReturn >= 0 ? '+' : ''}{stats.avgReturn.toFixed(1)}%
              </p>
            </div>
            <div className="p-3 bg-purple-100 dark:bg-purple-900/20 rounded-lg">
              <TrendingUp className="w-6 h-6 text-purple-600 dark:text-purple-400" />
            </div>
          </div>
        </Card>
      </div>

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
      <div className="flex items-center space-x-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg w-fit">
        {(['all', 'completed', 'running', 'failed'] as const).map((filter) => (
          <button
            key={filter}
            onClick={() => setSelectedFilter(filter)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              selectedFilter === filter
                ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
            }`}
          >
            {filter.charAt(0).toUpperCase() + filter.slice(1)}
            <span className="ml-2 text-xs opacity-75">
              ({filter === 'all' ? backtests.length : backtests.filter(bt => bt.status === filter).length})
            </span>
          </button>
        ))}
      </div>

      {/* Backtests List */}
      <div className="space-y-4">
        {filteredBacktests.map((backtest) => {
          const StatusIcon = getStatusIcon(backtest.status);
          
          return (
            <Card key={backtest.id} className="p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <StatusIcon className={`w-6 h-6 ${backtest.status === 'completed' ? 'text-green-500' : backtest.status === 'running' ? 'text-blue-500' : backtest.status === 'failed' ? 'text-red-500' : 'text-yellow-500'}`} />
                  <div>
                    <div className="flex items-center space-x-3">
                      <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                        {backtest.strategy}
                      </h3>
                      <Badge variant={getStatusVariant(backtest.status)}>
                        {backtest.status}
                      </Badge>
                    </div>
                    <div className="flex items-center space-x-6 mt-1 text-sm text-gray-500 dark:text-gray-400">
                      <span>Backtest: {backtest.id}</span>
                      {backtest.jobId && <span>Job: {backtest.jobId}</span>}
                      <span>Dataset: {backtest.dataset}</span>
                      <span>Created: {backtest.createdAt}</span>
                      <span>Duration: {backtest.duration}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-6">
                  {/* Performance Metrics */}
                  {backtest.status === 'completed' && (
                    <div className="flex items-center space-x-6 text-sm">
                      <div className="text-center">
                        <p className="text-gray-500 dark:text-gray-400">Return</p>
                        <p className={`font-semibold ${getReturnColor(backtest.totalReturn)}`}>
                          {backtest.totalReturn}
                        </p>
                      </div>
                      <div className="text-center">
                        <p className="text-gray-500 dark:text-gray-400">Sharpe</p>
                        <p className="font-semibold text-gray-900 dark:text-gray-100">
                          {backtest.sharpeRatio.toFixed(2)}
                        </p>
                      </div>
                      <div className="text-center">
                        <p className="text-gray-500 dark:text-gray-400">Drawdown</p>
                        <p className="font-semibold text-red-400">
                          {backtest.maxDrawdown}
                        </p>
                      </div>
                      <div className="text-center">
                        <p className="text-gray-500 dark:text-gray-400">Trades</p>
                        <p className="font-semibold text-gray-900 dark:text-gray-100">
                          {backtest.totalTrades}
                        </p>
                      </div>
                      <div className="text-center">
                        <p className="text-gray-500 dark:text-gray-400">Win Rate</p>
                        <p className="font-semibold text-gray-900 dark:text-gray-100">
                          {backtest.winRate}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      icon={Eye}
                      onClick={() => handleViewBacktest(backtest.id)}
                    >
                      View
                    </Button>
                    {backtest.status === 'completed' && (
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={Download}
                        onClick={() => handleDownloadReport(backtest.id)}
                      >
                        Download
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      icon={Trash2}
                      onClick={() => handleDeleteBacktest(backtest.id)}
                      className="text-red-600 hover:text-red-700"
                    >
                      Delete
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          );
        })}

        {filteredBacktests.length === 0 && (
          <Card className="p-12">
            <div className="text-center">
              <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
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
        onClose={() => setShowNewBacktestModal(false)}
        onSubmit={handleNewBacktest}
        isSubmitting={submittingBacktest}
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
