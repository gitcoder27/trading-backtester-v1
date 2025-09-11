import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Button, LoadingSkeleton, StatusBadge, PerformanceBadge } from '../../../components/ui';
import { BarChart3, History } from 'lucide-react';

interface RecentActivityProps {
  recentBacktests: any[];
  recentJobs: any[];
  loading?: boolean;
}

const RecentActivity: React.FC<RecentActivityProps> = ({ recentBacktests, recentJobs, loading = false }) => {
  const navigate = useNavigate();

  const renderBacktestItem = (bt: any) => {
    const metrics = bt.results?.metrics || bt.metrics || bt.results || {};
    const totalReturnPct = typeof metrics.total_return_percent === 'number'
      ? metrics.total_return_percent
      : typeof metrics.total_return_pct === 'number'
      ? metrics.total_return_pct
      : (typeof metrics.total_return === 'number' ? (Math.abs(metrics.total_return) <= 1 ? metrics.total_return * 100 : metrics.total_return) : undefined);
    const sharpe = metrics.sharpe_ratio;
    const date = bt.created_at ? new Date(bt.created_at).toLocaleString() : '';
    const name = bt.strategy_name || bt.strategy_id || 'Strategy';

    return (
      <div
        key={bt.id}
        className="flex items-center justify-between p-4 bg-gray-50/60 dark:bg-gray-800/60 rounded-lg border border-gray-200 dark:border-gray-700"
      >
        <div className="min-w-0 pr-3">
          <div className="flex items-center gap-3">
            <h4 className="truncate font-medium text-gray-900 dark:text-gray-100">
              {name}
            </h4>
            <StatusBadge status={bt.status} size="sm" />
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{date}</p>
        </div>
        <div className="flex items-center gap-4">
          {bt.status === 'completed' && typeof totalReturnPct === 'number' && (
            <PerformanceBadge value={totalReturnPct} format="percentage" size="sm" />
          )}
          {bt.status === 'completed' && typeof sharpe === 'number' && (
            <p className="text-xs text-gray-500 dark:text-gray-400">Sharpe: {Number(sharpe).toFixed(2)}</p>
          )}
          <Button variant="ghost" size="sm" onClick={() => navigate(`/backtests/${bt.id}`)}>View</Button>
        </div>
      </div>
    );
  };

  const renderJobItem = (job: any) => (
    <div
      key={job.id}
      className="flex items-center justify-between p-4 bg-gray-50/60 dark:bg-gray-800/60 rounded-lg border border-gray-200 dark:border-gray-700"
    >
      <div className="min-w-0 pr-3">
        <div className="flex items-center gap-3">
          <h4 className="truncate font-medium text-gray-900 dark:text-gray-100">
            Job #{job.id}
          </h4>
          <StatusBadge status={job.status} size="sm" />
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{job.created_at ? new Date(job.created_at).toLocaleString() : ''}</p>
      </div>
      <div className="flex items-center gap-4">
        {typeof job.progress === 'number' && (
          <span className="text-xs text-gray-500 dark:text-gray-400">{Math.round(job.progress)}%</span>
        )}
        <Button variant="ghost" size="sm" onClick={() => navigate(`/backtests/${job.id}`)}>Open</Button>
      </div>
    </div>
  );

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card className="p-6">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Recent Backtests</h3>
          <Button variant="ghost" size="sm" onClick={() => navigate('/backtests')}>
            <BarChart3 className="h-4 w-4 mr-1" />
            View All
          </Button>
        </div>
        {loading ? (
          <div className="space-y-4">
            <LoadingSkeleton height="h-16" />
            <LoadingSkeleton height="h-16" />
            <LoadingSkeleton height="h-16" />
          </div>
        ) : recentBacktests.length ? (
          <div className="space-y-4">
            {recentBacktests.slice(0, 5).map(renderBacktestItem)}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <BarChart3 className="h-10 w-10 mx-auto mb-3 text-gray-300 dark:text-gray-600" />
            No backtests found
          </div>
        )}
      </Card>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Recent Jobs</h3>
          <Button variant="ghost" size="sm" onClick={() => navigate('/backtests')}>
            <History className="h-4 w-4 mr-1" />
            View Jobs
          </Button>
        </div>
        {loading ? (
          <div className="space-y-4">
            <LoadingSkeleton height="h-16" />
            <LoadingSkeleton height="h-16" />
            <LoadingSkeleton height="h-16" />
          </div>
        ) : recentJobs.length ? (
          <div className="space-y-4">
            {recentJobs.slice(0, 5).map(renderJobItem)}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <History className="h-10 w-10 mx-auto mb-3 text-gray-300 dark:text-gray-600" />
            No jobs yet
          </div>
        )}
      </Card>
    </div>
  );
};

export default RecentActivity;

