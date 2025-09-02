import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { BarChart3, Activity, Table } from 'lucide-react';
import Card from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import {
  EquityChart,
  DrawdownChart,
  ReturnsChart,
  TradeAnalysisChart,
  PerformanceMetrics
} from '../../components/charts';

const Analytics: React.FC = () => {
  const [searchParams] = useSearchParams();
  const backtestId = searchParams.get('backtestId') || '1'; // Default to ID 1 for demo
  const [activeTab, setActiveTab] = useState<'overview' | 'charts' | 'trades'>('overview');

  // Fetch backtest list for selection
  const { data: backtests } = useQuery({
    queryKey: ['backtests'],
    queryFn: async () => {
      // This would normally come from a backtests service
      // For now, return mock data
      return {
        data: [
          { id: '1', strategy_name: 'EMA Crossover', created_at: '2024-01-15', status: 'completed' },
          { id: '2', strategy_name: 'RSI Mean Reversion', created_at: '2024-01-14', status: 'completed' },
          { id: '3', strategy_name: 'Bollinger Bands', created_at: '2024-01-13', status: 'completed' }
        ]
      };
    }
  });

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Activity },
    { id: 'charts', label: 'Charts', icon: BarChart3 },
    { id: 'trades', label: 'Trade Analysis', icon: Table }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Analytics & Reports</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Analyze your strategy performance and generate reports
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <select 
            value={backtestId}
            onChange={(e) => {
              const params = new URLSearchParams(searchParams);
              params.set('backtestId', e.target.value);
              window.history.replaceState({}, '', `${window.location.pathname}?${params}`);
            }}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            {backtests?.data?.map((backtest: any) => (
              <option key={backtest.id} value={backtest.id}>
                {backtest.strategy_name} - {new Date(backtest.created_at).toLocaleDateString()}
              </option>
            ))}
          </select>
          <Badge variant="primary" size="sm">
            <Activity className="h-3 w-3 mr-1" />
            Live Data
          </Badge>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Performance Metrics */}
          <PerformanceMetrics backtestId={backtestId} />

          {/* Quick Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Equity Curve</h3>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setActiveTab('charts')}
                >
                  View Details
                </Button>
              </div>
              <div className="h-64">
                <EquityChart backtestId={backtestId} />
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Drawdown</h3>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setActiveTab('charts')}
                >
                  View Details
                </Button>
              </div>
              <div className="h-64">
                <DrawdownChart backtestId={backtestId} />
              </div>
            </Card>
          </div>
        </div>
      )}

      {activeTab === 'charts' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Portfolio Equity Curve
              </h3>
              <div className="h-80">
                <EquityChart backtestId={backtestId} />
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Drawdown Analysis
              </h3>
              <div className="h-80">
                <DrawdownChart backtestId={backtestId} />
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Returns Distribution
              </h3>
              <div className="h-80">
                <ReturnsChart backtestId={backtestId} />
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Trade Analysis
              </h3>
              <div className="h-80">
                <TradeAnalysisChart backtestId={backtestId} />
              </div>
            </Card>
          </div>
        </div>
      )}

      {activeTab === 'trades' && (
        <div className="space-y-6">
          <Card className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Trade Performance Analysis
              </h3>
              <Badge variant="info" size="sm">
                Interactive Chart
              </Badge>
            </div>
            <div className="h-96">
              <TradeAnalysisChart backtestId={backtestId} />
            </div>
          </Card>

          {/* Trade Log Table */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Detailed Trade Log
              </h3>
              <div className="flex items-center space-x-2">
                <Button variant="outline" size="sm">
                  Export CSV
                </Button>
                <Button variant="outline" size="sm">
                  Filter
                </Button>
              </div>
            </div>
            <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-8 text-center border-2 border-dashed border-gray-200 dark:border-gray-700">
              <Table className="h-12 w-12 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
              <h4 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                Trade Log Table Coming Soon
              </h4>
              <p className="text-gray-600 dark:text-gray-400">
                Detailed trade-by-trade analysis with sorting and filtering will be implemented in the next phase.
              </p>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};

export default Analytics;
