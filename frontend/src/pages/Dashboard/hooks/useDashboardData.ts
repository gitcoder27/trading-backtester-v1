import { useState, useEffect } from 'react';
import { showToast } from '../../../components/ui/Toast';
import { StrategyService } from '../../../services/strategyService';
import { BacktestService } from '../../../services/backtest';

interface DashboardStats {
  totalReturn: number;
  activeStrategies: number;
  sharpeRatio: number;
  maxDrawdown: number;
  totalBacktests: number;
}

export const useDashboardData = () => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<DashboardStats>({
    totalReturn: 0,
    activeStrategies: 0,
    sharpeRatio: 0,
    maxDrawdown: 0,
    totalBacktests: 0
  });
  const [recentBacktests, setRecentBacktests] = useState<any[]>([]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load real strategy stats
      const strategyStats = await StrategyService.getStrategyStats();
      
      // Load recent backtests
      const backtestsResponse = await BacktestService.listBacktests({ page: 1, size: 5 });
      
      setStats({
        totalReturn: 24.5, // This would come from aggregated backtest results
        activeStrategies: strategyStats.active_strategies || 0,
        sharpeRatio: strategyStats.avg_performance || 0,
        maxDrawdown: -8.2, // This would come from aggregated backtest results
        totalBacktests: strategyStats.total_backtests || 0
      });
      
      setRecentBacktests(backtestsResponse.items || []);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      showToast.error('Failed to load dashboard data');
      // Keep default values
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  return {
    loading,
    stats,
    recentBacktests,
    refetch: loadDashboardData
  };
};
