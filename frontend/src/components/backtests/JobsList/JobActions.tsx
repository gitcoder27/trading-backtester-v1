import React from 'react';
import { Download, Square, Trash2 } from 'lucide-react';
import Button from '../../ui/Button';
import type { JobActionsProps } from './types';

const JobActions: React.FC<JobActionsProps> = ({
  job,
  onCancel,
  onDelete,
  onDownload
}) => {
  return (
    <div className="flex items-center space-x-2">
      {job.status === 'completed' && (
        <Button
          variant="secondary"
          size="sm"
          icon={Download}
          onClick={() => onDownload(job.id)}
        >
          Download
        </Button>
      )}
      {(job.status === 'running' || job.status === 'pending') && (
        <Button
          variant="danger"
          size="sm"
          icon={Square}
          onClick={() => onCancel(job.id)}
        >
          Cancel
        </Button>
      )}
      {(job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') && (
        <Button
          variant="ghost"
          size="sm"
          icon={Trash2}
          onClick={() => onDelete(job.id)}
        >
          Delete
        </Button>
      )}
    </div>
  );
};

export default JobActions;
