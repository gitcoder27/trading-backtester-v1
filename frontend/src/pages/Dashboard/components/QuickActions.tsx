import React from 'react';
import { Plus, Upload, BarChart3 } from 'lucide-react';
import { Card, Button, LoadingSkeleton } from '../../../components/ui';

const QuickActions: React.FC = () => {
  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-6">
        Quick Actions
      </h3>
      
      <div className="space-y-4">
        <Button variant="primary" fullWidth icon={Plus}>
          Create New Strategy
        </Button>
        <Button variant="outline" fullWidth icon={Upload}>
          Upload Market Data
        </Button>
        <Button variant="outline" fullWidth icon={BarChart3}>
          View Performance Report
        </Button>
        <Button variant="ghost" fullWidth>
          System Settings
        </Button>
      </div>

      {/* Loading Skeleton Demo */}
      <div className="mt-8">
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          Loading Demo (Skeleton)
        </h4>
        <div className="space-y-3">
          <LoadingSkeleton className="h-4 w-3/4" />
          <LoadingSkeleton className="h-4 w-1/2" />
          <LoadingSkeleton className="h-8 w-full" />
        </div>
      </div>
    </Card>
  );
};

export default QuickActions;
