import React from 'react';
import Button from '../ui/Button';
import { Download, RotateCcw, Square } from 'lucide-react';
import type { JobStatus } from '../../types';

interface JobActionsBarProps {
  status: JobStatus;
  isPolling: boolean;
  onCancel: () => void;
  onDownload: () => void;
}

const JobActionsBar: React.FC<JobActionsBarProps> = ({ status, isPolling, onCancel, onDownload }) => {
  return (
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
        {status === 'completed' && (
          <Button variant="secondary" size="sm" icon={Download} onClick={onDownload}>
            Download Results
          </Button>
        )}
        {(status === 'running' || status === 'pending') && (
          <Button variant="danger" size="sm" icon={Square} onClick={onCancel}>
            Cancel
          </Button>
        )}
      </div>
    </div>
  );
};

export default JobActionsBar;

