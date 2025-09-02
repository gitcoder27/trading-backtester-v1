import React, { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import Button from './Button';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    this.setState({
      error,
      errorInfo
    });

    // Call the onError callback if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  private handleReload = () => {
    window.location.reload();
  };

  private handleGoHome = () => {
    window.location.href = '/';
  };

  public render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex items-center justify-center p-4">
          <div className="max-w-md w-full">
            <div className="card text-center space-y-6">
              <div className="mx-auto w-16 h-16 bg-danger-100 dark:bg-danger-900 rounded-full flex items-center justify-center">
                <AlertTriangle className="w-8 h-8 text-danger-600 dark:text-danger-400" />
              </div>

              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                  Something went wrong
                </h1>
                <p className="text-gray-600 dark:text-gray-400">
                  We're sorry, but something unexpected happened. Please try refreshing the page or contact support if the problem persists.
                </p>
              </div>

              {import.meta.env.DEV && this.state.error && (
                <div className="text-left">
                  <details className="bg-gray-100 dark:bg-gray-800 rounded-lg p-4">
                    <summary className="cursor-pointer text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Error Details (Development)
                    </summary>
                    <div className="text-xs text-gray-600 dark:text-gray-400 font-mono">
                      <div className="mb-2">
                        <strong>Error:</strong> {this.state.error.message}
                      </div>
                      <div className="mb-2">
                        <strong>Stack:</strong>
                        <pre className="whitespace-pre-wrap mt-1 text-xs">
                          {this.state.error.stack}
                        </pre>
                      </div>
                      {this.state.errorInfo && (
                        <div>
                          <strong>Component Stack:</strong>
                          <pre className="whitespace-pre-wrap mt-1 text-xs">
                            {this.state.errorInfo.componentStack}
                          </pre>
                        </div>
                      )}
                    </div>
                  </details>
                </div>
              )}

              <div className="flex flex-col sm:flex-row gap-3">
                <Button
                  variant="primary"
                  onClick={this.handleReset}
                  icon={RefreshCw}
                  fullWidth
                >
                  Try Again
                </Button>
                <Button
                  variant="outline"
                  onClick={this.handleReload}
                  fullWidth
                >
                  Reload Page
                </Button>
                <Button
                  variant="ghost"
                  onClick={this.handleGoHome}
                  icon={Home}
                  fullWidth
                >
                  Go Home
                </Button>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

// Hook-based error boundary for functional components
export const useErrorHandler = () => {
  return (error: Error, errorInfo?: ErrorInfo) => {
    console.error('Error caught by useErrorHandler:', error, errorInfo);
    
    // In a real app, you might want to send this to an error reporting service
    // Example: Sentry.captureException(error, { contexts: { react: errorInfo } });
  };
};

// Simple error fallback component
export const ErrorFallback: React.FC<{ 
  error?: Error; 
  resetError?: () => void;
  message?: string;
}> = ({ 
  error, 
  resetError, 
  message = "Something went wrong" 
}) => {
  return (
    <div className="card text-center space-y-4 max-w-md mx-auto mt-8">
      <div className="w-12 h-12 bg-danger-100 dark:bg-danger-900 rounded-full flex items-center justify-center mx-auto">
        <AlertTriangle className="w-6 h-6 text-danger-600 dark:text-danger-400" />
      </div>
      
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
          {message}
        </h3>
        {error && (
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {error.message}
          </p>
        )}
      </div>

      {resetError && (
        <Button
          variant="primary"
          onClick={resetError}
          icon={RefreshCw}
          size="sm"
        >
          Try Again
        </Button>
      )}
    </div>
  );
};
