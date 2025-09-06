import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ApiClient } from '../api';

// Mock fetch passed into ApiClient (avoid MSW interception and global side effects)
const mockFetch = vi.fn();

describe('ApiClient', () => {
  let apiClient: ApiClient;
  const mockBaseURL = 'http://localhost:8000/api/v1';

  beforeEach(() => {
    apiClient = new ApiClient(mockBaseURL, mockFetch as unknown as typeof fetch);
    mockFetch.mockClear();
  });

  describe('constructor', () => {
    it('should initialize with default base URL', () => {
      const client = new ApiClient();
      expect(client).toBeInstanceOf(ApiClient);
    });

    it('should initialize with custom base URL', () => {
      const customURL = 'http://custom.api.com';
      const client = new ApiClient(customURL);
      expect(client).toBeInstanceOf(ApiClient);
    });
  });

  describe('GET requests', () => {
    it('should make successful GET request', async () => {
      const mockResponse = { data: 'test' };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await apiClient.get('/test');

      expect(mockFetch).toHaveBeenCalledWith(
        `${mockBaseURL}/test`,
        expect.objectContaining({
          headers: {
            'Content-Type': 'application/json',
          },
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should handle GET request with query parameters', async () => {
      const mockResponse = { data: 'test' };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const params = { page: 1, limit: 10, filter: 'active' };
      await apiClient.get('/test', params);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/test?page=1&limit=10&filter=active'),
        expect.any(Object)
      );
    });

    it('should skip undefined and null parameters', async () => {
      const mockResponse = { data: 'test' };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const params = { page: 1, limit: undefined, filter: null, active: 'true' };
      await apiClient.get('/test', params);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/test?page=1&active=true'),
        expect.any(Object)
      );
    });

    it('should throw error for failed GET request', async () => {
      const errorMessage = 'Not Found';
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: () => Promise.resolve({ message: errorMessage }),
      });

      await expect(apiClient.get('/test')).rejects.toThrow(errorMessage);
    });

    it('should handle network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(apiClient.get('/test')).rejects.toThrow('Network error');
    });
  });

  describe('POST requests', () => {
    it('should make successful POST request', async () => {
      const mockResponse = { id: 1, name: 'test' };
      const requestData = { name: 'test' };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await apiClient.post('/test', requestData);

      expect(mockFetch).toHaveBeenCalledWith(
        `${mockBaseURL}/test`,
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestData),
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should make POST request without data', async () => {
      const mockResponse = { success: true };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await apiClient.post('/test');

      expect(mockFetch).toHaveBeenCalledWith(
        `${mockBaseURL}/test`,
        expect.objectContaining({
          method: 'POST',
          body: undefined,
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should throw error for failed POST request', async () => {
      const errorMessage = 'Validation Error';
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        json: () => Promise.resolve({ message: errorMessage }),
      });

      await expect(apiClient.post('/test', {})).rejects.toThrow(errorMessage);
    });
  });

  describe('PUT requests', () => {
    it('should make successful PUT request', async () => {
      const mockResponse = { id: 1, name: 'updated' };
      const requestData = { name: 'updated' };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await apiClient.put('/test/1', requestData);

      expect(mockFetch).toHaveBeenCalledWith(
        `${mockBaseURL}/test/1`,
        expect.objectContaining({
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestData),
        })
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('DELETE requests', () => {
    it('should make successful DELETE request', async () => {
      const mockResponse = { success: true };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await apiClient.delete('/test/1');

      expect(mockFetch).toHaveBeenCalledWith(
        `${mockBaseURL}/test/1`,
        expect.objectContaining({
          method: 'DELETE',
        })
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('File upload', () => {
    it('should make successful file upload', async () => {
      const mockResponse = { id: 1, filename: 'test.csv' };
      const formData = new FormData();
      formData.append('file', new File(['test'], 'test.csv'));
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await apiClient.upload('/upload', formData);

      expect(mockFetch).toHaveBeenCalledWith(
        `${mockBaseURL}/upload`,
        expect.objectContaining({
          method: 'POST',
          body: formData,
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should throw error for failed upload', async () => {
      const errorMessage = 'File too large';
      const formData = new FormData();
      
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 413,
        statusText: 'Payload Too Large',
        json: () => Promise.resolve({ message: errorMessage }),
      });

      await expect(apiClient.upload('/upload', formData)).rejects.toThrow(errorMessage);
    });
  });

  describe('Error handling', () => {
    it('should handle response without error details', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: () => Promise.reject(new Error('Invalid JSON')),
      });

      await expect(apiClient.get('/test')).rejects.toThrow('HTTP 500: Internal Server Error');
    });

    it('should handle non-Error exceptions', async () => {
      mockFetch.mockRejectedValueOnce('String error');

      await expect(apiClient.get('/test')).rejects.toThrow('An unexpected error occurred');
    });
  });
});
