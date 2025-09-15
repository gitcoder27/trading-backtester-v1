import React from 'react';
import { AlertCircle, Download } from 'lucide-react';
import Button from '../ui/Button';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import { JobService } from '../../services/backtest';
import type { Job, JobStatus } from '../../types';
import { showToast } from '../ui/Toast';
import { getStatusIcon, getStatusColor, getStatusVariant } from '../../utils/status';
import { formatDuration } from '../../utils/formatters';
import { useJobPolling } from '../../hooks/useJobPolling';
import JobProgressBar from './JobProgressBar';
import JobActionsBar from './JobActionsBar';

interface JobProgressTrackerProps {
  job: Job;
  onJobComplete?: (job: Job) => void;
  onJobCancel?: (job: Job) => void;
  showActions?: boolean;
  compact?: boolean;
}

const JobProgressTracker: React.FC<JobProgressTrackerProps> = ({
  job: initialJob,
  onJobComplete,
  onJobCancel,
  showActions = true,
  compact = false
}) => {
  const { job, setJob, isPolling, estimatedTimeRemaining } = useJobPolling(initialJob, {
    onComplete: onJobComplete,
    pollIntervalMs: 2000,
    autoStart: true,
  });

  const handleCancel = async () => {
    try {
      await JobService.cancelJob(job.id);
      setJob(prev => ({ ...prev, status: 'cancelled' }));
      if (onJobCancel) {
        onJobCancel(job);
      }
      showToast.warning('Job cancelled successfully');
    } catch (error) {
      console.error('Failed to cancel job:', error);
      showToast.error('Failed to cancel job');
    }
  };

  const handleDownloadResults = async () => {
    try {
      const results = await JobService.getJobResults(job.id);
      // Create a blob and download
      const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `backtest-results-${job.id}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showToast.success('Results downloaded successfully');
    } catch (error) {
      console.error('Failed to download results:', error);
      showToast.error('Failed to download results');
    }
  };

  // status helpers and formatters are centralized in utils

  const StatusIcon = getStatusIcon(job.status);

  if (compact) {
    return (
      <div className="flex items-center space-x-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
        <StatusIcon className={`w-4 h-4 ${getStatusColor(job.status)}`} />
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
            Job {job.id}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            {job.status === 'running' ? `${job.progress || 0}% complete` : job.status}
          </div>
        </div>
        <JobProgressBar status={job.status} progress={job.progress || 0} size="sm" />
        <Badge variant={getStatusVariant(job.status)} size="sm">
          {job.status}
        </Badge>
      </div>
    );
  }

  return (
    <Card className="p-6">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <StatusIcon className={`w-6 h-6 ${getStatusColor(job.status)}`} />
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Backtest Job #{job.id}
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {job.type} • Started {new Date(job.created_at).toLocaleString()}
              </p>
            </div>
          </div>
          <Badge variant={getStatusVariant(job.status)}>
            {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
          </Badge>
        </div>

        {/* Progress Bar */}
        <JobProgressBar status={job.status} progress={job.progress || 0} estimatedTime={estimatedTimeRemaining} size="md" />

        {/* Job Details */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500 dark:text-gray-400">Type:</span>
            <span className="ml-2 font-medium text-gray-900 dark:text-gray-100">
              {job.type}
            </span>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400">Duration:</span>
            <span className="ml-2 font-medium text-gray-900 dark:text-gray-100">
              {formatDuration(job.created_at, job.completed_at || new Date().toISOString())}
            </span>
          </div>
        </div>

        {/* Error Message */}
        {job.status === 'failed' && job.error && (
          <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
            <div className="flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400 mt-0.5" />
              <div>
                <h4 className="text-sm font-medium text-red-800 dark:text-red-200">
                  Error
                </h4>
                <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                  {job.error}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        {showActions && (
          <JobActionsBar
            status={job.status}
            isPolling={isPolling}
            onCancel={handleCancel}
            onDownload={handleDownloadResults}
          />
        )}
      </div>
    </Card>
  );
};

export default JobProgressTracker;
