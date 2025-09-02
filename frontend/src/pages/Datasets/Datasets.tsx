import React, { useState } from 'react';
import { Database, Upload, Eye, Download, Trash2, TrendingUp, Calendar, HardDrive } from 'lucide-react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import FileUpload from '../../components/ui/FileUpload';
import Modal from '../../components/ui/Modal';
import { toast } from 'react-hot-toast';
import type { Dataset } from '../../types';

const Datasets: React.FC = () => {
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [uploadingFile, setUploadingFile] = useState<File | null>(null);

  // Mock data for now (will be replaced with real API calls)
  const datasets = {
    items: [
      {
        id: '1',
        name: 'NIFTY 2024 Data',
        symbol: 'NIFTY',
        timeframe: '1m',
        file_path: '/data/nifty_2024.csv',
        file_size: 15678900,
        record_count: 125432,
        start_date: '2024-01-01',
        end_date: '2024-12-31',
        created_at: '2024-08-30T10:00:00Z',
        updated_at: '2024-08-30T10:00:00Z',
        quality_score: 95,
      },
      {
        id: '2',
        name: 'BANKNIFTY Q3 2024',
        symbol: 'BANKNIFTY',
        timeframe: '5m',
        file_path: '/data/banknifty_q3.csv',
        file_size: 8456123,
        record_count: 45678,
        start_date: '2024-07-01',
        end_date: '2024-09-30',
        created_at: '2024-08-29T14:30:00Z',
        updated_at: '2024-08-29T14:30:00Z',
        quality_score: 87,
      },
    ] as Dataset[]
  };

  const handleFileSelect = (file: File) => {
    setUploadingFile(file);
  };

  const handleUpload = () => {
    if (uploadingFile) {
      // Simulate upload
      setTimeout(() => {
        toast.success('Dataset uploaded successfully!');
        setShowUploadModal(false);
        setUploadingFile(null);
      }, 2000);
    }
  };

  const handlePreview = (dataset: Dataset) => {
    setSelectedDataset(dataset);
    setShowPreviewModal(true);
  };

  const handleDelete = (dataset: Dataset) => {
    if (confirm(`Are you sure you want to delete "${dataset.name}"? This action cannot be undone.`)) {
      toast.success('Dataset deleted successfully!');
    }
  };

  const formatFileSize = (bytes: number): string => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatNumber = (num: number): string => {
    return new Intl.NumberFormat().format(num);
  };

  const getQualityBadge = (score?: number) => {
    if (!score) return <Badge variant="gray">Not analyzed</Badge>;
    if (score >= 90) return <Badge variant="success">Excellent</Badge>;
    if (score >= 75) return <Badge variant="primary">Good</Badge>;
    if (score >= 60) return <Badge variant="warning">Fair</Badge>;
    return <Badge variant="danger">Poor</Badge>;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Dataset Management</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Upload and manage your market data files
          </p>
        </div>
        <Button
          icon={Upload}
          onClick={() => setShowUploadModal(true)}
          className="shadow-sm"
        >
          Upload Dataset
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-primary-100 dark:bg-primary-900/50 rounded-lg">
              <Database className="h-5 w-5 text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Datasets</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {datasets?.items.length || 0}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-success-100 dark:bg-success-900/50 rounded-lg">
              <TrendingUp className="h-5 w-5 text-success-600 dark:text-success-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Records</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {formatNumber(datasets?.items.reduce((sum, d) => sum + d.record_count, 0) || 0)}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-info-100 dark:bg-info-900/50 rounded-lg">
              <HardDrive className="h-5 w-5 text-info-600 dark:text-info-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Size</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {formatFileSize(datasets?.items.reduce((sum, d) => sum + d.file_size, 0) || 0)}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-warning-100 dark:bg-warning-900/50 rounded-lg">
              <Calendar className="h-5 w-5 text-warning-600 dark:text-warning-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Latest Upload</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {datasets?.items.length ? 'Today' : 'None'}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Datasets Grid */}
      {datasets?.items.length === 0 ? (
        <Card className="p-12 text-center">
          <Database className="h-16 w-16 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">No datasets yet</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Upload your first market data file to get started with backtesting
          </p>
          <Button
            icon={Upload}
            onClick={() => setShowUploadModal(true)}
          >
            Upload Your First Dataset
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {datasets?.items.map((dataset) => (
            <Card key={dataset.id} className="p-6 hover:shadow-lg transition-shadow">
              <div className="space-y-4">
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100 truncate">
                      {dataset.name}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {dataset.symbol} • {dataset.timeframe}
                    </p>
                  </div>
                  {getQualityBadge(dataset.quality_score)}
                </div>

                {/* Metrics */}
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Records:</span>
                    <span className="font-medium text-gray-900 dark:text-gray-100">
                      {formatNumber(dataset.record_count)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Size:</span>
                    <span className="font-medium text-gray-900 dark:text-gray-100">
                      {formatFileSize(dataset.file_size)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Period:</span>
                    <span className="font-medium text-gray-900 dark:text-gray-100">
                      {new Date(dataset.start_date).toLocaleDateString()} - {new Date(dataset.end_date).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex space-x-2 pt-2 border-t border-gray-200 dark:border-gray-700">
                  <Button
                    variant="outline"
                    size="sm"
                    icon={Eye}
                    onClick={() => handlePreview(dataset)}
                    className="flex-1"
                  >
                    Preview
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={Download}
                    aria-label="Download dataset"
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={Trash2}
                    onClick={() => handleDelete(dataset)}
                    className="text-danger-600 hover:text-danger-700"
                    aria-label="Delete dataset"
                  />
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Upload Modal */}
      <Modal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        title="Upload Market Data"
        size="lg"
      >
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
              Select CSV File
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Upload OHLC market data in CSV format with timestamp, open, high, low, close columns.
            </p>
          </div>

          <FileUpload
            onFileSelect={handleFileSelect}
            onFileRemove={() => setUploadingFile(null)}
            acceptedTypes={['.csv', '.txt']}
            maxSize={100 * 1024 * 1024} // 100MB
          />

          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <Button
              variant="outline"
              onClick={() => setShowUploadModal(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleUpload}
              disabled={!uploadingFile}
            >
              Upload Dataset
            </Button>
          </div>
        </div>
      </Modal>

      {/* Preview Modal */}
      <DatasetPreviewModal
        dataset={selectedDataset}
        isOpen={showPreviewModal}
        onClose={() => setShowPreviewModal(false)}
      />
    </div>
  );
};

// Dataset Preview Modal Component
const DatasetPreviewModal: React.FC<{
  dataset: Dataset | null;
  isOpen: boolean;
  onClose: () => void;
}> = ({ dataset, isOpen, onClose }) => {
  // Mock preview data
  const preview = {
    columns: ['timestamp', 'open', 'high', 'low', 'close', 'volume'],
    data: [
      { timestamp: '2024-08-30 09:15:00', open: '24850.50', high: '24865.20', low: '24840.10', close: '24860.75', volume: '12456' },
      { timestamp: '2024-08-30 09:16:00', open: '24860.75', high: '24875.30', low: '24855.60', close: '24870.25', volume: '10234' },
      { timestamp: '2024-08-30 09:17:00', open: '24870.25', high: '24880.40', low: '24865.80', close: '24875.90', volume: '9876' },
    ]
  };

  const quality = {
    missing_data_percentage: 0.02,
    gaps_detected: 3,
    duplicate_timestamps: 0,
    data_consistency_score: 95,
    anomalies: [],
    recommendations: ['Consider filling small data gaps', 'Data quality is excellent overall']
  };

  if (!dataset) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Preview: ${dataset.name}`}
      size="xl"
    >
      <div className="space-y-6">
        {/* Dataset Info */}
        <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Symbol & Timeframe</p>
            <p className="font-medium text-gray-900 dark:text-gray-100">{dataset.symbol} • {dataset.timeframe}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Records</p>
            <p className="font-medium text-gray-900 dark:text-gray-100">{new Intl.NumberFormat().format(dataset.record_count)}</p>
          </div>
        </div>

        {/* Data Quality */}
        <div className="space-y-3">
          <h4 className="font-medium text-gray-900 dark:text-gray-100">Data Quality Analysis</h4>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <p className="text-sm text-gray-600 dark:text-gray-400">Missing Data</p>
              <p className="font-medium text-gray-900 dark:text-gray-100">{quality.missing_data_percentage.toFixed(2)}%</p>
            </div>
            <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <p className="text-sm text-gray-600 dark:text-gray-400">Gaps Detected</p>
              <p className="font-medium text-gray-900 dark:text-gray-100">{quality.gaps_detected}</p>
            </div>
          </div>
          {quality.recommendations.length > 0 && (
            <div className="p-3 bg-warning-50 dark:bg-warning-900/20 border border-warning-200 dark:border-warning-800 rounded-lg">
              <h5 className="text-sm font-medium text-warning-800 dark:text-warning-200 mb-2">Recommendations</h5>
              <ul className="text-sm text-warning-700 dark:text-warning-300 space-y-1">
                {quality.recommendations.map((rec, i) => (
                  <li key={i}>• {rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Data Preview */}
        <div className="space-y-3">
          <h4 className="font-medium text-gray-900 dark:text-gray-100">Data Preview</h4>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  {preview.columns.map((col) => (
                    <th
                      key={col}
                      className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                {preview.data.map((row, i) => (
                  <tr key={i}>
                    {preview.columns.map((col) => (
                      <td
                        key={col}
                        className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100"
                      >
                        {row[col as keyof typeof row]}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </Modal>
  );
};

export default Datasets;
