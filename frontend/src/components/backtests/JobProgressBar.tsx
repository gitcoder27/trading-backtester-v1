import React from 'react';
import type { JobStatus } from '../../types';

interface JobProgressBarProps {
  status: JobStatus;
  progress?: number;
  estimatedTime?: string;
  size?: 'sm' | 'md';
}

const JobProgressBar: React.FC<JobProgressBarProps> = ({ status, progress = 0, estimatedTime, size = 'md' }) => {
  if (!(status === 'running' || status === 'pending')) return null;

  const barHeight = size === 'sm' ? 'h-2' : 'h-3';

  return (
    <div className={`space-y-${size === 'sm' ? '1' : '2'}`}>
      {size === 'md' && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-400">Progress</span>
          <span className="font-medium text-gray-900 dark:text-gray-100">{progress}%</span>
        </div>
      )}
      <div className={`w-full ${barHeight} bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden`}>
        <div
          className={`h-full ${size === 'md' ? 'bg-gradient-to-r from-blue-500 to-blue-600' : 'bg-blue-500'} transition-all duration-500 ease-out`}
          style={{ width: `${progress}%` }}
        />
      </div>
      {size === 'md' && estimatedTime && (
        <p className="text-xs text-gray-500 dark:text-gray-400">{estimatedTime}</p>
      )}
    </div>
  );
};

export default JobProgressBar;
