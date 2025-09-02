import React, { useState, useEffect } from 'react';
import { ArrowLeft, Play, ToggleLeft, ToggleRight, CheckCircle, AlertCircle, TrendingUp, Calendar, Settings } from 'lucide-react';
import Button from '../ui/Button';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import Modal from '../ui/Modal';
import { showToast } from '../ui/Toast';
import StrategyParameterForm from './StrategyParameterForm';
import { StrategyService } from '../../services/strategyService';
import type { Strategy, ParameterSchema } from '../../types';

interface StrategyDetailViewProps {
  strategyId: string;
  onBack: () => void;
  onRunBacktest?: (strategyId: string, parameters: Record<string, any>) => void;
}

const StrategyDetailView: React.FC<StrategyDetailViewProps> = ({
  strategyId,
  onBack,
  onRunBacktest
}) => {
  const [strategy, setStrategy] = useState<Strategy | null>(null);
  const [parameterSchema, setParameterSchema] = useState<ParameterSchema[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isValidating, setIsValidating] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [currentParameters, setCurrentParameters] = useState<Record<string, any>>({});
  const [showBacktestModal, setShowBacktestModal] = useState(false);

  useEffect(() => {
    loadStrategyDetails();
  }, [strategyId]);

  const loadStrategyDetails = async () => {
    setIsLoading(true);
    try {
      const [strategyData, schema] = await Promise.all([
        StrategyService.getStrategy(strategyId),
        StrategyService.getStrategySchema(strategyId)
      ]);
      
      setStrategy(strategyData);
      setParameterSchema(schema);
      
      // Initialize parameters with defaults
      const defaultParams: Record<string, any> = {};
      schema.forEach(param => {
        if (param.default !== undefined) {
          defaultParams[param.name] = param.default;
        }
      });
      setCurrentParameters(defaultParams);
    } catch (error) {
      console.error('Failed to load strategy details:', error);
      showToast.error('Failed to load strategy details');
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleActive = async () => {
    if (!strategy) return;
    
    try {
      const updatedStrategy = await StrategyService.toggleStrategy(strategyId, !strategy.is_active);
      setStrategy(updatedStrategy);
      showToast.success(`Strategy ${updatedStrategy.is_active ? 'activated' : 'deactivated'}`);
    } catch (error) {
      console.error('Failed to toggle strategy:', error);
      showToast.error('Failed to update strategy status');
    }
  };

  const handleValidateParameters = async (parameters: Record<string, any>) => {
    setIsValidating(true);
    setValidationErrors([]);
    try {
      const result = await StrategyService.validateStrategy(strategyId, parameters);
      if (result.is_valid) {
        showToast.success('Parameters are valid!');
        setValidationErrors([]);
      } else {
        setValidationErrors(result.errors);
        showToast.error('Parameter validation failed');
      }
    } catch (error) {
      console.error('Failed to validate parameters:', error);
      showToast.error('Failed to validate parameters');
    } finally {
      setIsValidating(false);
    }
  };

  const handleRunBacktest = () => {
    if (onRunBacktest) {
      onRunBacktest(strategyId, currentParameters);
      setShowBacktestModal(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!strategy) {
    return (
      <div className="text-center py-8">
        <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">Strategy Not Found</h3>
        <p className="text-gray-600 dark:text-gray-400 mb-4">The requested strategy could not be loaded.</p>
        <Button onClick={onBack} icon={ArrowLeft}>Back to Strategies</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="outline"
            size="sm"
            icon={ArrowLeft}
            onClick={onBack}
          >
            Back
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{strategy.name}</h1>
            <p className="text-gray-600 dark:text-gray-400">{strategy.description || 'No description available'}</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            icon={strategy.is_active ? ToggleRight : ToggleLeft}
            onClick={handleToggleActive}
            className={strategy.is_active ? 'text-success-600' : 'text-gray-500'}
          >
            {strategy.is_active ? 'Active' : 'Inactive'}
          </Button>
          <Button
            icon={Play}
            onClick={() => setShowBacktestModal(true)}
            disabled={!strategy.is_active}
          >
            Run Backtest
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Strategy Info */}
        <Card className="lg:col-span-1">
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center">
              <Settings className="h-5 w-5 mr-2" />
              Strategy Information
            </h3>
            
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium text-gray-600 dark:text-gray-400">Status</label>
                <div className="mt-1">
                  <Badge variant={strategy.is_active ? 'success' : 'danger'}>
                    <CheckCircle className="h-3 w-3 mr-1" />
                    {strategy.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                </div>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-600 dark:text-gray-400">File Path</label>
                <p className="text-sm text-gray-900 dark:text-gray-100 mt-1 font-mono break-all">
                  {strategy.file_path}
                </p>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-600 dark:text-gray-400">Created</label>
                <div className="flex items-center mt-1 text-sm text-gray-900 dark:text-gray-100">
                  <Calendar className="h-4 w-4 mr-1" />
                  {new Date(strategy.created_at).toLocaleDateString()}
                </div>
              </div>
              
              {strategy.last_backtest_at && (
                <div>
                  <label className="text-sm font-medium text-gray-600 dark:text-gray-400">Last Backtest</label>
                  <div className="flex items-center mt-1 text-sm text-gray-900 dark:text-gray-100">
                    <TrendingUp className="h-4 w-4 mr-1" />
                    {new Date(strategy.last_backtest_at).toLocaleDateString()}
                  </div>
                </div>
              )}
            </div>
          </div>
        </Card>

        {/* Performance Summary */}
        {strategy.performance_summary && (
          <Card className="lg:col-span-2">
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center">
                <TrendingUp className="h-5 w-5 mr-2" />
                Performance Summary
              </h3>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                  <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {strategy.performance_summary.total_backtests}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Total Backtests</div>
                </div>
                
                <div className="text-center p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                  <div className="text-2xl font-bold text-success-600 dark:text-success-400">
                    {strategy.performance_summary.avg_return.toFixed(2)}%
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Avg Return</div>
                </div>
                
                <div className="text-center p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                  <div className="text-2xl font-bold text-success-600 dark:text-success-400">
                    {strategy.performance_summary.best_return.toFixed(2)}%
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Best Return</div>
                </div>
                
                <div className="text-center p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                  <div className="text-2xl font-bold text-danger-600 dark:text-danger-400">
                    {strategy.performance_summary.worst_return.toFixed(2)}%
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Worst Return</div>
                </div>
              </div>
            </div>
          </Card>
        )}
      </div>

      {/* Parameter Configuration */}
      {parameterSchema.length > 0 && (
        <Card>
          <StrategyParameterForm
            schema={parameterSchema}
            initialValues={currentParameters}
            onParametersChange={setCurrentParameters}
            onValidate={handleValidateParameters}
            isValidating={isValidating}
            validationErrors={validationErrors}
          />
        </Card>
      )}

      {/* Backtest Modal */}
      <Modal
        isOpen={showBacktestModal}
        onClose={() => setShowBacktestModal(false)}
        title="Run Backtest"
        size="md"
      >
        <div className="space-y-4">
          <p className="text-gray-600 dark:text-gray-400">
            Run a backtest with the current parameter configuration for strategy "{strategy.name}".
          </p>
          
          <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Current Parameters:</h4>
            {Object.keys(currentParameters).length > 0 ? (
              <div className="space-y-1 text-sm">
                {Object.entries(currentParameters).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">{key}:</span>
                    <span className="font-mono text-gray-900 dark:text-gray-100">
                      {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400">No parameters configured</p>
            )}
          </div>
          
          <div className="flex justify-end space-x-3">
            <Button
              variant="outline"
              onClick={() => setShowBacktestModal(false)}
            >
              Cancel
            </Button>
            <Button
              icon={Play}
              onClick={handleRunBacktest}
            >
              Start Backtest
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default StrategyDetailView;
