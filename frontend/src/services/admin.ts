import { apiClient } from './api';

export interface MaintenanceResponse {
  success: boolean;
  message?: string;
  [key: string]: unknown;
}

export class AdminService {
  static async clearDatasets(): Promise<MaintenanceResponse> {
    return apiClient.delete<MaintenanceResponse>('/admin/datasets');
  }

  static async clearBacktests(): Promise<MaintenanceResponse> {
    return apiClient.delete<MaintenanceResponse>('/admin/backtests');
  }

  static async clearJobs(): Promise<MaintenanceResponse> {
    return apiClient.delete<MaintenanceResponse>('/admin/jobs');
  }
}
