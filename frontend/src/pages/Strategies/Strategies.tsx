import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Target, Edit3, Play, Clock, CheckCircle, Search, BarChart3, AlertTriangle, Filter } from 'lucide-react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import Modal from '../../components/ui/Modal';
import { showToast } from '../../components/ui/Toast';
import StrategyDiscovery from '../../components/strategies/StrategyDiscovery';
import StrategyDetailView from '../../components/strategies/StrategyDetailView';
import { StrategyService } from '../../services/strategyService';
import type { Strategy } from '../../types';

type ViewMode = 'list' | 'detail';
type FilterType = 'all' | 'active' | 'inactive';

const Strategies: React.FC = () => {
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [selectedStrategyId, setSelectedStrategyId] = useState<string | null>(null);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [filteredStrategies, setFilteredStrategies] = useState<Strategy[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<FilterType>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [strategyStats, setStrategyStats] = useState({
    total_strategies: 0,
    active_strategies: 0,
    discovered_strategies: 0,
    total_backtests: 0,
    avg_performance: 0
  });

  useEffect(() => {
    loadStrategies();
    loadStrategyStats();
  }, []);

  useEffect(() => {
    // Filter strategies based on search and filter type
    let filtered = Array.isArray(strategies) ? strategies : [];
    
    if (searchTerm) {
      filtered = filtered.filter(strategy =>
        strategy.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (strategy.description && strategy.description.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }
    
    if (filterType !== 'all') {
      filtered = filtered.filter(strategy =>
        filterType === 'active' ? strategy.is_active : !strategy.is_active
      );
    }
    
    setFilteredStrategies(filtered);
  }, [strategies, searchTerm, filterType]);

  const loadStrategies = async () => {
    try {
      const strategiesData = await StrategyService.getStrategies();
      setStrategies(Array.isArray(strategiesData) ? strategiesData : []);
    } catch (error) {
      console.error('Failed to load strategies:', error);
      showToast.error('Failed to load strategies');
      setStrategies([]); // Ensure we set empty array on error
    } finally {
      setIsLoading(false);
    }
  };

  const loadStrategyStats = async () => {
    try {
      const stats = await StrategyService.getStrategyStats();
      setStrategyStats(stats || {
        total_strategies: 0,
        active_strategies: 0,
        discovered_strategies: 0,
        total_backtests: 0,
        avg_performance: 0
      });
    } catch (error) {
      console.error('Failed to load strategy stats:', error);
      // Keep the default stats values on error
    }
  };

  const handleStrategyClick = (strategyId: string) => {
    setSelectedStrategyId(strategyId);
    setViewMode('detail');
  };

  const handleBackToList = () => {
    setViewMode('list');
    setSelectedStrategyId(null);
  };

  const handleStrategiesRegistered = (registeredIds: string[]) => {
    showToast.success(`Successfully registered ${registeredIds.length} strategies`);
    loadStrategies();
    loadStrategyStats();
  };

  const handleCreateStrategy = () => {
    setShowCreateModal(false);
    showToast.info('Strategy creation feature coming soon!');
  };

  const handleEditStrategy = (id: string) => {
    showToast.info(`Strategy editing feature coming soon for strategy ${id}`);
  };

  const handleRunBacktest = (strategyId: string, parameters?: Record<string, any>) => {
    console.log('Running backtest with parameters:', parameters);
    showToast.success(`Navigating to backtest configuration for strategy ${strategyId}`);
    // Navigate to backtests page and pass the strategy ID
    navigate('/backtests', { 
      state: { 
        openConfigModal: true, 
        preselectedStrategyId: strategyId,
        parameters 
      } 
    });
  };

  if (viewMode === 'detail' && selectedStrategyId) {
    return (
      <StrategyDetailView
        strategyId={selectedStrategyId}
        onBack={handleBackToList}
        onRunBacktest={handleRunBacktest}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Strategy Library</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage and create your trading strategies
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <StrategyDiscovery onStrategiesRegistered={handleStrategiesRegistered} />
          <Button
            icon={Plus}
            onClick={() => setShowCreateModal(true)}
            className="shadow-sm"
          >
            Create New Strategy
          </Button>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-primary-100 dark:bg-primary-900/50 rounded-lg">
              <Target className="h-6 w-6 text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {strategyStats.total_strategies}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Total Strategies</div>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-success-100 dark:bg-success-900/50 rounded-lg">
              <CheckCircle className="h-6 w-6 text-success-600 dark:text-success-400" />
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {strategyStats.active_strategies}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Active Strategies</div>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-warning-100 dark:bg-warning-900/50 rounded-lg">
              <BarChart3 className="h-6 w-6 text-warning-600 dark:text-warning-400" />
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {strategyStats.total_backtests}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Total Backtests</div>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-info-100 dark:bg-info-900/50 rounded-lg">
              <Target className="h-6 w-6 text-info-600 dark:text-info-400" />
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {(strategyStats.avg_performance || 0).toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Avg Performance</div>
            </div>
          </div>
        </Card>
      </div>

      {/* Search and Filter Controls */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search strategies..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
          />
        </div>
        
        <div className="flex items-center space-x-2">
          <Filter className="h-4 w-4 text-gray-400" />
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value as FilterType)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
          >
            <option value="all">All Strategies</option>
            <option value="active">Active Only</option>
            <option value="inactive">Inactive Only</option>
          </select>
        </div>
      </div>

      {/* Loading State */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      ) : (
        <>
          {/* Results Info */}
          <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
            <span>
              Showing {(filteredStrategies || []).length} of {(strategies || []).length} strategies
            </span>
            {searchTerm && (
              <span>Search: "{searchTerm}"</span>
            )}
          </div>

          {/* Strategies Grid */}
          {(filteredStrategies || []).length === 0 ? (
            <Card className="text-center py-12">
              <AlertTriangle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                {(strategies || []).length === 0 ? 'No Strategies Found' : 'No Matching Strategies'}
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                {(strategies || []).length === 0 
                  ? 'Start by discovering existing strategies or creating a new one.'
                  : 'Try adjusting your search or filter criteria.'
                }
              </p>
              {(strategies || []).length === 0 && (
                <div className="flex justify-center space-x-3">
                  <StrategyDiscovery onStrategiesRegistered={handleStrategiesRegistered} />
                  <Button
                    icon={Plus}
                    onClick={() => setShowCreateModal(true)}
                  >
                    Create Strategy
                  </Button>
                </div>
              )}
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {(filteredStrategies || []).map((strategy) => (
                <div
                  key={strategy.id} 
                  className="p-6 hover:shadow-lg transition-all duration-200 cursor-pointer bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-soft"
                  onClick={() => handleStrategyClick(strategy.id)}
                >
                  <div className="space-y-4">
                    {/* Header */}
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="p-2 bg-primary-100 dark:bg-primary-900/50 rounded-lg">
                          <Target className="h-5 w-5 text-primary-600 dark:text-primary-400" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                            {strategy.name || 'Unnamed Strategy'}
                          </h3>
                          <div className="flex items-center space-x-2 mt-1">
                            <Badge variant={strategy.is_active ? 'success' : 'danger'} size="sm">
                              <CheckCircle className="h-3 w-3 mr-1" />
                              {strategy.is_active ? 'Active' : 'Inactive'}
                            </Badge>
                            {strategy.performance_summary && (
                              <span className="text-xs text-gray-500 dark:text-gray-400">
                                {strategy.performance_summary.total_backtests || 0} runs
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Description */}
                    <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                      {strategy.description || 'No description available'}
                    </p>

                    {/* Performance & Stats */}
                    {strategy.performance_summary ? (
                      <div className="grid grid-cols-2 gap-4 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                        <div>
                          <p className="text-xs text-gray-500 dark:text-gray-400">Avg Performance</p>
                          <p className={`font-semibold ${
                            (strategy.performance_summary.avg_return || 0) >= 0 
                              ? 'text-success-600 dark:text-success-400' 
                              : 'text-danger-600 dark:text-danger-400'
                          }`}>
                            {(strategy.performance_summary.avg_return || 0).toFixed(2)}%
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 dark:text-gray-400">Last Run</p>
                          <div className="flex items-center space-x-1">
                            <Clock className="h-3 w-3 text-gray-400" />
                            <p className="text-xs font-medium text-gray-700 dark:text-gray-300">
                              {strategy.last_backtest_at 
                                ? new Date(strategy.last_backtest_at).toLocaleDateString()
                                : 'Never'
                              }
                            </p>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg text-center">
                        <p className="text-xs text-gray-500 dark:text-gray-400">No backtest data available</p>
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex space-x-2 pt-2">
                      <Button
                        variant="nav"
                        size="sm"
                        icon={Edit3}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleEditStrategy(strategy.id);
                        }}
                        className="flex-1"
                      >
                        Edit
                      </Button>
                      <Button
                        variant="action"
                        size="sm"
                        icon={Play}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRunBacktest(strategy.id);
                        }}
                        className="flex-1"
                        disabled={!strategy.is_active}
                      >
                        Run Backtest
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Create Strategy Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create New Strategy"
        size="md"
      >
        <div className="space-y-4">
          <p className="text-gray-600 dark:text-gray-400">
            This will open the strategy editor where you can create a new trading strategy.
            Feature coming soon!
          </p>
          <div className="flex justify-end space-x-3">
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateStrategy}>
              Continue to Editor
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default Strategies;
