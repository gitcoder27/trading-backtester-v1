import React, { useState } from 'react';
import { showToast } from '../../components/ui';
import { useDashboardData } from './hooks/useDashboardData';
import WelcomeHeader from './components/WelcomeHeader';
import StatsCards from './components/StatsCards';
import RecentBacktests from './components/RecentBacktests';
import QuickActions from './components/QuickActions';
import DemoModal from './components/DemoModal';

const Dashboard: React.FC = () => {
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const { loading: dashboardLoading, stats, recentBacktests } = useDashboardData();

  const handleQuickBacktest = () => {
    setLoading(true);
    showToast.loading('Starting backtest...');
    
    // Simulate API call
    setTimeout(() => {
      setLoading(false);
      showToast.success('Backtest started successfully!', 'You can monitor progress in the Backtests page.');
    }, 2000);
  };

  const handleShowDemo = () => {
    setShowModal(true);
    showToast.info('Demo modal opened', 'This showcases our modal component with theme support.');
  };

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <WelcomeHeader
        onQuickBacktest={handleQuickBacktest}
        onShowDemo={handleShowDemo}
        loading={loading}
      />

      {/* Stats Overview */}
      <StatsCards stats={stats} loading={dashboardLoading} />

      {/* Recent Backtests & Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RecentBacktests recentBacktests={recentBacktests} loading={dashboardLoading} />
        <QuickActions />
      </div>

      {/* Demo Modal */}
      <DemoModal 
        isOpen={showModal}
        onClose={() => setShowModal(false)}
      />
    </div>
  );
};

export default Dashboard;
