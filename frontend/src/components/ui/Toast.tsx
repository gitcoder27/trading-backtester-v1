import React from 'react';
import { Toaster, toast } from 'react-hot-toast';
import { CheckCircle, XCircle, AlertCircle, Info, X } from 'lucide-react';
import Button from './Button';

// Custom toast component
interface CustomToastProps {
  message: string;
  description?: string;
  type: 'success' | 'error' | 'warning' | 'info';
  onDismiss: () => void;
}

const CustomToast: React.FC<CustomToastProps> = ({
  message,
  description,
  type,
  onDismiss
}) => {
  const icons = {
    success: CheckCircle,
    error: XCircle,
    warning: AlertCircle,
    info: Info
  };

  const colors = {
    success: 'text-success-600',
    error: 'text-danger-600',
    warning: 'text-warning-600',
    info: 'text-info-600'
  };

  const Icon = icons[type];

  return (
    <div className="flex items-start space-x-3 p-4 bg-white dark:bg-gray-800 rounded-lg shadow-soft-lg border border-gray-200 dark:border-gray-700 max-w-md">
      <Icon className={`h-5 w-5 ${colors[type]} flex-shrink-0 mt-0.5`} />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
          {message}
        </p>
        {description && (
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {description}
          </p>
        )}
      </div>
      <Button
        variant="ghost"
        size="xs"
        onClick={onDismiss}
        className="p-1 h-auto text-gray-400 hover:text-gray-600"
      >
        <X className="h-4 w-4" />
      </Button>
    </div>
  );
};

// Toast utility functions
export const showToast = {
  success: (message: string, description?: string) => {
    toast.custom(
      (t) => (
        <CustomToast
          message={message}
          description={description}
          type="success"
          onDismiss={() => toast.dismiss(t.id)}
        />
      ),
      { duration: 4000 }
    );
  },

  error: (message: string, description?: string) => {
    toast.custom(
      (t) => (
        <CustomToast
          message={message}
          description={description}
          type="error"
          onDismiss={() => toast.dismiss(t.id)}
        />
      ),
      { duration: 6000 }
    );
  },

  warning: (message: string, description?: string) => {
    toast.custom(
      (t) => (
        <CustomToast
          message={message}
          description={description}
          type="warning"
          onDismiss={() => toast.dismiss(t.id)}
        />
      ),
      { duration: 5000 }
    );
  },

  info: (message: string, description?: string) => {
    toast.custom(
      (t) => (
        <CustomToast
          message={message}
          description={description}
          type="info"
          onDismiss={() => toast.dismiss(t.id)}
        />
      ),
      { duration: 4000 }
    );
  },

  loading: (message: string) => {
    return toast.loading(message, {
      style: {
        background: 'white',
        color: '#374151',
        border: '1px solid #e5e7eb',
        borderRadius: '0.5rem',
        fontSize: '14px'
      }
    });
  },

  dismiss: (toastId?: string) => {
    toast.dismiss(toastId);
  },

  promise: <T,>(
    promise: Promise<T>,
    {
      loading,
      success,
      error
    }: {
      loading: string;
      success: string | ((data: T) => string);
      error: string | ((error: any) => string);
    }
  ) => {
    return toast.promise(promise, {
      loading,
      success,
      error
    });
  }
};

// Toast provider component
export const ToastProvider: React.FC = () => {
  return (
    <Toaster
      position="top-right"
      toastOptions={{
        duration: 4000,
        style: {
          background: 'transparent',
          boxShadow: 'none',
          padding: 0,
          margin: 0
        }
      }}
      containerStyle={{
        top: 20,
        right: 20
      }}
    />
  );
};

export default ToastProvider;
