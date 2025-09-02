import React, { useState, useEffect } from 'react';
import { Settings, Info } from 'lucide-react';

interface ParameterSchema {
  type: string;
  default: any;
  min?: number;
  max?: number;
  step?: number;
  label: string;
  description: string;
}

interface ParametersSchema {
  [key: string]: ParameterSchema;
}

interface StrategyParametersProps {
  strategyId: string;
  initialParameters?: Record<string, any>;
  onParametersChange: (parameters: Record<string, any>) => void;
  disabled?: boolean;
}

const StrategyParameters: React.FC<StrategyParametersProps> = ({
  strategyId,
  initialParameters = {},
  onParametersChange,
  disabled = false
}) => {
  const [schema, setSchema] = useState<ParametersSchema>({});
  const [parameters, setParameters] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadParameterSchema();
  }, [strategyId]);

  useEffect(() => {
    // Initialize parameters when schema loads or initial parameters change
    if (Object.keys(schema).length > 0) {
      const newParameters = { ...parameters };
      let hasChanges = false;

      // Set defaults from schema
      Object.entries(schema).forEach(([key, paramSchema]) => {
        if (key === 'params') return; // Skip the generic params field
        
        if (initialParameters[key] !== undefined) {
          newParameters[key] = initialParameters[key];
        } else if (newParameters[key] === undefined) {
          newParameters[key] = paramSchema.default;
          hasChanges = true;
        }
      });

      if (hasChanges || Object.keys(parameters).length === 0) {
        setParameters(newParameters);
        onParametersChange(newParameters);
      }
    }
  }, [schema, initialParameters]);

  const loadParameterSchema = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`/api/v1/strategies/${strategyId}/schema`);
      if (!response.ok) {
        throw new Error(`Failed to load strategy schema: ${response.statusText}`);
      }
      
      const data = await response.json();
      if (data.success) {
        // Filter out the generic 'params' field and ensure type safety
        const filteredSchema: ParametersSchema = {};
        Object.entries(data.parameters_schema).forEach(([key, value]) => {
          if (key !== 'params' && typeof value === 'object' && value !== null) {
            filteredSchema[key] = value as ParameterSchema;
          }
        });
        setSchema(filteredSchema);
      } else {
        throw new Error('Failed to load strategy schema');
      }
    } catch (err) {
      console.error('Error loading parameter schema:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleParameterChange = (paramKey: string, value: any) => {
    const newParameters = { ...parameters, [paramKey]: value };
    setParameters(newParameters);
    onParametersChange(newParameters);
  };

  const renderParameterInput = (paramKey: string, paramSchema: ParameterSchema) => {
    const value = parameters[paramKey] ?? paramSchema.default;

    if (paramSchema.type === 'number_input') {
      const isFloat = paramSchema.step && paramSchema.step !== Math.floor(paramSchema.step);
      
      return (
        <div key={paramKey} className="space-y-2">
          <div className="flex items-center space-x-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              {paramSchema.label}
            </label>
            <div className="group relative">
              <Info className="w-4 h-4 text-gray-400 cursor-help" />
              <div className="absolute left-0 bottom-full mb-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10">
                {paramSchema.description}
              </div>
            </div>
          </div>
          <input
            type="number"
            min={paramSchema.min}
            max={paramSchema.max}
            step={paramSchema.step || (isFloat ? 0.1 : 1)}
            value={value}
            onChange={(e) => {
              const newValue = isFloat ? parseFloat(e.target.value) : parseInt(e.target.value);
              if (!isNaN(newValue)) {
                handleParameterChange(paramKey, newValue);
              }
            }}
            disabled={disabled}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white disabled:opacity-50"
          />
          <div className="text-xs text-gray-500 dark:text-gray-400">
            Range: {paramSchema.min} - {paramSchema.max} (step: {paramSchema.step || 1})
          </div>
        </div>
      );
    }

    if (paramSchema.type === 'text_input') {
      return (
        <div key={paramKey} className="space-y-2">
          <div className="flex items-center space-x-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              {paramSchema.label}
            </label>
            <div className="group relative">
              <Info className="w-4 h-4 text-gray-400 cursor-help" />
              <div className="absolute left-0 bottom-full mb-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10">
                {paramSchema.description}
              </div>
            </div>
          </div>
          <input
            type="text"
            value={value}
            onChange={(e) => handleParameterChange(paramKey, e.target.value)}
            disabled={disabled}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white disabled:opacity-50"
          />
        </div>
      );
    }

    return null;
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <Settings className="w-5 h-5 text-gray-400" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">Strategy Parameters</h3>
        </div>
        <div className="animate-pulse space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="space-y-2">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
              <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <Settings className="w-5 h-5 text-gray-400" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">Strategy Parameters</h3>
        </div>
        <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
          <p className="text-red-700 dark:text-red-400 text-sm">{error}</p>
        </div>
      </div>
    );
  }

  const parameterEntries = Object.entries(schema);

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-2">
        <Settings className="w-5 h-5 text-gray-600 dark:text-gray-400" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">Strategy Parameters</h3>
        <span className="text-sm text-gray-500 dark:text-gray-400">
          ({parameterEntries.length} parameters)
        </span>
      </div>
      
      {parameterEntries.length === 0 ? (
        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-md">
          <p className="text-gray-600 dark:text-gray-400 text-sm">
            This strategy uses default parameters and doesn't expose configuration options.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {parameterEntries.map(([paramKey, paramSchema]) => 
            renderParameterInput(paramKey, paramSchema)
          )}
        </div>
      )}
    </div>
  );
};

export default StrategyParameters;
