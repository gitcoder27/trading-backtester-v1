const API_BASE_URL = 'http://localhost:8000/api/v1';

export class ApiClient {
  private baseURL: string;
  private fetchImpl: (...args: Parameters<typeof fetch>) => ReturnType<typeof fetch>;

  constructor(baseURL: string = API_BASE_URL, fetchImpl?: typeof fetch) {
    this.baseURL = baseURL;
    // Avoid storing bare window.fetch reference to prevent "Illegal invocation" in some environments
    this.fetchImpl = fetchImpl
      ? ((...args) => fetchImpl(...args))
      : ((...args) => globalThis.fetch(...args));
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await this.fetchImpl(url, config);
      
      if (!response.ok) {
        const contentType = response.headers.get('content-type');
        let errorBody: any;
        try {
          if (contentType && contentType.includes('application/json')) {
            errorBody = await response.json();
          } else {
            errorBody = await response.text();
          }
        } catch {
          errorBody = `(Failed to parse error body): ${response.statusText}`;
        }

        const errorMessage = typeof errorBody === 'string' 
          ? errorBody
          : errorBody.detail || errorBody.message || `HTTP ${response.status}: ${response.statusText}`;

        throw new Error(errorMessage);
      }

      // Handle successful but empty responses
      if (response.status === 204 || response.headers.get('content-length') === '0') {
        return {} as T;
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('An unexpected error occurred');
    }
  }

  async get<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
    const url = new URL(endpoint, this.baseURL);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value === undefined || value === null) return;
        if (Array.isArray(value)) {
          // Append repeated keys for arrays to satisfy FastAPI List[str]
          value.forEach((v) => url.searchParams.append(key, String(v)));
        } else {
          url.searchParams.append(key, String(value));
        }
      });
    }
    return this.request<T>(url.pathname + url.search);
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'DELETE',
    });
  }

  async upload<T>(endpoint: string, formData: FormData): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const response = await this.fetchImpl(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
        const contentType = response.headers.get('content-type');
        let errorBody: any;
        try {
          if (contentType && contentType.includes('application/json')) {
            errorBody = await response.json();
          } else {
            errorBody = await response.text();
          }
        } catch {
          errorBody = `(Failed to parse error body): ${response.statusText}`;
        }

        const errorMessage = typeof errorBody === 'string' 
          ? errorBody
          : errorBody.detail || errorBody.message || `HTTP ${response.status}: ${response.statusText}`;

        throw new Error(errorMessage);
    }

    return await response.json();
  }
}

export const apiClient = new ApiClient();
