import React, { useState, useEffect, useRef } from 'react';
import { Clock, CheckCircle, XCircle, AlertCircle, Play, Square, RotateCcw, Download } from 'lucide-react';
import Button from '../ui/Button';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import { JobService } from '../../services/backtest';
import type { Job, JobStatus } from '../../types';
import { showToast } from '../ui/Toast';

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
  const [job, setJob] = useState<Job>(initialJob);
  const [isPolling, setIsPolling] = useState(false);
  const [estimatedTimeRemaining, setEstimatedTimeRemaining] = useState<string>('');
  const [hasNotifiedCompletion, setHasNotifiedCompletion] = useState(
    // If job is already completed when component mounts, mark as already notified
    initialJob.status === 'completed' || initialJob.status === 'failed' || initialJob.status === 'cancelled'
  );
  const intervalRef = useRef<number | null>(null);
  const startTimeRef = useRef<Date>(new Date());

  useEffect(() => {
    // Only start polling for jobs that are actually running or pending
    // Don't poll for completed, failed, or cancelled jobs
    if ((job.status === 'running' || job.status === 'pending') && !hasNotifiedCompletion) {
      startPolling();
    } else {
      stopPolling();
    }

    return () => {
      stopPolling();
    };
  }, [job.status, hasNotifiedCompletion]);

  useEffect(() => {
    if (job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') {
      if (job.status === 'completed' && onJobComplete && !hasNotifiedCompletion) {
        setHasNotifiedCompletion(true);
        onJobComplete(job);
      }
      stopPolling();
    }
  }, [job.status, onJobComplete, hasNotifiedCompletion]);

  const startPolling = () => {
    if (intervalRef.current) return;
    
    setIsPolling(true);
    intervalRef.current = setInterval(async () => {
      try {
        const updatedJob = await JobService.getJobStatus(job.id);
        setJob(prev => ({
          ...prev,
          status: updatedJob.status,
          progress: updatedJob.progress || 0,
          error: updatedJob.error,
          completed_at: updatedJob.completed_at
        }));

        // Update estimated time remaining
        updateEstimatedTime(updatedJob.progress || 0);
      } catch (error) {
        console.error('Failed to fetch job status:', error);
        // Continue polling even if there's an error
      }
    }, 2000); // Poll every 2 seconds
  };

  const stopPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsPolling(false);
  };

  const updateEstimatedTime = (progress: number) => {
    if (progress <= 0) {
      setEstimatedTimeRemaining('Calculating...');
      return;
    }

    const elapsed = Date.now() - startTimeRef.current.getTime();
    const totalEstimated = elapsed / (progress / 100);
    const remaining = totalEstimated - elapsed;

    if (remaining <= 0) {
      setEstimatedTimeRemaining('Completing...');
      return;
    }

    const minutes = Math.floor(remaining / 60000);
    const seconds = Math.floor((remaining % 60000) / 1000);

    if (minutes > 0) {
      setEstimatedTimeRemaining(`~${minutes}m ${seconds}s remaining`);
    } else {
      setEstimatedTimeRemaining(`~${seconds}s remaining`);
    }
  };

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

  const getStatusIcon = (status: JobStatus) => {
    switch (status) {
      case 'completed':
        return CheckCircle;
      case 'running':
        return Play;
      case 'failed':
        return XCircle;
      case 'cancelled':
        return Square;
      case 'pending':
      default:
        return Clock;
    }
  };

  const getStatusColor = (status: JobStatus) => {
    switch (status) {
      case 'completed':
        return 'text-green-500';
      case 'running':
        return 'text-blue-500';
      case 'failed':
        return 'text-red-500';
      case 'cancelled':
        return 'text-gray-500';
      case 'pending':
      default:
        return 'text-yellow-500';
    }
  };

  const getStatusVariant = (status: JobStatus): 'success' | 'primary' | 'danger' | 'warning' => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'running':
        return 'primary';
      case 'failed':
        return 'danger';
      case 'cancelled':
      case 'pending':
      default:
        return 'warning';
    }
  };

  const formatDuration = (startTime: string, endTime?: string) => {
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const duration = end.getTime() - start.getTime();
    
    const minutes = Math.floor(duration / 60000);
    const seconds = Math.floor((duration % 60000) / 1000);
    
    if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    }
    return `${seconds}s`;
  };

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
        {job.status === 'running' && (
          <div className="w-16 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 transition-all duration-300"
              style={{ width: `${job.progress || 0}%` }}
            />
          </div>
        )}
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
        {(job.status === 'running' || job.status === 'pending') && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">Progress</span>
              <span className="font-medium text-gray-900 dark:text-gray-100">
                {job.progress || 0}%
              </span>
            </div>
            <div className="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-blue-600 transition-all duration-500 ease-out"
                style={{ width: `${job.progress || 0}%` }}
              />
            </div>
            {estimatedTimeRemaining && (
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {estimatedTimeRemaining}
              </p>
            )}
          </div>
        )}

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
              {formatDuration(job.created_at, job.completed_at)}
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
          <div className="flex items-center justify-between pt-2 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center space-x-2">
              {isPolling && (
                <div className="flex items-center space-x-1 text-xs text-gray-500 dark:text-gray-400">
                  <RotateCcw className="w-3 h-3 animate-spin" />
                  <span>Live updates</span>
                </div>
              )}
            </div>
            <div className="flex items-center space-x-2">
              {job.status === 'completed' && (
                <Button
                  variant="secondary"
                  size="sm"
                  icon={Download}
                  onClick={handleDownloadResults}
                >
                  Download Results
                </Button>
              )}
              {(job.status === 'running' || job.status === 'pending') && (
                <Button
                  variant="danger"
                  size="sm"
                  icon={Square}
                  onClick={handleCancel}
                >
                  Cancel
                </Button>
              )}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

export default JobProgressTracker;
