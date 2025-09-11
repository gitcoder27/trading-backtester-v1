import { apiClient } from './api';
import type { 
  Dataset, 
  DatasetPreview, 
  PaginatedResponse, 
  PaginationParams,
  UploadResponse,
  ValidationResult
} from '../types';

export class DatasetService {
  static async uploadDataset(file: File, metadata?: Partial<Dataset>): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (metadata) {
      formData.append('metadata', JSON.stringify(metadata));
    }
    
    return apiClient.upload<UploadResponse>('/datasets/upload', formData);
  }

  static async listDatasets(params?: PaginationParams): Promise<PaginatedResponse<Dataset>> {
    return apiClient.get<PaginatedResponse<Dataset>>('/datasets', params);
  }

  static async getDataset(id: string): Promise<Dataset> {
    return apiClient.get<Dataset>(`/datasets/${id}`);
  }

  static async previewDataset(id: string, rows?: number): Promise<DatasetPreview> {
    return apiClient.get<DatasetPreview>(`/datasets/${id}/preview`, { rows });
  }

  static async getDataQuality(id: string): Promise<ValidationResult> {
    return apiClient.get<ValidationResult>(`/datasets/${id}/quality`);
  }

  static async deleteDataset(id: string): Promise<void> {
    return apiClient.delete<void>(`/datasets/${id}`);
  }

  static async downloadDataset(id: string): Promise<Blob> {
    const response = await fetch(`http://localhost:8000/api/v1/datasets/${id}/download`);
    if (!response.ok) {
      throw new Error(`Failed to download dataset: ${response.statusText}`);
    }
    return response.blob();
  }

  /**
   * Get datasets summary (counts, rows, quality, groupings)
   */
  static async getSummary(): Promise<any> {
    return apiClient.get<any>('/datasets/stats/summary');
  }
}
