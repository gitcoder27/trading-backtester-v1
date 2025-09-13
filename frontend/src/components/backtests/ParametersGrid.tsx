import React from 'react';
import Input from '../ui/Input';
import type { ParameterSchema } from '../../types';

interface Props {
  schema?: ParameterSchema[];
  parameters: Record<string, any>;
  errors: Record<string, string>;
  onChange: (next: Record<string, any>) => void;
}

const ParametersGrid: React.FC<Props> = ({ schema = [], parameters, errors, onChange }) => {
  const renderParameterField = (param: ParameterSchema) => {
    const value = parameters[param.name];
    const error = errors[`param_${param.name}`];

    switch (param.type) {
      case 'bool':
        return (
          <div key={param.name} className="space-y-2">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={value || false}
                onChange={(e) => onChange({ ...parameters, [param.name]: e.target.checked })}
                className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {param.name}
              </span>
            </label>
            {param.description && (
              <p className="text-xs text-gray-500 dark:text-gray-400">{param.description}</p>
            )}
            {error && <p className="text-xs text-red-500">{error}</p>}
          </div>
        );

      case 'select':
        return (
          <div key={param.name} className="space-y-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              {param.name}
              {param.required && <span className="text-red-500 ml-1">*</span>}
            </label>
            <select
              value={value || ''}
              onChange={(e) => onChange({ ...parameters, [param.name]: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white"
            >
              <option value="">Select {param.name}</option>
              {(param.options || []).map((option: any) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            {param.description && (
              <p className="text-xs text-gray-500 dark:text-gray-400">{param.description}</p>
            )}
            {error && <p className="text-xs text-red-500">{error}</p>}
          </div>
        );

      default:
        return (
          <div key={param.name} className="space-y-2">
            <Input
              label={param.name}
              type={param.type === 'int' || param.type === 'float' ? 'number' : 'text'}
              value={value || ''}
              onChange={(e) => {
                let newValue: any = e.target.value;
                if (param.type === 'int') {
                  newValue = newValue === '' ? '' : parseInt(newValue);
                } else if (param.type === 'float') {
                  newValue = newValue === '' ? '' : parseFloat(newValue);
                }
                onChange({ ...parameters, [param.name]: newValue });
              }}
              placeholder={`Enter ${param.name}`}
              min={param.min}
              max={param.max}
              step={param.type === 'float' ? 'any' : '1'}
              required={param.required}
              error={error}
              helpText={param.description}
            />
          </div>
        );
    }
  };

  if (!schema || schema.length === 0) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {schema.map(renderParameterField)}
    </div>
  );
};

export default ParametersGrid;

