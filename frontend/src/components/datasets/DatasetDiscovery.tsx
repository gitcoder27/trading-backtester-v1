import React, { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, CheckCircle, Database, RefreshCw, Search } from 'lucide-react';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import Modal from '../ui/Modal';
import { showToast } from '../ui/Toast';
import { DatasetService } from '../../services/dataset';
import type { DatasetDiscoveryItem, DatasetDiscoveryResponse } from '../../types';

interface DatasetDiscoveryProps {
  onDatasetsRegistered?: (ids: (number | string)[]) => void;
}

const DatasetDiscovery: React.FC<DatasetDiscoveryProps> = ({ onDatasetsRegistered }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const [discoveredDatasets, setDiscoveredDatasets] = useState<DatasetDiscoveryItem[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedPaths, setSelectedPaths] = useState<string[]>([]);
  const [dataDirectory, setDataDirectory] = useState<string | undefined>(undefined);

  const filteredDatasets = useMemo(() => {
    if (!searchTerm) return discoveredDatasets;
    const q = searchTerm.toLowerCase();
    return discoveredDatasets.filter((dataset) => {
      const name = dataset.name || '';
      return name.toLowerCase().includes(q) || dataset.file_path.toLowerCase().includes(q);
    });
  }, [discoveredDatasets, searchTerm]);

  const refreshDiscovery = async () => {
    setIsDiscovering(true);
    try {
      const result: DatasetDiscoveryResponse = await DatasetService.discoverLocalDatasets();
      const datasets = Array.isArray(result.datasets) ? result.datasets : [];
      setDiscoveredDatasets(datasets);
      setDataDirectory(result.data_directory);
      setSelectedPaths([]);
      showToast.success(`Discovered ${datasets.length} dataset${datasets.length === 1 ? '' : 's'}`);
    } catch (error) {
      console.error('Failed to discover datasets:', error);
      setDiscoveredDatasets([]);
      showToast.error('Failed to discover datasets');
    } finally {
      setIsDiscovering(false);
    }
  };

  const handleOpen = () => {
    setIsOpen(true);
  };

  useEffect(() => {
    if (isOpen) {
      refreshDiscovery();
    }
  }, [isOpen]);

  const toggleSelection = (filePath: string, disabled: boolean) => {
    if (disabled) return;
    setSelectedPaths((prev) =>
      prev.includes(filePath) ? prev.filter((path) => path !== filePath) : [...prev, filePath]
    );
  };

  const selectAll = () => {
    const selectable = discoveredDatasets
      .filter((dataset) => !dataset.registered && !dataset.error)
      .map((dataset) => dataset.file_path);
    setSelectedPaths(selectable);
  };

  const clearSelection = () => setSelectedPaths([]);

  const registerSelected = async () => {
    if (selectedPaths.length === 0) {
      showToast.warning('Select at least one dataset to register');
      return;
    }
    setIsRegistering(true);
    try {
      const result = await DatasetService.registerLocalDatasets(selectedPaths);
      const registered = result.registered || [];
      const skipped = result.skipped || [];
      const errors = result.errors || [];

      if (registered.length > 0) {
        showToast.success(`Registered ${registered.length} dataset${registered.length === 1 ? '' : 's'}`);
        onDatasetsRegistered?.(registered);
      } else if (skipped.length === 0) {
        showToast.info('No datasets were registered');
      }

      if (skipped.length > 0) {
        showToast.info(`${skipped.length} dataset${skipped.length === 1 ? '' : 's'} already registered`);
      }

      if (errors.length > 0) {
        errors.forEach((err) => console.error('Dataset registration error:', err));
        showToast.error(`${errors.length} dataset${errors.length === 1 ? '' : 's'} failed to register`);
      }

      await refreshDiscovery();
    } catch (error) {
      console.error('Failed to register datasets:', error);
      showToast.error('Failed to register datasets');
    } finally {
      setIsRegistering(false);
      setIsOpen(false);
    }
  };

  return (
    <>
      <Button variant="outline" onClick={handleOpen} icon={Database}>
        Discover Datasets
      </Button>

      <Modal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="Discover Local Datasets"
        size="lg"
      >
        <div className="space-y-6">
          {dataDirectory && (
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Scanning directory: <span className="font-medium text-gray-900 dark:text-gray-100">{dataDirectory}</span>
            </div>
          )}

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Button
                icon={RefreshCw}
                variant="outline"
                size="sm"
                onClick={refreshDiscovery}
                disabled={isDiscovering}
              >
                {isDiscovering ? 'Discovering...' : 'Refresh'}
              </Button>
              {discoveredDatasets.length > 0 && (
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Found {discoveredDatasets.length} dataset{discoveredDatasets.length === 1 ? '' : 's'}
                </span>
              )}
            </div>
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm" onClick={selectAll}>
                Select All
              </Button>
              <Button variant="outline" size="sm" onClick={clearSelection}>
                Clear
              </Button>
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {selectedPaths.length} selected
              </span>
            </div>
          </div>

          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search datasets by name or path"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
            />
          </div>

          <div className="max-h-96 overflow-y-auto space-y-3">
            {isDiscovering ? (
              <div className="flex items-center justify-center py-10 text-gray-600 dark:text-gray-400">
                <RefreshCw className="h-6 w-6 animate-spin mr-2" /> Discovering datasets...
              </div>
            ) : filteredDatasets.length === 0 ? (
              <div className="text-center py-10 text-gray-500 dark:text-gray-400">
                {searchTerm ? 'No datasets match your search' : 'No datasets found in the data directory'}
              </div>
            ) : (
              filteredDatasets.map((dataset) => {
                const disabled = dataset.registered || !!dataset.error;
                const isSelected = selectedPaths.includes(dataset.file_path);
                return (
                  <button
                    key={dataset.file_path}
                    type="button"
                    onClick={() => toggleSelection(dataset.file_path, disabled)}
                    className={`w-full text-left p-4 rounded-xl border transition-shadow ${
                      isSelected ? 'border-primary-500 shadow-md' : 'border-gray-200 dark:border-gray-700'
                    } ${disabled ? 'cursor-not-allowed opacity-80' : 'hover:shadow-md'}`}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center space-x-2">
                          <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                            {dataset.name || dataset.file_path.split('/').pop()}
                          </h3>
                          {dataset.registered && (
                            <Badge variant="success" className="flex items-center space-x-1">
                              <CheckCircle className="h-3 w-3" />
                              <span>Registered</span>
                            </Badge>
                          )}
                          {dataset.error && (
                            <Badge variant="danger" className="flex items-center space-x-1">
                              <AlertTriangle className="h-3 w-3" />
                              <span>Error</span>
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 break-all">
                          {dataset.file_path}
                        </p>
                      </div>
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleSelection(dataset.file_path, disabled)}
                        disabled={disabled}
                        className="mt-1 h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                      />
                    </div>

                    <div className="mt-3 grid grid-cols-2 gap-2 text-sm text-gray-700 dark:text-gray-300">
                      <span>Rows: {dataset.rows_count ?? 'Unknown'}</span>
                      <span>Size: {dataset.file_size ? `${(dataset.file_size / (1024 * 1024)).toFixed(2)} MB` : 'Unknown'}</span>
                      <span>Timeframe: {dataset.timeframe || 'Unknown'}</span>
                      <span>Quality: {dataset.quality_score ? `${dataset.quality_score}` : 'N/A'}</span>
                    </div>

                    {dataset.error && (
                      <p className="mt-2 text-sm text-danger-600 dark:text-danger-400 flex items-center space-x-2">
                        <AlertTriangle className="h-4 w-4" />
                        <span>{dataset.error}</span>
                      </p>
                    )}
                  </button>
                );
              })
            )}
          </div>

          <div className="flex justify-end space-x-3">
            <Button variant="outline" onClick={() => setIsOpen(false)}>
              Close
            </Button>
            <Button onClick={registerSelected} disabled={isRegistering || selectedPaths.length === 0}>
              {isRegistering ? 'Registering…' : 'Register Selected'}
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
};

export default DatasetDiscovery;
