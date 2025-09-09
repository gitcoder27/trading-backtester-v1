import React, { useState } from 'react';
import { Settings, Target, Filter, Play } from 'lucide-react';
import Modal from '../../ui/Modal';
import Button from '../../ui/Button';
import StrategySection from './StrategySection';
import ExecutionSection from './ExecutionSection';
import FiltersSection from './FiltersSection';
import { useBacktestForm } from './useBacktestForm';
import type { EnhancedBacktestModalProps, TabType } from './types';

const EnhancedBacktestModal: React.FC<EnhancedBacktestModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  isSubmitting = false,
  preselectedStrategyId,
  preselectedParameters
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('strategy');
  
  const {
    strategies,
    datasets,
    config,
    handleConfigChange,
    handleParametersChange,
    validateAndConvertConfig,
    resetForm
  } = useBacktestForm(isOpen, preselectedStrategyId, preselectedParameters);

  const handleSubmit = () => {
    const baseConfig = validateAndConvertConfig();
    if (baseConfig) {
      onSubmit(baseConfig);
    }
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const tabs = [
    { id: 'strategy', label: 'Strategy & Data', icon: Settings },
    { id: 'execution', label: 'Execution & Risk', icon: Target },
    { id: 'filters', label: 'Filters & Rules', icon: Filter }
  ] as const;

  const renderTabContent = () => {
    switch (activeTab) {
      case 'strategy':
        return (
          <StrategySection
            strategies={strategies}
            datasets={datasets}
            config={config}
            onConfigChange={handleConfigChange}
            onParametersChange={handleParametersChange}
          />
        );
      case 'execution':
        return (
          <ExecutionSection
            config={config}
            onConfigChange={handleConfigChange}
          />
        );
      case 'filters':
        return (
          <FiltersSection
            config={config}
            onConfigChange={handleConfigChange}
          />
        );
      default:
        return null;
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Configure Backtest" size="xl">
      <div className="space-y-6">
        {/* Tab Navigation */}
        <div className="border-b border-gray-200 dark:border-gray-700">
          <nav className="-mb-px flex space-x-8">
            {tabs.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                  activeTab === id
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="min-h-[400px]">
          {renderTabContent()}
        </div>

        {/* Actions */}
        <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-700">
          <Button
            variant="secondary"
            onClick={handleClose}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting || !config.strategy_id || !config.dataset_id}
            loading={isSubmitting}
          >
            <Play className="w-4 h-4 mr-2" />
            Start Backtest
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default EnhancedBacktestModal;
