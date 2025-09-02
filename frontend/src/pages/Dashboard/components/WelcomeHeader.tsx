import React from 'react';
import { PlayCircle, Upload, Plus } from 'lucide-react';
import { Button } from '../../../components/ui';

interface WelcomeHeaderProps {
  onQuickBacktest: () => void;
  onShowDemo: () => void;
  loading: boolean;
}

const WelcomeHeader: React.FC<WelcomeHeaderProps> = ({
  onQuickBacktest,
  onShowDemo,
  loading
}) => {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Welcome back, Trader
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Here's what's happening with your trading strategies today.
        </p>
      </div>
      
      <div className="flex space-x-3 mt-4 sm:mt-0">
        <Button
          variant="primary"
          icon={PlayCircle}
          onClick={onQuickBacktest}
          loading={loading}
        >
          Quick Backtest
        </Button>
        <Button
          variant="outline"
          icon={Upload}
        >
          Import Data
        </Button>
        <Button
          variant="ghost"
          icon={Plus}
          onClick={onShowDemo}
        >
          Demo Modal
        </Button>
      </div>
    </div>
  );
};

export default WelcomeHeader;
