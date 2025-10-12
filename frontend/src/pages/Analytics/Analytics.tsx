import React, { Suspense, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { BarChart3, Activity, Table, Calendar, TrendingUp } from 'lucide-react';
import Card from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import AdvancedMetrics from '../../components/analytics/AdvancedMetrics';
import { BacktestService } from '../../services/backtest';
import { EquityChart, DrawdownChart, PriceChartPanel } from '../../components/charts';
import { getStatusVariant } from '../../utils/status';

const Analytics: React.FC = () => {
  const [searchParams] = useSearchParams();
  const backtestId = searchParams.get('backtest_id') || '';
  const [activeTab, setActiveTab] = useState<'overview' | 'price' | 'analytics'>('overview');
  const DEFAULT_TZ = 'Asia/Kolkata';

  // Fetch selected backtest details for identification in header
  const { data: backtest } = useQuery({
    queryKey: ['analytics-backtest', backtestId],
    queryFn: () => BacktestService.getBacktest(backtestId, { minimal: true }),
    enabled: !!backtestId,
    retry: 1,
    staleTime: 10 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const cleanStrategyName = React.useMemo(() => {
    if (backtest?.strategy_name) {
      const name = backtest.strategy_name as string;
      return name.includes('.') ? name.split('.').pop() || name : name;
    }
    return backtestId ? `Backtest #${backtestId}` : 'No Backtest Selected';
  }, [backtest?.strategy_name, backtestId]);

  const lotsUsed = React.useMemo(() => {
    if (!backtest) return null;
    const candidates = [
      (backtest as any)?.engine_config?.lots,
      (backtest as any)?.results?.engine_config?.lots,
      (backtest as any)?.execution_info?.engine_config?.lots,
      (backtest as any)?.engine_options?.lots,
      (backtest as any)?.strategy_params?.position_size,
      (backtest as any)?.strategy_params?.lots,
    ];

    for (const candidate of candidates) {
      if (typeof candidate === 'number' && Number.isFinite(candidate)) {
        return candidate;
      }
      if (typeof candidate === 'string') {
        const parsed = Number(candidate);
        if (Number.isFinite(parsed)) {
          return parsed;
        }
      }
    }

    return null;
  }, [backtest]);

  // status variants centralized in utils/status

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Activity },
    { id: 'price', label: 'Price + Trades', icon: BarChart3 },
    { id: 'analytics', label: 'Analytics', icon: Table }
  ];

  // Lazy-only charts for Analytics tab
  const LazyReturnsChart = React.lazy(() => import('../../components/charts/ReturnsChart'));
  const LazyTradeAnalysisChart = React.lazy(() => import('../../components/charts/TradeAnalysisChart'));

  // Fetch earliest available candle to default the view to first day
  // Common panel now manages date range and chart

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
          {backtestId ? (
            <div className="flex items-center space-x-4 bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2">
              <div className="flex items-center text-sm text-gray-700 dark:text-gray-300">
                <TrendingUp className="h-4 w-4 mr-1" />
                <span className="font-medium">{cleanStrategyName}</span>
                <span className="mx-2 text-gray-400">•</span>
                <span className="text-gray-500 dark:text-gray-400">#{backtestId}</span>
              </div>
              {backtest?.created_at && (
                <div className="hidden md:flex items-center text-sm text-gray-600 dark:text-gray-400">
                  <Calendar className="h-4 w-4 mr-1" />
                  {new Date(backtest.created_at).toLocaleDateString()}
                </div>
              )}
              {backtest?.dataset_name && (
                <div className="hidden lg:flex items-center text-sm text-gray-600 dark:text-gray-400">
                  <span className="mx-2 text-gray-400">•</span>
                  <span className="font-normal">Dataset:</span>
                  <span className="ml-1 text-gray-700 dark:text-gray-300">{backtest.dataset_name}</span>
                </div>
              )}
              {lotsUsed !== null && (
                <div className="hidden lg:flex items-center text-sm text-gray-600 dark:text-gray-400">
                  <span className="mx-2 text-gray-400">•</span>
                  <span className="font-normal">Lots:</span>
                  <span className="ml-1 text-gray-700 dark:text-gray-300">{lotsUsed}</span>
                </div>
              )}
              {backtest?.status && (
                <Badge variant={getStatusVariant(backtest.status)} size="sm">
                  {backtest.status}
                </Badge>
              )}
              <Link to={`/backtests/${backtestId}`}>
                <Button variant="nav" size="sm">
                  View Backtest
                </Button>
              </Link>
            </div>
          ) : (
            <Badge variant="warning" size="sm">No backtest selected</Badge>
          )}
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
          {/* Advanced Performance Metrics */}
          {backtestId ? (
            <AdvancedMetrics backtestId={backtestId} />
          ) : (
            <Card className="p-6">
              <div className="text-gray-600 dark:text-gray-400">
                Select a backtest from the Backtests page to view analytics.
              </div>
            </Card>
          )}

          {/* Quick Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Equity Curve</h3>
                <Button variant="outline" size="sm" onClick={() => setActiveTab('price')}>
                  View Price + Trades
                </Button>
              </div>
              <div className="h-64">
                {backtestId && <EquityChart backtestId={backtestId} maxPoints={600} />}
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Drawdown</h3>
                <Button variant="outline" size="sm" onClick={() => setActiveTab('price')}>
                  View Price + Trades
                </Button>
              </div>
              <div className="h-64">
                {backtestId && <DrawdownChart backtestId={backtestId} maxPoints={600} />}
              </div>
            </Card>
          </div>
        </div>
      )}

      {activeTab === 'price' && (
        <div className="space-y-6">
          {backtestId && (
            <PriceChartPanel
              backtestId={backtestId}
              title={`Price + Trades — ${cleanStrategyName}`}
              height={560}
              defaultMaxCandles={3000}
              defaultTz={DEFAULT_TZ}
            />
          )}
        </div>
      )}

      {activeTab === 'analytics' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 xl-grid-cols-2 xl:grid-cols-2 gap-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Portfolio Equity Curve</h3>
              <div className="h-80">
                {backtestId && (
                  <Suspense fallback={<div className="h-80 flex items-center justify-center text-gray-500">Loading…</div>}>
                    <EquityChart backtestId={backtestId} maxPoints={1500} />
                  </Suspense>
                )}
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Drawdown Analysis</h3>
              <div className="h-80">
                {backtestId && (
                  <Suspense fallback={<div className="h-80 flex items-center justify-center text-gray-500">Loading…</div>}>
                    <DrawdownChart backtestId={backtestId} maxPoints={1500} />
                  </Suspense>
                )}
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Returns Distribution</h3>
              <div className="h-80">
                {backtestId && (
                  <Suspense fallback={<div className="h-80 flex items-center justify-center text-gray-500">Loading…</div>}>
                    <LazyReturnsChart backtestId={backtestId} />
                  </Suspense>
                )}
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Trade Analysis</h3>
                <Badge variant="info" size="sm">Interactive</Badge>
              </div>
              <div className="h-80">
                {backtestId && (
                  <Suspense fallback={<div className="h-80 flex items-center justify-center text-gray-500">Loading…</div>}>
                    <LazyTradeAnalysisChart backtestId={backtestId} />
                  </Suspense>
                )}
              </div>
            </Card>
          </div>

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
