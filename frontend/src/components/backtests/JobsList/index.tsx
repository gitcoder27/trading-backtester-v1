import React from 'react';
import { Clock, RefreshCw } from 'lucide-react';
import Button from '../../ui/Button';
import Card from '../../ui/Card';
import JobProgressTracker from '../JobProgressTracker';
import { useJobManagement } from './useJobManagement';
import JobFilters from './JobFilters';
import JobCard from './JobCard';
import type { JobsListProps } from './types';

const JobsList: React.FC<JobsListProps> = ({
  onJobComplete,
  compact = false,
  maxJobs
}) => {
  const {
    jobs,
    loading,
    isRefreshing,
    searchTerm,
    statusFilter,
    sortBy,
    sortOrder,
    page,
    totalPages,
    handleRefresh,
    handleSearch,
    handleStatusFilterChange,
    handleSortChange,
    handleCancelJob,
    handleDownloadResults,
    handleDeleteJob,
    setPage
  } = useJobManagement(maxJobs);

  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-16 bg-gray-200 dark:bg-gray-700 rounded"></div>
            ))}
          </div>
        </div>
      </Card>
    );
  }

  if (compact) {
    return (
      <div className="space-y-3">
        {jobs.slice(0, maxJobs).map((job) => (
          <JobProgressTracker
            key={job.id}
            job={job}
            onJobComplete={onJobComplete}
            compact={true}
            showActions={false}
          />
        ))}
        {jobs.length === 0 && (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            No jobs found
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            Background Jobs
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {jobs.length} jobs found
          </p>
        </div>
        <Button
          variant="secondary"
          size="sm"
          icon={RefreshCw}
          onClick={handleRefresh}
          loading={isRefreshing}
        >
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <JobFilters
        searchTerm={searchTerm}
        onSearchChange={handleSearch}
        statusFilter={statusFilter}
        onStatusFilterChange={handleStatusFilterChange}
        sortBy={sortBy}
        sortOrder={sortOrder}
        onSortChange={handleSortChange}
      />

      {/* Jobs List */}
      <div className="space-y-4">
        {jobs.map((job) => (
          <JobCard
            key={job.id}
            job={job}
            onCancel={handleCancelJob}
            onDelete={handleDeleteJob}
            onDownload={handleDownloadResults}
          />
        ))}

        {jobs.length === 0 && (
          <Card className="p-12">
            <div className="text-center">
              <Clock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                No jobs found
              </h3>
              <p className="text-gray-500 dark:text-gray-400">
                {statusFilter === 'all' 
                  ? 'No background jobs have been created yet.'
                  : `No jobs with status "${statusFilter}" found.`
                }
              </p>
            </div>
          </Card>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center space-x-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setPage(page - 1)}
            disabled={page <= 1}
          >
            Previous
          </Button>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setPage(page + 1)}
            disabled={page >= totalPages}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
};

export default JobsList;
