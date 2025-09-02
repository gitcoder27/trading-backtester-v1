import React, { useState, useEffect } from 'react';
import { Search, RefreshCw, CheckCircle, AlertTriangle, Plus, FileText } from 'lucide-react';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import Modal from '../ui/Modal';
import { showToast } from '../ui/Toast';
import { StrategyService } from '../../services/strategyService';
import type { StrategyDiscoveryResult } from '../../services/strategyService';

interface StrategyDiscoveryProps {
  onStrategiesRegistered?: (strategies: string[]) => void;
}

const StrategyDiscovery: React.FC<StrategyDiscoveryProps> = ({ onStrategiesRegistered }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const [discoveredStrategies, setDiscoveredStrategies] = useState<StrategyDiscoveryResult[]>([]);
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState('');

  const filteredStrategies = (discoveredStrategies || []).filter(strategy =>
    strategy.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    strategy.module_path.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const discoverStrategies = async () => {
    setIsDiscovering(true);
    try {
      const strategies = await StrategyService.discoverStrategies();
      setDiscoveredStrategies(Array.isArray(strategies) ? strategies : []);
      showToast.success(`Discovered ${(strategies || []).length} strategies`);
    } catch (error) {
      console.error('Failed to discover strategies:', error);
      showToast.error('Failed to discover strategies');
      setDiscoveredStrategies([]); // Ensure we set empty array on error
    } finally {
      setIsDiscovering(false);
    }
  };

  const registerSelectedStrategies = async () => {
    if (selectedStrategies.length === 0) {
      showToast.warning('Please select at least one strategy to register');
      return;
    }

    setIsRegistering(true);
    try {
      const result = await StrategyService.registerStrategies(selectedStrategies);
      const registeredCount = result.registered || 0;
      const updatedCount = result.updated || 0;
      const totalProcessed = registeredCount + updatedCount;
      
      if (totalProcessed > 0) {
        showToast.success(`Successfully processed ${totalProcessed} strategies (${registeredCount} new, ${updatedCount} updated)`);
        onStrategiesRegistered?.(selectedStrategies); // Pass the selected IDs
      } else {
        showToast.warning('No strategies were registered');
      }
      
      if (result.errors && result.errors.length > 0) {
        console.error('Registration errors:', result.errors);
        showToast.error(`Some strategies had errors: ${result.errors.length} errors`);
      }
      
      setIsOpen(false);
      setSelectedStrategies([]);
    } catch (error) {
      console.error('Failed to register strategies:', error);
      showToast.error('Failed to register strategies');
    } finally {
      setIsRegistering(false);
    }
  };

  const toggleStrategySelection = (strategyId: string) => {
    setSelectedStrategies(prev => 
      prev.includes(strategyId)
        ? prev.filter(id => id !== strategyId)
        : [...prev, strategyId]
    );
  };

  const selectAllValid = () => {
    const validStrategyIds = (discoveredStrategies || [])
      .filter(s => s.is_valid)
      .map(s => s.id);
    setSelectedStrategies(validStrategyIds);
  };

  const selectNone = () => {
    setSelectedStrategies([]);
  };

  useEffect(() => {
    if (isOpen && (discoveredStrategies || []).length === 0) {
      discoverStrategies();
    }
  }, [isOpen]);

  return (
    <>
      <Button
        icon={Search}
        variant="outline"
        onClick={() => setIsOpen(true)}
      >
        Discover Strategies
      </Button>

      <Modal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="Strategy Discovery"
        size="lg"
      >
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button
                icon={RefreshCw}
                variant="outline"
                size="sm"
                onClick={discoverStrategies}
                disabled={isDiscovering}
              >
                {isDiscovering ? 'Discovering...' : 'Refresh'}
              </Button>
              
              {(discoveredStrategies || []).length > 0 && (
                <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
                  <span>Found: {(discoveredStrategies || []).length}</span>
                  <span>•</span>
                  <span className="text-success-600 dark:text-success-400">
                    Valid: {(discoveredStrategies || []).filter(s => s.is_valid).length}
                  </span>
                  <span>•</span>
                  <span className="text-danger-600 dark:text-danger-400">
                    Invalid: {(discoveredStrategies || []).filter(s => !s.is_valid).length}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search strategies..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
            />
          </div>

          {/* Selection Controls */}
          {(filteredStrategies || []).length > 0 && (
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={selectAllValid}
                >
                  Select All Valid
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={selectNone}
                >
                  Select None
                </Button>
              </div>
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {selectedStrategies.length} selected
              </span>
            </div>
          )}

          {/* Strategies List */}
          <div className="max-h-96 overflow-y-auto space-y-3">
            {isDiscovering ? (
              <div className="flex items-center justify-center py-8">
                <RefreshCw className="h-6 w-6 animate-spin text-primary-600" />
                <span className="ml-2 text-gray-600 dark:text-gray-400">Discovering strategies...</span>
              </div>
            ) : (filteredStrategies || []).length === 0 ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                {searchTerm ? 'No strategies match your search' : 'No strategies found'}
              </div>
            ) : (
              filteredStrategies.map((strategy) => (
                <div
                  key={strategy.id}
                  className={`p-4 cursor-pointer transition-all bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-soft ${
                    selectedStrategies.includes(strategy.id)
                      ? 'ring-2 ring-primary-500 bg-primary-50 dark:bg-primary-900/20'
                      : 'hover:shadow-md'
                  }`}
                  onClick={(e) => {
                    // Prevent double-triggering from checkbox
                    if ((e.target as HTMLElement).tagName !== 'INPUT' && strategy.is_valid) {
                      toggleStrategySelection(strategy.id);
                    }
                  }}
                >
                  <div className="flex items-start space-x-3">
                    {/* Selection Checkbox */}
                    <input
                      type="checkbox"
                      checked={selectedStrategies.includes(strategy.id)}
                      onChange={(e) => {
                        e.stopPropagation();
                        if (strategy.is_valid) {
                          toggleStrategySelection(strategy.id);
                        }
                      }}
                      disabled={!strategy.is_valid}
                      className="mt-1 w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500"
                    />

                    {/* Strategy Icon */}
                    <div className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
                      <FileText className="h-4 w-4 text-gray-600 dark:text-gray-400" />
                    </div>

                    {/* Strategy Details */}
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium text-gray-900 dark:text-gray-100">
                          {strategy.name}
                        </h4>
                        <div className="flex items-center space-x-2">
                          {strategy.is_valid ? (
                            <Badge variant="success" size="sm">
                              <CheckCircle className="h-3 w-3 mr-1" />
                              Valid
                            </Badge>
                          ) : (
                            <Badge variant="danger" size="sm">
                              <AlertTriangle className="h-3 w-3 mr-1" />
                              Invalid
                            </Badge>
                          )}
                        </div>
                      </div>

                      <div className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
                        <div>
                          <span className="font-medium">Module:</span> {strategy.module_path}
                        </div>
                        <div>
                          <span className="font-medium">Class:</span> {strategy.class_name}
                        </div>
                        {strategy.description && (
                          <div>
                            <span className="font-medium">Description:</span> {strategy.description}
                          </div>
                        )}
                      </div>

                      {/* Parameters Schema Preview */}
                      {strategy.parameters_schema && strategy.parameters_schema.length > 0 && (
                        <div className="flex items-center space-x-2 text-xs text-gray-500 dark:text-gray-400">
                          <span>Parameters:</span>
                          <div className="flex flex-wrap gap-1">
                            {strategy.parameters_schema.slice(0, 3).map((param, index) => (
                              <Badge key={index} variant="primary" size="sm">
                                {param.name}
                              </Badge>
                            ))}
                            {strategy.parameters_schema.length > 3 && (
                              <span>+{strategy.parameters_schema.length - 3} more</span>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Validation Errors */}
                      {!strategy.is_valid && strategy.validation_errors && (
                        <div className="mt-2 p-2 bg-red-50 dark:bg-red-900/20 rounded text-xs text-red-600 dark:text-red-400">
                          <div className="font-medium mb-1">Validation Errors:</div>
                          <ul className="list-disc list-inside space-y-1">
                            {strategy.validation_errors.map((error, index) => (
                              <li key={index}>{error}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer Actions */}
          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <Button
              variant="outline"
              onClick={() => setIsOpen(false)}
            >
              Cancel
            </Button>
            <Button
              icon={Plus}
              onClick={registerSelectedStrategies}
              disabled={selectedStrategies.length === 0 || isRegistering}
            >
              {isRegistering 
                ? 'Registering...' 
                : `Register ${selectedStrategies.length} Strategies`
              }
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
};

export default StrategyDiscovery;
