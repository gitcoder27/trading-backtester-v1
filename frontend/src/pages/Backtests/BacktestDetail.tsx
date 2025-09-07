import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Calendar, Clock, TrendingUp, Download, Share2 } from 'lucide-react';
import Card from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import {
  EquityChart,
  DrawdownChart,
  ReturnsChart,
  TradeAnalysisChart,
  TradingViewChart
} from '../../components/charts';
import { BacktestService, JobService } from '../../services/backtest';

const BacktestDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  const { data: backtest, isLoading, error } = useQuery({
    queryKey: ['backtest', id],
    queryFn: () => BacktestService.getBacktest(id!),
    enabled: !!id,
  });

  const { data: chartData, isLoading: chartLoading } = useQuery({
    queryKey: ['chart-data', id],
    queryFn: () => BacktestService.getChartData(id!, {
      includeTrades: true,
      includeIndicators: true,
      maxCandles: 2000 // Limit for performance
    }),
    enabled: !!id && !!backtest,
  });

  // Fallback to job results if no backtest record exists
  const { data: jobResults, isLoading: jobLoading } = useQuery({
    queryKey: ['job-results', id],
    queryFn: () => JobService.getJobResults(id!),
    enabled: !!id && !backtest,
    retry: 1,
  });

  // Always call useMemo hook before any conditional returns
  const cleanStrategyName = React.useMemo(() => {
    if (backtest?.strategy_name) {
      const name = backtest.strategy_name;
      return name.includes('.') ? name.split('.').pop() || name : name;
    }
    return `Backtest Job #${id}`;
  }, [backtest?.strategy_name, id]);

  if (isLoading || (jobLoading && !backtest)) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-4"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-8"></div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-48 bg-gray-200 dark:bg-gray-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error && !backtest && (!jobResults || !jobResults.success)) {
    return (
      <div className="text-center py-12">
        <div className="text-red-500 text-lg font-medium mb-2">
          Failed to load backtest details
        </div>
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          {error?.message || 'Backtest not found'}
        </p>
        <Link to="/backtests">
          <Button variant="outline">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Backtests
          </Button>
        </Link>
      </div>
    );
  }

  const getStatusColor = (status: string | undefined) => {
    if (!status) return 'secondary';
    
    switch (status.toLowerCase()) {
      case 'completed':
        return 'success';
      case 'running':
        return 'info';
      case 'failed':
        return 'danger';
      default:
        return 'secondary';
    }
  };

  // Determine if we are rendering from job results
  const isJobMode = !backtest && jobResults?.success && jobResults?.results;
  const resultsFromJob = (jobResults?.results) || {};
  const metrics: any = backtest?.results?.metrics || (backtest as any)?.metrics || resultsFromJob?.metrics;
  const equityCurve: any[] | undefined = backtest?.results?.equity_curve || resultsFromJob?.equity_curve;
  const trades: any[] | undefined = backtest?.results?.trades || backtest?.results?.trade_log || resultsFromJob?.trades || resultsFromJob?.trade_log;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link to="/backtests">
            <Button variant="outline" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {cleanStrategyName}
            </h1>
            <div className="flex items-center space-x-6 mt-1">
              <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                <Calendar className="h-4 w-4 mr-1" />
                {backtest?.created_at ? new Date(backtest.created_at).toLocaleDateString() : new Date().toLocaleDateString()}
              </div>
              {backtest?.duration && (
                <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                  <Clock className="h-4 w-4 mr-1" />
                  {backtest?.duration}
                </div>
              )}
              <Badge variant={getStatusColor(backtest?.status || jobResults?.status)} size="sm">
                {(backtest?.status || jobResults?.status || 'Unknown')}
              </Badge>
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {!isJobMode && (
            <Link to={`/analytics?backtest_id=${id}`}>
              <Button variant="primary" size="sm">
                <TrendingUp className="h-4 w-4 mr-2" />
                Advanced Analytics
              </Button>
            </Link>
          )}
          <Button variant="outline" size="sm">
            <Share2 className="h-4 w-4 mr-2" />
            Share
          </Button>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          {!isJobMode && (
            <Link to={`/analytics?backtestId=${id}`}>
              <Button variant="primary" size="sm">
                <TrendingUp className="h-4 w-4 mr-2" />
                View Analytics
              </Button>
            </Link>
          )}
        </div>
      </div>

      {/* Backtest Configuration Summary */}
      {backtest && (
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Configuration
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Strategy</p>
            <p className="font-medium text-gray-900 dark:text-gray-100">
              {cleanStrategyName}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Dataset</p>
            <p className="font-medium text-gray-900 dark:text-gray-100">
              {backtest.dataset_name && backtest.dataset_name !== 'Unknown Dataset' 
                ? backtest.dataset_name 
                : 'NIFTY Aug 2025 (1min)'
              }
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Initial Capital</p>
            <p className="font-medium text-gray-900 dark:text-gray-100">
              ${(backtest.initial_capital || 100000).toLocaleString()}
            </p>
          </div>
        </div>
        {backtest.parameters && (
          <div className="mt-6">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Strategy Parameters</p>
            <div className="bg-gray-100 dark:bg-gray-900/80 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
              <pre className="text-sm text-gray-900 dark:text-gray-200 overflow-x-auto">
                {JSON.stringify(backtest.parameters, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </Card>
      )}

      {/* Performance Metrics */}
      {metrics && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Performance Metrics
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
            <div className="text-center p-4 bg-gray-100 dark:bg-gray-900/80 rounded-xl border border-gray-200 dark:border-gray-700">
              <div className={`text-2xl font-bold mb-1 ${
                (metrics.total_return || metrics.total_return_percent || 0) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
              }`}>
                {metrics.total_return_percent 
                  ? `${metrics.total_return_percent.toFixed(2)}%`
                  : `${((metrics.total_return || 0) * 100).toFixed(2)}%`
                }
              </div>
              <div className="text-sm font-medium text-gray-600 dark:text-gray-300">Total Return</div>
            </div>
            
            <div className="text-center p-4 bg-gray-100 dark:bg-gray-900/80 rounded-xl border border-gray-200 dark:border-gray-700">
              <div className="text-2xl font-bold mb-1 text-gray-900 dark:text-gray-100">
                {(metrics.sharpe_ratio || 0).toFixed(3)}
              </div>
              <div className="text-sm font-medium text-gray-600 dark:text-gray-300">Sharpe Ratio</div>
            </div>
            
            <div className="text-center p-4 bg-gray-100 dark:bg-gray-900/80 rounded-xl border border-gray-200 dark:border-gray-700">
              <div className="text-2xl font-bold mb-1 text-red-600 dark:text-red-400">
                {metrics.max_drawdown_percent 
                  ? `${metrics.max_drawdown_percent.toFixed(2)}%`
                  : `${((metrics.max_drawdown || 0) * 100).toFixed(2)}%`
                }
              </div>
              <div className="text-sm font-medium text-gray-600 dark:text-gray-300">Max Drawdown</div>
            </div>
            
            <div className="text-center p-4 bg-gray-100 dark:bg-gray-900/80 rounded-xl border border-gray-200 dark:border-gray-700">
              <div className="text-2xl font-bold mb-1 text-gray-900 dark:text-gray-100">
                {metrics.total_trades || 0}
              </div>
              <div className="text-sm font-medium text-gray-600 dark:text-gray-300">Total Trades</div>
            </div>
            
              <div className="text-center p-4 bg-gray-100 dark:bg-gray-900/80 rounded-xl border border-gray-200 dark:border-gray-700">
              <div className="text-2xl font-bold mb-1 text-blue-600 dark:text-blue-400">
                {(metrics.win_rate || 0).toFixed(1)}%
              </div>
              <div className="text-sm font-medium text-gray-600 dark:text-gray-300">Win Rate</div>
            </div>
            
            <div className="text-center p-4 bg-gray-100 dark:bg-gray-900/80 rounded-xl border border-gray-200 dark:border-gray-700">
              <div className="text-2xl font-bold mb-1 text-gray-900 dark:text-gray-100">
                {metrics.profit_factor?.toFixed(2) || 'N/A'}
              </div>
              <div className="text-sm font-medium text-gray-600 dark:text-gray-300">Profit Factor</div>
            </div>
          </div>
        </Card>
      )}

      {/* TradingView Chart Section (only for persisted backtests) */}
      {backtest && (
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-6">
          Price Chart with Trades
        </h3>
        <div className="h-[600px] w-full">
          {chartLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                <p className="text-gray-400">Loading chart data...</p>
              </div>
            </div>
          ) : chartData?.success && chartData.candlestick_data ? (
            <TradingViewChart
              candleData={chartData.candlestick_data}
              tradeMarkers={chartData.trade_markers || []}
              indicators={chartData.indicators || []}
              title={`${cleanStrategyName} - ${chartData.dataset_name || backtest.dataset_name || 'Unknown Dataset'}`}
              height={600}
              theme="dark"
              showControls={true}
              autoFit={true}
            />
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="text-gray-500 dark:text-gray-400 mb-2">Chart data not available</div>
              <div className="text-sm text-gray-400 dark:text-gray-500">
                {chartData?.error || 'Unable to load price chart data'}
              </div>
            </div>
          )}
        </div>
      </Card>
      )}

      {/* Charts Section */}
      <div className="space-y-10">
        {/* Top Row - Two Charts Side by Side */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
          {/* Equity Chart */}
          <Card className="p-8 overflow-hidden">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-6">
              Portfolio Equity Curve
            </h3>
            <div className="h-80 w-full overflow-hidden rounded-lg">
              {equityCurve ? (
                <EquityChart data={equityCurve} />
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <div className="text-gray-500 dark:text-gray-400 mb-2">No data available</div>
                  <div className="text-sm text-gray-400 dark:text-gray-500">Chart data is empty</div>
                </div>
              )}
            </div>
          </Card>

          {/* Drawdown Chart */}
          <Card className="p-8 overflow-hidden">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-6">
              Drawdown Analysis
            </h3>
            <div className="h-80 w-full overflow-hidden rounded-lg">
              {equityCurve ? (
                <DrawdownChart data={equityCurve} />
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <div className="text-gray-500 dark:text-gray-400 mb-2">No data available</div>
                  <div className="text-sm text-gray-400 dark:text-gray-500">Chart data is empty</div>
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Bottom Row - Two Charts Side by Side */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
          {/* Returns Distribution */}
          <Card className="p-8 overflow-hidden">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-6">
              Returns Distribution
            </h3>
            <div className="h-80 w-full overflow-hidden rounded-lg">
              {equityCurve ? (
                <ReturnsChart data={equityCurve} />
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <div className="text-gray-500 dark:text-gray-400 mb-2">No data available</div>
                  <div className="text-sm text-gray-400 dark:text-gray-500">Chart data is empty</div>
                </div>
              )}
            </div>
          </Card>

          {/* Trade Analysis */}
          <Card className="p-8 overflow-hidden">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-6">
              Trade Analysis
            </h3>
            <div className="h-80 w-full overflow-hidden rounded-lg">
              {trades ? (
                <TradeAnalysisChart data={trades} />
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <div className="text-gray-500 dark:text-gray-400 mb-2">No data available</div>
                  <div className="text-sm text-gray-400 dark:text-gray-500">Chart data is empty</div>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default BacktestDetail;
