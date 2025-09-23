import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Target, BarChart3, CheckCircle } from 'lucide-react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Modal from '../../components/ui/Modal';
import { showToast } from '../../components/ui/Toast';
import StrategyDetailView from '../../components/strategies/StrategyDetailView';
import StrategyDiscovery from '../../components/strategies/StrategyDiscovery';
import EnhancedBacktestModal from '../../components/modals/BacktestModal';
import { JobService } from '../../services/backtest';
import { StrategyService } from '../../services/strategyService';
import StrategyEditorModal from '../../components/strategies/StrategyEditorModal';
import type { BacktestConfig, Strategy as StrategyType } from '../../types';
import { useStrategiesData } from '../../hooks/useStrategiesData';
import StrategiesToolbar from '../../components/strategies/StrategiesToolbar';
import StrategiesGrid from '../../components/strategies/StrategiesGrid';

type ViewMode = 'list' | 'detail';
type FilterType = 'all' | 'active' | 'inactive';

const Strategies: React.FC = () => {
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [selectedStrategyId, setSelectedStrategyId] = useState<string | null>(null);
  const { strategies, stats: strategyStats, loading: isLoading, refetch } = useStrategiesData();
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<FilterType>('all');
  const [editorState, setEditorState] = useState<{ mode: 'edit' | 'create'; strategy?: StrategyType | null } | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<StrategyType | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  // Backtest modal state (open from Strategies without navigating)
  const [showBacktestModal, setShowBacktestModal] = useState(false);
  const [preselectedStrategyId, setPreselectedStrategyId] = useState<string | number | undefined>(undefined);
  const [preselectedParameters, setPreselectedParameters] = useState<Record<string, any> | undefined>(undefined);
  const [submittingBacktest, setSubmittingBacktest] = useState(false);

  const filteredStrategies = useMemo(() => {
    let filtered = Array.isArray(strategies) ? strategies : [];
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      filtered = filtered.filter((s) =>
        s.name.toLowerCase().includes(q) || (s.description && s.description.toLowerCase().includes(q))
      );
    }
    if (filterType !== 'all') {
      filtered = filtered.filter((s) => (filterType === 'active' ? s.is_active : !s.is_active));
    }
    return filtered;
  }, [strategies, searchTerm, filterType]);

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
    refetch();
  };

  const handleCreateStrategy = () => {
    setEditorState({ mode: 'create' });
  };

  const handleEditStrategy = (strategy: StrategyType) => {
    setEditorState({ mode: 'edit', strategy });
  };

  const handleRequestDelete = (strategy: StrategyType) => {
    setDeleteTarget(strategy);
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      setIsDeleting(true);
      const result = await StrategyService.deleteStrategy(deleteTarget.id);

      const archivePath = result.archive_path;
      const baseMessage = result.file_removed
        ? archivePath
          ? `Strategy deleted. Archived at ${archivePath}`
          : 'Strategy deleted and archived'
        : 'Strategy record deleted';
      showToast.success(baseMessage);

      if (result.shared_module) {
        showToast.warning('Strategy module is shared; source file left in place.');
      } else if (!result.file_removed) {
        showToast.warning('Strategy file missing; only database entry removed.');
      }

      if (selectedStrategyId === deleteTarget.id) {
        handleBackToList();
      }
      setEditorState(null);
      setDeleteTarget(null);
      refetch();
    } catch (error) {
      console.error('Failed to delete strategy:', error);
      const message = error instanceof Error ? error.message : 'Failed to delete strategy';
      showToast.error(message);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleRunBacktest = (strategyId: string, parameters?: Record<string, any>) => {
    // Open configure modal locally without navigating away
    setPreselectedStrategyId(strategyId);
    setPreselectedParameters(parameters);
    setShowBacktestModal(true);
  };

  const handleSubmitBacktest = async (config: BacktestConfig) => {
    try {
      setSubmittingBacktest(true);
      await JobService.submitBackgroundJob(config);
      showToast.success('Backtest job submitted successfully!');
      setShowBacktestModal(false);
      // Navigate to Backtests to monitor progress after starting
      navigate('/backtests');
    } catch (error) {
      console.error('Failed to submit backtest:', error);
      showToast.error('Failed to submit backtest job');
    } finally {
      setSubmittingBacktest(false);
      // Clear preselected values after closing
      setPreselectedStrategyId(undefined);
      setPreselectedParameters(undefined);
    }
  };

  if (viewMode === 'detail' && selectedStrategyId) {
    return (
      <>
        <StrategyDetailView
          strategyId={selectedStrategyId}
          onBack={handleBackToList}
          onRunBacktest={handleRunBacktest}
        />
        <EnhancedBacktestModal
          isOpen={showBacktestModal}
          onClose={() => {
            setShowBacktestModal(false);
            setPreselectedStrategyId(undefined);
            setPreselectedParameters(undefined);
          }}
          onSubmit={handleSubmitBacktest}
          isSubmitting={submittingBacktest}
          preselectedStrategyId={preselectedStrategyId}
          preselectedParameters={preselectedParameters}
        />
      </>
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
            onClick={handleCreateStrategy}
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

      <StrategiesToolbar
        search={searchTerm}
        onSearchChange={setSearchTerm}
        filter={filterType}
        onFilterChange={setFilterType}
      />

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

          <StrategiesGrid
            strategies={filteredStrategies}
            allCount={(strategies || []).length}
            onClick={handleStrategyClick}
            onEdit={handleEditStrategy}
            onRunBacktest={handleRunBacktest}
            onDiscoverClick={handleStrategiesRegistered}
            onCreate={handleCreateStrategy}
            onDelete={handleRequestDelete}
          />
        </>
      )}

      <StrategyEditorModal
        isOpen={!!editorState}
        mode={editorState?.mode ?? 'create'}
        strategy={editorState?.strategy ?? undefined}
        onClose={() => setEditorState(null)}
        onSaved={() => {
          setEditorState(null);
          refetch();
        }}
      />

      <Modal
        isOpen={!!deleteTarget}
        onClose={() => {
          if (!isDeleting) {
            setDeleteTarget(null);
          }
        }}
        title="Delete Strategy"
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Are you sure you want to delete{' '}
            <span className="font-semibold text-gray-900 dark:text-gray-100">{deleteTarget?.name || 'this strategy'}</span>?
            The strategy file will be moved to the archive and the database entry removed.
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-500">
            Existing backtest results keep their historical data and references to the deleted strategy name.
          </p>
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={() => setDeleteTarget(null)} disabled={isDeleting}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleConfirmDelete} loading={isDeleting}>
              Delete Strategy
            </Button>
          </div>
        </div>
      </Modal>

      {/* Configure Backtest Modal (local) */}
      <EnhancedBacktestModal
        isOpen={showBacktestModal}
        onClose={() => {
          setShowBacktestModal(false);
          setPreselectedStrategyId(undefined);
          setPreselectedParameters(undefined);
        }}
        onSubmit={handleSubmitBacktest}
        isSubmitting={submittingBacktest}
        preselectedStrategyId={preselectedStrategyId}
        preselectedParameters={preselectedParameters}
      />
    </div>
  );
};

export default Strategies;
