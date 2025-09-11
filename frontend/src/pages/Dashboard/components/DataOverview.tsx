import React from 'react';
import { Card, LoadingSkeleton, Badge } from '../../../components/ui';
import type { DatasetSummary } from '../hooks/useDashboardData';

interface DataOverviewProps {
  summary: DatasetSummary | null;
  loading?: boolean;
}

const Pill: React.FC<{ label: string; count: number }>= ({ label, count }) => (
  <span className="inline-flex items-center gap-2 text-xs px-2.5 py-1 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-700">
    <span className="truncate max-w-[8rem]">{label}</span>
    <Badge variant="primary" size="sm">{count}</Badge>
  </span>
);

const DataOverview: React.FC<DataOverviewProps> = ({ summary, loading = false }) => {
  if (loading) {
    return (
      <Card className="p-6">
        <div className="space-y-3">
          <LoadingSkeleton className="h-5 w-1/2" />
          <LoadingSkeleton className="h-5 w-2/3" />
          <LoadingSkeleton className="h-5 w-1/3" />
        </div>
      </Card>
    );
  }

  const timeframes = summary ? Object.entries(summary.timeframes || {}).sort((a, b) => b[1] - a[1]).slice(0, 4) : [];
  const exchanges = summary ? Object.entries(summary.exchanges || {}).sort((a, b) => b[1] - a[1]).slice(0, 4) : [];

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-5">Data Overview</h3>
      {summary ? (
        <div className="space-y-5">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Datasets</p>
              <p className="text-xl font-semibold text-gray-900 dark:text-gray-100">{summary.total_datasets}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Total Rows</p>
              <p className="text-xl font-semibold text-gray-900 dark:text-gray-100">{summary.total_rows}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Avg Quality</p>
              <p className="text-xl font-semibold text-gray-900 dark:text-gray-100">{summary.average_quality_score?.toFixed?.(1) ?? summary.average_quality_score}</p>
            </div>
          </div>

          <div>
            <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">Timeframes</p>
            <div className="flex flex-wrap gap-2">
              {timeframes.length ? timeframes.map(([tf, count]) => (
                <Pill key={tf} label={tf} count={count as number} />
              )) : <span className="text-sm text-gray-600 dark:text-gray-400">No data</span>}
            </div>
          </div>

          <div>
            <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">Exchanges</p>
            <div className="flex flex-wrap gap-2">
              {exchanges.length ? exchanges.map(([ex, count]) => (
                <Pill key={ex} label={ex} count={count as number} />
              )) : <span className="text-sm text-gray-600 dark:text-gray-400">No data</span>}
            </div>
          </div>
        </div>
      ) : (
        <p className="text-sm text-gray-600 dark:text-gray-400">No dataset information available.</p>
      )}
    </Card>
  );
};

export default DataOverview;
