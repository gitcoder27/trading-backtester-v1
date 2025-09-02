import React from 'react';
import { Clock, CheckCircle, XCircle, Play, Square } from 'lucide-react';
import Card from '../../ui/Card';
import Badge from '../../ui/Badge';
import JobActions from './JobActions';
import type { JobCardProps, JobStatus } from './types';

const JobCard: React.FC<JobCardProps> = ({
  job,
  onCancel,
  onDelete,
  onDownload
}) => {
  const getStatusIcon = (status: JobStatus) => {
    switch (status) {
      case 'completed': return CheckCircle;
      case 'running': return Play;
      case 'failed': return XCircle;
      case 'cancelled': return Square;
      case 'pending':
      default: return Clock;
    }
  };

  const getStatusColor = (status: JobStatus) => {
    switch (status) {
      case 'completed': return 'text-green-500';
      case 'running': return 'text-blue-500';
      case 'failed': return 'text-red-500';
      case 'cancelled': return 'text-gray-500';
      case 'pending':
      default: return 'text-yellow-500';
    }
  };

  const getStatusVariant = (status: JobStatus): 'success' | 'primary' | 'danger' | 'warning' => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'primary';
      case 'failed': return 'danger';
      case 'cancelled':
      case 'pending':
      default: return 'warning';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const StatusIcon = getStatusIcon(job.status);

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <StatusIcon className={`w-6 h-6 ${getStatusColor(job.status)}`} />
          <div>
            <div className="flex items-center space-x-3">
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                Job #{job.id}
              </h3>
              <Badge variant={getStatusVariant(job.status)}>
                {job.status}
              </Badge>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {job.type}
              </span>
            </div>
            <div className="flex items-center space-x-4 mt-1 text-sm text-gray-500 dark:text-gray-400">
              <span>Created: {formatDate(job.created_at)}</span>
              {job.completed_at && (
                <span>Completed: {formatDate(job.completed_at)}</span>
              )}
              {job.progress !== undefined && job.status === 'running' && (
                <span>{job.progress}% complete</span>
              )}
            </div>
          </div>
        </div>

        <JobActions
          job={job}
          onCancel={onCancel}
          onDelete={onDelete}
          onDownload={onDownload}
        />
      </div>

      {/* Progress Bar for Running Jobs */}
      {job.status === 'running' && job.progress !== undefined && (
        <div className="mt-4">
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-gray-600 dark:text-gray-400">Progress</span>
            <span className="font-medium text-gray-900 dark:text-gray-100">
              {job.progress}%
            </span>
          </div>
          <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 transition-all duration-300"
              style={{ width: `${job.progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Error Message */}
      {job.status === 'failed' && job.error && (
        <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
          <p className="text-sm text-red-700 dark:text-red-300">
            <strong>Error:</strong> {job.error}
          </p>
        </div>
      )}
    </Card>
  );
};

export default JobCard;
