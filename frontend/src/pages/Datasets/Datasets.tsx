import React, { useMemo, useState } from 'react';
import { Database, Upload, Eye, Download, Trash2, TrendingUp, Calendar, HardDrive } from 'lucide-react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import { showToast } from '../../components/ui/Toast';
import type { Dataset } from '../../types';
import { useDatasets } from '../../hooks/useDatasets';
import { DatasetService } from '../../services/dataset';
import UploadDatasetModal from '../../components/datasets/UploadDatasetModal';
import DatasetPreviewModal from '../../components/datasets/DatasetPreviewModal';

const Datasets: React.FC = () => {
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const { datasets, loading, refetch } = useDatasets();

  const handlePreview = (dataset: Dataset) => {
    setSelectedDataset(dataset);
    setShowPreviewModal(true);
  };

  const handleDelete = async (dataset: Dataset) => {
    if (!confirm(`Delete "${dataset.name}"? This action cannot be undone.`)) return;
    const toastId = showToast.loading('Deleting...');
    try {
      await DatasetService.deleteDataset(String(dataset.id));
      showToast.success('Dataset deleted successfully');
      refetch();
    } catch (e) {
      console.error(e);
      showToast.error('Failed to delete dataset');
    } finally {
      showToast.dismiss(toastId as any);
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

  const totalRecords = useMemo(() => datasets.reduce((sum, d: any) => sum + (d.record_count || d.rows_count || 0), 0), [datasets]);
  const totalSize = useMemo(() => datasets.reduce((sum, d: any) => sum + (d.file_size || 0), 0), [datasets]);

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
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{datasets.length}</p>
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
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{formatNumber(totalRecords)}</p>
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
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{formatFileSize(totalSize)}</p>
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
                {datasets.length ? 'Today' : 'None'}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Datasets Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      ) : datasets.length === 0 ? (
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
          {datasets.map((dataset: any) => (
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
                      {formatNumber(dataset.record_count || dataset.rows_count || 0)}
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
                    onClick={async () => {
                      const toastId = showToast.loading('Preparing download...');
                      try {
                        const blob = await DatasetService.downloadDataset(String(dataset.id));
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `${dataset.name || 'dataset'}.csv`;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        URL.revokeObjectURL(url);
                        showToast.success('Download started');
                      } catch (e) {
                        console.error(e);
                        showToast.error('Failed to download dataset');
                      } finally {
                        showToast.dismiss(toastId as any);
                      }
                    }}
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
      <UploadDatasetModal isOpen={showUploadModal} onClose={() => setShowUploadModal(false)} onUploaded={refetch} />

      {/* Preview Modal */}
      <DatasetPreviewModal dataset={selectedDataset} isOpen={showPreviewModal} onClose={() => setShowPreviewModal(false)} />
    </div>
  );
};

export default Datasets;
