import type { Job, JobStatus } from '../../../types';

export interface JobsListProps {
  onJobComplete?: (job: Job) => void;
  onJobClick?: (job: Job) => void;
  compact?: boolean;
  maxJobs?: number;
}

export interface JobCardProps {
  job: Job;
  onCancel: (jobId: string) => void;
  onDelete: (jobId: string) => void;
  onDownload: (jobId: string) => void;
  onClick?: (job: Job) => void;
}

export interface JobFiltersProps {
  searchTerm: string;
  onSearchChange: (term: string) => void;
  statusFilter: JobStatus | 'all';
  onStatusFilterChange: (status: JobStatus | 'all') => void;
  sortBy: 'created_at' | 'status' | 'type';
  sortOrder: 'asc' | 'desc';
  onSortChange: (sortBy: 'created_at' | 'status' | 'type', sortOrder: 'asc' | 'desc') => void;
}

export interface JobActionsProps {
  job: Job;
  onCancel: (jobId: string) => void;
  onDelete: (jobId: string) => void;
  onDownload: (jobId: string) => void;
}

export type { Job, JobStatus };
