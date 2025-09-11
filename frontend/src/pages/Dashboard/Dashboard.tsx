import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, LoadingSkeleton, showToast } from '../../components/ui';
import { useDashboardData } from './hooks/useDashboardData';
import RecentActivity from './components/RecentActivity';
import PerformanceRow from './components/PerformanceRow';
import StrategyHighlights from './components/StrategyHighlights';
import DataOverview from './components/DataOverview';
import EnhancedBacktestModal from '../../components/modals/BacktestModal';
import { JobService } from '../../services/backtest';
import type { BacktestConfig } from '../../types';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const {
    loading,
    recentBacktests,
    recentJobs,
    latestCompletedBacktestId,
    topStrategies,
    mostTestedStrategies,
    datasetSummary,
  } = useDashboardData();

  // Backtest modal state
  const [showBacktestModal, setShowBacktestModal] = useState(false);
  const [submittingBacktest, setSubmittingBacktest] = useState(false);
  const handleSubmitBacktest = async (config: BacktestConfig) => {
    try {
      setSubmittingBacktest(true);
      await JobService.submitBackgroundJob(config);
      showToast.success('Backtest job submitted successfully!');
      setShowBacktestModal(false);
      navigate('/backtests');
    } catch (error) {
      console.error('Failed to submit backtest:', error);
      showToast.error('Failed to submit backtest job');
    } finally {
      setSubmittingBacktest(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Hero / Welcome */}
      <Card className="relative overflow-hidden p-6 md:p-8">
        <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/10 via-sky-500/5 to-emerald-500/10 pointer-events-none" />
        <div className="relative flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
              Welcome back
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Your trading system at a glance — clean, fast, and focused.
            </p>
          </div>
          <div className="flex gap-3">
            <Button variant="primary" onClick={() => setShowBacktestModal(true)}>
              Run Backtest
            </Button>
            <Button variant="outline" onClick={() => navigate('/datasets')}>Manage Data</Button>
          </div>
        </div>
      </Card>

      {/* Performance Snapshot Row (horizontal) */}
      <PerformanceRow backtestId={latestCompletedBacktestId} />

      {/* Main Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Left column: Recent Activity */}
        <div className="xl:col-span-2 space-y-6">
          <RecentActivity
            recentBacktests={recentBacktests}
            recentJobs={recentJobs}
            loading={loading}
          />

          {/* Strategy Highlights and Data Overview side by side */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <StrategyHighlights
              topStrategies={topStrategies}
              mostTestedStrategies={mostTestedStrategies}
              loading={loading}
            />
            <DataOverview summary={datasetSummary} loading={loading} />
          </div>
        </div>

        {/* Right column: space for future widgets */}
        <div className="space-y-6">
          <Card className="p-6">
            {loading ? (
              <div className="space-y-3">
                <LoadingSkeleton className="h-6 w-1/2" />
                <LoadingSkeleton className="h-5 w-2/3" />
                <LoadingSkeleton className="h-5 w-1/3" />
              </div>
            ) : (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Tips</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Use background jobs to queue multiple backtests efficiently.</p>
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* Backtest Modal */}
      <EnhancedBacktestModal
        isOpen={showBacktestModal}
        onClose={() => setShowBacktestModal(false)}
        onSubmit={handleSubmitBacktest}
        isSubmitting={submittingBacktest}
      />
    </div>
  );
};

export default Dashboard;
