import React, { useCallback, useState } from 'react';
import { Upload, X, AlertCircle, CheckCircle } from 'lucide-react';
import Button from './Button';
import { clsx } from 'clsx';

export interface FileUploadProps {
  onFileSelect: (file: File) => void;
  onFileRemove?: () => void;
  acceptedTypes?: string[];
  maxSize?: number; // in bytes
  multiple?: boolean;
  disabled?: boolean;
  className?: string;
  children?: React.ReactNode;
}

export interface UploadError {
  type: 'size' | 'type' | 'validation';
  message: string;
}

const FileUpload: React.FC<FileUploadProps> = ({
  onFileSelect,
  onFileRemove,
  acceptedTypes = ['.csv', '.txt'],
  maxSize = 100 * 1024 * 1024, // 100MB default
  multiple = false,
  disabled = false,
  className,
  children,
}) => {
  const isDevEnv = typeof import.meta !== 'undefined' && Boolean(import.meta.env?.DEV);
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<UploadError | null>(null);
  const [isValidating, setIsValidating] = useState(false);

  const formatFileSize = useCallback((bytes: number): string => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  }, []);

  const validateFile = useCallback(async (file: File): Promise<UploadError | null> => {
    // Check file size
    if (file.size > maxSize) {
      return {
        type: 'size',
        message: `File size (${formatFileSize(file.size)}) exceeds maximum allowed size (${formatFileSize(maxSize)})`
      };
    }

    // Check file type
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!acceptedTypes.includes(fileExtension)) {
      return {
        type: 'type',
        message: `File type ${fileExtension} is not supported. Accepted types: ${acceptedTypes.join(', ')}`
      };
    }

    // Basic CSV validation for data files
    if (fileExtension === '.csv') {
      return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = (e) => {
          try {
            const text = e.target?.result as string;
            const lines = text.split('\n').slice(0, 5);
            
            if (lines.length < 2) {
              resolve({
                type: 'validation',
                message: 'CSV file must contain at least a header row and one data row'
              });
              return;
            }

            const header = lines[0].toLowerCase();
            const requiredColumns = ['timestamp', 'open', 'high', 'low', 'close'];
            const hasRequiredColumns = requiredColumns.some(col => 
              header.includes(col) || header.includes('date') || header.includes('time')
            );

            if (!hasRequiredColumns) {
              resolve({
                type: 'validation',
                message: 'CSV must contain OHLC data with timestamp/date column'
              });
              return;
            }

            resolve(null);
          } catch (error) {
            if (isDevEnv) {
              console.warn('FileUpload: failed CSV validation', error);
            }
            resolve({
              type: 'validation',
              message: 'Invalid CSV format'
            });
          }
        };
        reader.readAsText(file.slice(0, 10000)); // Read first 10KB for validation
      });
    }

    return null;
  }, [acceptedTypes, formatFileSize, maxSize]);

  const handleFile = useCallback(async (file: File) => {
    setError(null);
    setIsValidating(true);

    try {
      const validationError = await validateFile(file);
      if (validationError) {
        setError(validationError);
        setIsValidating(false);
        return;
      }

      setSelectedFile(file);
      onFileSelect(file);
    } catch (error) {
      if (isDevEnv) {
        console.warn('FileUpload: validation threw unexpectedly', error);
      }
      setError({
        type: 'validation',
        message: 'Failed to validate file'
      });
    } finally {
      setIsValidating(false);
    }
  }, [onFileSelect, validateFile]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) {
      setIsDragOver(true);
    }
  }, [disabled]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    if (disabled) return;

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFile(files[0]);
    }
  }, [disabled, handleFile]);

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setError(null);
    onFileRemove?.();
  };

  const inputId = `file-upload-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className={clsx('space-y-4', className)}>
      {/* Drop Zone */}
      <div
        className={clsx(
          'border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200',
          {
            'border-primary-300 bg-primary-50 dark:border-primary-600 dark:bg-primary-900/20': isDragOver && !disabled,
            'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500': !isDragOver && !disabled && !selectedFile,
            'border-success-300 bg-success-50 dark:border-success-600 dark:bg-success-900/20': selectedFile && !error,
            'border-danger-300 bg-danger-50 dark:border-danger-600 dark:bg-danger-900/20': error,
            'border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800 opacity-50 cursor-not-allowed': disabled,
          }
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {children || (
          <>
            {isValidating ? (
              <div className="flex flex-col items-center space-y-3">
                <div className="w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full animate-spin" />
                <p className="text-sm text-gray-600 dark:text-gray-400">Validating file...</p>
              </div>
            ) : selectedFile ? (
              <div className="flex flex-col items-center space-y-3">
                <div className="flex items-center space-x-3">
                  <CheckCircle className="h-8 w-8 text-success-600" />
                  <div className="text-left">
                    <p className="font-medium text-gray-900 dark:text-gray-100">{selectedFile.name}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{formatFileSize(selectedFile.size)}</p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={X}
                    onClick={handleRemoveFile}
                    className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    aria-label="Remove file"
                  />
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center space-y-3">
                <Upload className={clsx(
                  'h-12 w-12',
                  error ? 'text-danger-400' : 'text-gray-400 dark:text-gray-500'
                )} />
                <div>
                  <p className="text-lg font-medium text-gray-900 dark:text-gray-100">
                    {isDragOver ? 'Drop file here' : 'Upload market data'}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Drag and drop your CSV file here, or{' '}
                    <label htmlFor={inputId} className="text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 cursor-pointer underline">
                      browse
                    </label>
                  </p>
                  <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                    {acceptedTypes.join(', ')} • Max {formatFileSize(maxSize)}
                  </p>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="flex items-start space-x-3 p-4 bg-danger-50 dark:bg-danger-900/20 border border-danger-200 dark:border-danger-800 rounded-lg">
          <AlertCircle className="h-5 w-5 text-danger-600 dark:text-danger-400 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="text-sm font-medium text-danger-800 dark:text-danger-200">Upload Error</h4>
            <p className="text-sm text-danger-700 dark:text-danger-300 mt-1">{error.message}</p>
          </div>
        </div>
      )}

      {/* Hidden File Input */}
      <input
        id={inputId}
        type="file"
        className="hidden"
        accept={acceptedTypes.join(',')}
        multiple={multiple}
        disabled={disabled}
        onChange={handleFileInputChange}
      />
    </div>
  );
};

export default FileUpload;
