import React from 'react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import { Eye, Download, Trash2 } from 'lucide-react';
import { getStatusIcon, getStatusVariant, getStatusColor } from '../../utils/status';
import { getReturnColor } from '../../utils/formatters';
import type { BacktestDisplay } from '../../types/backtest';

interface Props {
  backtest: BacktestDisplay;
  onView: (id: string) => void;
  onDownload: (id: string) => void;
  onDelete: (id: string) => void;
}

const BacktestCard: React.FC<Props> = ({ backtest, onView, onDownload, onDelete }) => {
  const StatusIcon = getStatusIcon(backtest.status);
  return (
    <Card className="p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <StatusIcon className={`w-6 h-6 ${getStatusColor(backtest.status)}`} />
          <div>
            <div className="flex items-center space-x-3">
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                {backtest.strategy}
              </h3>
              <Badge variant={getStatusVariant(backtest.status)}>{backtest.status}</Badge>
            </div>
            <div className="flex items-center space-x-6 mt-1 text-sm text-gray-500 dark:text-gray-400">
              <span>Backtest: {backtest.id}</span>
              {backtest.jobId && <span>Job: {backtest.jobId}</span>}
              <span>Dataset: {backtest.dataset}</span>
              <span>
                Lots:{' '}
                <span className="font-medium text-gray-700 dark:text-gray-200">
                  {typeof backtest.lots === 'number' && Number.isFinite(backtest.lots) ? backtest.lots : '—'}
                </span>
              </span>
              <span>Created: {backtest.createdAt}</span>
              <span>Duration: {backtest.duration}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-6">
          {/* Performance Metrics */}
          {backtest.status === 'completed' && (
            <div className="flex items-center space-x-6 text-sm">
              <div className="text-center">
                <p className="text-gray-500 dark:text-gray-400">Return</p>
                <p className={`font-semibold ${getReturnColor(backtest.totalReturn)}`}>{backtest.totalReturn}</p>
              </div>
              <div className="text-center">
                <p className="text-gray-500 dark:text-gray-400">Sharpe</p>
                <p className="font-semibold text-gray-900 dark:text-gray-100">{backtest.sharpeRatio.toFixed(2)}</p>
              </div>
              <div className="text-center">
                <p className="text-gray-500 dark:text-gray-400">Drawdown</p>
                <p className="font-semibold text-red-400">{backtest.maxDrawdown}</p>
              </div>
              <div className="text-center">
                <p className="text-gray-500 dark:text-gray-400">Trades</p>
                <p className="font-semibold text-gray-900 dark:text-gray-100">{backtest.totalTrades}</p>
              </div>
              <div className="text-center">
                <p className="text-gray-500 dark:text-gray-400">Win Rate</p>
                <p className="font-semibold text-gray-900 dark:text-gray-100">{backtest.winRate}</p>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center space-x-2">
            <Button variant="ghost" size="sm" icon={Eye} onClick={() => onView(backtest.id)}>
              View
            </Button>
            {backtest.status === 'completed' && (
              <Button variant="ghost" size="sm" icon={Download} onClick={() => onDownload(backtest.id)}>
                Download
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              icon={Trash2}
              onClick={() => onDelete(backtest.id)}
              className="text-red-600 hover:text-red-700"
            >
              Delete
            </Button>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default BacktestCard;
