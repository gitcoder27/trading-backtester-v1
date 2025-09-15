import React, { useState } from 'react';
import Modal from '../ui/Modal';
import Button from '../ui/Button';
import FileUpload from '../ui/FileUpload';
import { DatasetService } from '../../services/dataset';
import { showToast } from '../ui/Toast';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onUploaded?: () => void;
}

const UploadDatasetModal: React.FC<Props> = ({ isOpen, onClose, onUploaded }) => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) return;
    const toastId = showToast.loading('Uploading dataset...');
    try {
      setLoading(true);
      await DatasetService.uploadDataset(file);
      showToast.success('Dataset uploaded successfully');
      onClose();
      onUploaded?.();
    } catch (e) {
      console.error(e);
      showToast.error('Failed to upload dataset');
    } finally {
      setLoading(false);
      showToast.dismiss(toastId as any);
      setFile(null);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Upload Market Data" size="lg">
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">Select CSV File</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Upload OHLC market data in CSV format with timestamp, open, high, low, close columns.
          </p>
        </div>

        <FileUpload
          onFileSelect={setFile}
          onFileRemove={() => setFile(null)}
          acceptedTypes={[".csv", ".txt"]}
          maxSize={100 * 1024 * 1024}
        />

        <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-700">
          <Button variant="outline" onClick={onClose} disabled={loading}>Cancel</Button>
          <Button onClick={handleUpload} disabled={!file || loading} loading={loading}>
            Upload Dataset
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default UploadDatasetModal;

