import { describe, it, expect, beforeEach } from 'vitest';
import { DatasetService } from '../dataset';
import { apiClient } from '../api';
import type { Dataset, DatasetPreview, ValidationResult, UploadResponse } from '../../types';
import { http, HttpResponse } from 'msw';
import { server } from '../../test/mocks/server';

// Mock the API client
vi.mock('../api', () => ({
  apiClient: {
    upload: vi.fn(),
    get: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockApiClient = vi.mocked(apiClient);

describe('DatasetService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('uploadDataset', () => {
    it('should upload dataset file without metadata', async () => {
      const file = new File(['test,data'], 'test.csv', { type: 'text/csv' });
      const mockResponse: UploadResponse = {
        id: 'dataset-123',
        message: 'Dataset uploaded successfully',
        validation_passed: true
      };

      mockApiClient.upload.mockResolvedValue(mockResponse);

      const result = await DatasetService.uploadDataset(file);

      expect(mockApiClient.upload).toHaveBeenCalledWith(
        '/datasets/upload',
        expect.any(FormData)
      );
      
      const formData = mockApiClient.upload.mock.calls[0][1] as FormData;
      expect(formData.get('file')).toBe(file);
      expect(formData.get('metadata')).toBeNull();
      
      expect(result).toEqual(mockResponse);
    });

    it('should upload dataset file with metadata', async () => {
      const file = new File(['test,data'], 'test.csv', { type: 'text/csv' });
      const metadata = {
        name: 'Test Dataset',
        symbol: 'TEST',
        timeframe: '1min'
      };
      const mockResponse: UploadResponse = {
        id: 'dataset-123',
        message: 'Dataset uploaded successfully',
        validation_passed: true
      };

      mockApiClient.upload.mockResolvedValue(mockResponse);

      const result = await DatasetService.uploadDataset(file, metadata);

      const formData = mockApiClient.upload.mock.calls[0][1] as FormData;
      expect(formData.get('file')).toBe(file);
      expect(formData.get('metadata')).toBe(JSON.stringify(metadata));
      
      expect(result).toEqual(mockResponse);
    });

    it('should handle upload errors', async () => {
      const file = new File(['test'], 'test.csv');
      const errorMessage = 'Invalid file format';
      
      mockApiClient.upload.mockRejectedValue(new Error(errorMessage));

      await expect(DatasetService.uploadDataset(file)).rejects.toThrow(errorMessage);
    });
  });

  describe('listDatasets', () => {
    it('should list datasets without parameters', async () => {
      const mockDatasets = {
        items: [
          {
            id: '1',
            name: 'NIFTY 2024',
            symbol: 'NIFTY',
            timeframe: '1min',
            file_path: '/data/nifty.csv',
            file_size: 1024000,
            record_count: 50000,
            start_date: '2024-01-01',
            end_date: '2024-12-31',
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z'
          }
        ],
        total: 1,
        page: 1,
        page_size: 20,
        total_pages: 1
      };

      mockApiClient.get.mockResolvedValue(mockDatasets);

      const result = await DatasetService.listDatasets();

      expect(mockApiClient.get).toHaveBeenCalledWith('/datasets', undefined);
      expect(result).toEqual(mockDatasets);
    });

    it('should list datasets with pagination parameters', async () => {
      const params = { page: 2, page_size: 5 };
      const mockDatasets = {
        items: [],
        total: 10,
        page: 2,
        page_size: 5,
        total_pages: 2
      };

      mockApiClient.get.mockResolvedValue(mockDatasets);

      const result = await DatasetService.listDatasets(params);

      expect(mockApiClient.get).toHaveBeenCalledWith('/datasets', params);
      expect(result).toEqual(mockDatasets);
    });
  });

  describe('getDataset', () => {
    it('should fetch dataset by ID', async () => {
      const mockDataset: Dataset = {
        id: '123',
        name: 'Test Dataset',
        symbol: 'TEST',
        timeframe: '5min',
        file_path: '/data/test.csv',
        file_size: 512000,
        record_count: 25000,
        start_date: '2024-01-01',
        end_date: '2024-06-30',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        quality_score: 95.5,
        metadata: {
          source: 'NSE',
          validated: true
        }
      };

      mockApiClient.get.mockResolvedValue(mockDataset);

      const result = await DatasetService.getDataset('123');

      expect(mockApiClient.get).toHaveBeenCalledWith('/datasets/123');
      expect(result).toEqual(mockDataset);
    });

    it('should handle dataset not found error', async () => {
      mockApiClient.get.mockRejectedValue(new Error('Dataset not found'));

      await expect(DatasetService.getDataset('invalid-id')).rejects.toThrow('Dataset not found');
    });
  });

  describe('previewDataset', () => {
    it('should preview dataset with default rows', async () => {
      const mockPreview: DatasetPreview = {
        columns: ['timestamp', 'open', 'high', 'low', 'close', 'volume'],
        data: [
          {
            timestamp: '2024-01-01 09:15:00',
            open: 18500.0,
            high: 18520.0,
            low: 18490.0,
            close: 18510.0,
            volume: 1000
          }
        ],
        total_rows: 50000,
        preview_rows: 100
      };

      mockApiClient.get.mockResolvedValue(mockPreview);

      const result = await DatasetService.previewDataset('123');

      expect(mockApiClient.get).toHaveBeenCalledWith('/datasets/123/preview', { rows: undefined });
      expect(result).toEqual(mockPreview);
    });

    it('should preview dataset with custom row count', async () => {
      const mockPreview: DatasetPreview = {
        columns: ['timestamp', 'close'],
        data: [],
        total_rows: 1000,
        preview_rows: 50
      };

      mockApiClient.get.mockResolvedValue(mockPreview);

      const result = await DatasetService.previewDataset('123', 50);

      expect(mockApiClient.get).toHaveBeenCalledWith('/datasets/123/preview', { rows: 50 });
      expect(result).toEqual(mockPreview);
    });
  });

  describe('getDataQuality', () => {
    it('should fetch data quality analysis', async () => {
      const mockQuality: ValidationResult = {
        valid: true,
        errors: [],
        warnings: [
          'Minor data gaps detected in 0.1% of records'
        ],
        statistics: {
          total_records: 50000,
          missing_values: 5,
          duplicate_timestamps: 0,
          data_gaps: 2,
          anomalies: 1
        },
        quality_score: 98.5
      };

      mockApiClient.get.mockResolvedValue(mockQuality);

      const result = await DatasetService.getDataQuality('123');

      expect(mockApiClient.get).toHaveBeenCalledWith('/datasets/123/quality');
      expect(result).toEqual(mockQuality);
    });

    it('should handle quality analysis for invalid dataset', async () => {
      const mockQuality: ValidationResult = {
        valid: false,
        errors: [
          'Invalid timestamp format in row 105',
          'Missing close price in row 2340'
        ],
        warnings: [],
        statistics: {
          total_records: 5000,
          missing_values: 245,
          duplicate_timestamps: 12,
          data_gaps: 89,
          anomalies: 15
        },
        quality_score: 45.2
      };

      mockApiClient.get.mockResolvedValue(mockQuality);

      const result = await DatasetService.getDataQuality('invalid-dataset');

      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
      expect(result.quality_score).toBeLessThan(50);
    });
  });

  describe('deleteDataset', () => {
    it('should delete dataset by ID', async () => {
      mockApiClient.delete.mockResolvedValue(undefined);

      await DatasetService.deleteDataset('123');

      expect(mockApiClient.delete).toHaveBeenCalledWith('/datasets/123');
    });

    it('should handle delete errors', async () => {
      mockApiClient.delete.mockRejectedValue(new Error('Dataset is in use'));

      await expect(DatasetService.deleteDataset('123')).rejects.toThrow('Dataset is in use');
    });
  });

  describe('downloadDataset', () => {
    it('should download dataset as blob', async () => {
      const result = await DatasetService.downloadDataset('123');
      expect(typeof (result as any)).toBe('object');
      expect((result as Blob).size).toBeGreaterThan(0);
      expect((result as Blob).type).toBe('text/csv');
    });

    it('should handle download errors', async () => {
      server.use(
        http.get('http://localhost:8000/api/v1/datasets/:id/download', () =>
          HttpResponse.text('Not Found', { status: 404 })
        )
      );
      await expect(DatasetService.downloadDataset('invalid-id')).rejects.toThrow('Failed to download dataset: Not Found');
    });

    it('should handle network errors during download', async () => {
      server.use(
        http.get('http://localhost:8000/api/v1/datasets/:id/download', () => HttpResponse.error())
      );
      await expect(DatasetService.downloadDataset('123')).rejects.toThrow();
    });
  });

  describe('Error handling and edge cases', () => {
    it('should handle empty file upload', async () => {
      const emptyFile = new File([], 'empty.csv', { type: 'text/csv' });
      mockApiClient.upload.mockRejectedValue(new Error('File is empty'));

      await expect(DatasetService.uploadDataset(emptyFile)).rejects.toThrow('File is empty');
    });

    it('should handle large file upload timeout', async () => {
      const largeFile = new File(['x'.repeat(100000)], 'large.csv', { type: 'text/csv' });
      mockApiClient.upload.mockRejectedValue(new Error('Request timeout'));

      await expect(DatasetService.uploadDataset(largeFile)).rejects.toThrow('Request timeout');
    });

    it('should handle malformed API responses', async () => {
      mockApiClient.get.mockResolvedValue(null);

      const result = await DatasetService.getDataset('123');

      expect(result).toBeNull();
    });
  });
});
