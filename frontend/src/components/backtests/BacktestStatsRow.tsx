import React from 'react';
import Card from '../ui/Card';
import { BarChart3, CheckCircle, Clock, TrendingUp } from 'lucide-react';

interface Props {
  totalBacktests: number;
  completedBacktests: number;
  runningJobs: number;
  avgReturn: number;
}

const BacktestStatsRow: React.FC<Props> = ({ totalBacktests, completedBacktests, runningJobs, avgReturn }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Backtests</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{totalBacktests}</p>
          </div>
          <div className="p-3 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
            <BarChart3 className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Completed</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{completedBacktests}</p>
          </div>
          <div className="p-3 bg-green-100 dark:bg-green-900/20 rounded-lg">
            <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Running Jobs</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{runningJobs}</p>
          </div>
          <div className="p-3 bg-yellow-100 dark:bg-yellow-900/20 rounded-lg">
            <Clock className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Avg Return</p>
            <p className={`text-2xl font-bold ${avgReturn >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {avgReturn >= 0 ? '+' : ''}{avgReturn.toFixed(1)}%
            </p>
          </div>
          <div className="p-3 bg-purple-100 dark:bg-purple-900/20 rounded-lg">
            <TrendingUp className="w-6 h-6 text-purple-600 dark:text-purple-400" />
          </div>
        </div>
      </Card>
    </div>
  );
};

export default BacktestStatsRow;

