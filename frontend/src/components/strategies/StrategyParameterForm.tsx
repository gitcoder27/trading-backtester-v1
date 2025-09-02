import React, { useState, useEffect } from 'react';
import { AlertCircle, Check, X } from 'lucide-react';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import type { ParameterSchema } from '../../types';

interface StrategyParameterFormProps {
  schema: ParameterSchema[];
  initialValues?: Record<string, any>;
  onParametersChange: (parameters: Record<string, any>) => void;
  onValidate?: (parameters: Record<string, any>) => void;
  isValidating?: boolean;
  validationErrors?: string[];
  className?: string;
}

const StrategyParameterForm: React.FC<StrategyParameterFormProps> = ({
  schema,
  initialValues = {},
  onParametersChange,
  onValidate,
  isValidating = false,
  validationErrors = [],
  className = ''
}) => {
  const [parameters, setParameters] = useState<Record<string, any>>(initialValues);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    // Initialize with default values
    const defaultParams: Record<string, any> = {};
    schema.forEach(param => {
      if (param.default !== undefined) {
        defaultParams[param.name] = param.default;
      }
    });
    
    const merged = { ...defaultParams, ...initialValues };
    setParameters(merged);
    onParametersChange(merged);
  }, [schema, initialValues]);

  const validateField = (param: ParameterSchema, value: any): string | null => {
    if (param.required && (value === undefined || value === null || value === '')) {
      return `${param.name} is required`;
    }

    if (value !== undefined && value !== null && value !== '') {
      if (param.type === 'int' || param.type === 'float') {
        const numValue = parseFloat(value);
        if (isNaN(numValue)) {
          return `${param.name} must be a valid number`;
        }
        if (param.min !== undefined && numValue < param.min) {
          return `${param.name} must be at least ${param.min}`;
        }
        if (param.max !== undefined && numValue > param.max) {
          return `${param.name} must be at most ${param.max}`;
        }
      }
    }

    return null;
  };

  const handleParameterChange = (paramName: string, value: any) => {
    const param = schema.find(p => p.name === paramName);
    if (!param) return;

    // Type conversion
    let convertedValue = value;
    if (param.type === 'int') {
      convertedValue = value === '' ? undefined : parseInt(value, 10);
    } else if (param.type === 'float') {
      convertedValue = value === '' ? undefined : parseFloat(value);
    } else if (param.type === 'bool') {
      convertedValue = Boolean(value);
    }

    const newParameters = { ...parameters, [paramName]: convertedValue };
    setParameters(newParameters);
    onParametersChange(newParameters);

    // Validate field
    const error = validateField(param, convertedValue);
    setFieldErrors(prev => ({
      ...prev,
      [paramName]: error || ''
    }));
  };

  const renderParameterInput = (param: ParameterSchema) => {
    const value = parameters[param.name] ?? '';
    const error = fieldErrors[param.name];

    const baseInputClasses = `w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors ${
      error 
        ? 'border-red-300 bg-red-50 dark:bg-red-900/20 dark:border-red-600' 
        : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800'
    } text-gray-900 dark:text-gray-100`;

    switch (param.type) {
      case 'bool':
        return (
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id={param.name}
              checked={Boolean(value)}
              onChange={(e) => handleParameterChange(param.name, e.target.checked)}
              className="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500 dark:focus:ring-primary-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
            />
            <label htmlFor={param.name} className="text-sm text-gray-700 dark:text-gray-300">
              {param.description || param.name}
            </label>
          </div>
        );

      case 'select':
        return (
          <select
            value={value}
            onChange={(e) => handleParameterChange(param.name, e.target.value)}
            className={baseInputClasses}
          >
            <option value="">Select {param.name}</option>
            {param.options?.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        );

      case 'int':
      case 'float':
        return (
          <input
            type="number"
            value={value}
            onChange={(e) => handleParameterChange(param.name, e.target.value)}
            className={baseInputClasses}
            placeholder={param.default?.toString() || ''}
            min={param.min}
            max={param.max}
            step={param.type === 'float' ? 'any' : '1'}
          />
        );

      default:
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => handleParameterChange(param.name, e.target.value)}
            className={baseInputClasses}
            placeholder={param.default?.toString() || ''}
          />
        );
    }
  };

  const isFormValid = () => {
    return schema.every(param => {
      const value = parameters[param.name];
      return validateField(param, value) === null;
    });
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Strategy Parameters
        </h3>
        {onValidate && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => onValidate(parameters)}
            disabled={!isFormValid() || isValidating}
            icon={isValidating ? undefined : Check}
          >
            {isValidating ? 'Validating...' : 'Validate Parameters'}
          </Button>
        )}
      </div>

      {/* Validation Errors */}
      {validationErrors.length > 0 && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
            <h4 className="font-medium text-red-800 dark:text-red-200">Validation Errors</h4>
          </div>
          <ul className="list-disc list-inside space-y-1 text-sm text-red-700 dark:text-red-300">
            {validationErrors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Parameters Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {schema.map((param) => (
          <div key={param.name} className="space-y-2">
            <div className="flex items-center space-x-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                {param.name}
              </label>
              {param.required && (
                <Badge variant="danger" size="sm">Required</Badge>
              )}
            </div>
            
            {param.description && (
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {param.description}
              </p>
            )}
            
            {renderParameterInput(param)}
            
            {fieldErrors[param.name] && (
              <div className="flex items-center space-x-1 text-sm text-red-600 dark:text-red-400">
                <X className="h-3 w-3" />
                <span>{fieldErrors[param.name]}</span>
              </div>
            )}
            
            {/* Parameter metadata */}
            <div className="flex flex-wrap gap-2 text-xs text-gray-500 dark:text-gray-400">
              <span>Type: {param.type}</span>
              {param.default !== undefined && (
                <span>Default: {param.default.toString()}</span>
              )}
              {param.min !== undefined && (
                <span>Min: {param.min}</span>
              )}
              {param.max !== undefined && (
                <span>Max: {param.max}</span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Parameters configured: {Object.keys(parameters).length} of {schema.length}
          </span>
          <div className="flex items-center space-x-2">
            {isFormValid() ? (
              <Badge variant="success" size="sm">
                <Check className="h-3 w-3 mr-1" />
                Valid
              </Badge>
            ) : (
              <Badge variant="danger" size="sm">
                <X className="h-3 w-3 mr-1" />
                Invalid
              </Badge>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default StrategyParameterForm;
