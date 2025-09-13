import React from 'react';

type Filter = 'all' | 'completed' | 'running' | 'failed';

interface Props {
  selected: Filter;
  counts: {
    all: number;
    completed: number;
    running: number;
    failed: number;
  };
  onChange: (filter: Filter) => void;
}

const BacktestFilterTabs: React.FC<Props> = ({ selected, counts, onChange }) => {
  const filters: Filter[] = ['all', 'completed', 'running', 'failed'];
  return (
    <div className="flex items-center space-x-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg w-fit">
      {filters.map((filter) => (
        <button
          key={filter}
          onClick={() => onChange(filter)}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            selected === filter
              ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
          }`}
        >
          {filter.charAt(0).toUpperCase() + filter.slice(1)}
          <span className="ml-2 text-xs opacity-75">
            ({counts[filter]})
          </span>
        </button>
      ))}
    </div>
  );
};

export default BacktestFilterTabs;

