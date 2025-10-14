import React from 'react';
import { Menu, User } from 'lucide-react';
import { useUIStore } from '../../stores/uiStore';
import Button from '../ui/Button';
import { ThemeToggle } from '../ui/ThemeToggle';

const Header: React.FC = () => {
  const { toggleSidebar } = useUIStore();

  return (
    <header className="bg-slate-900 shadow-lg border-b border-slate-700">
      <div className="flex items-center justify-between h-16 px-4 lg:px-6">
        {/* Left side */}
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleSidebar}
            icon={Menu}
            className="lg:hidden text-slate-300 hover:text-slate-100 hover:bg-slate-800"
            aria-label="Toggle sidebar"
          />
          
          <div className="hidden lg:block">
            <h1 className="text-xl font-bold text-slate-50">
              Trading Backtester
            </h1>
          </div>
        </div>

        {/* Right side */}
        <div className="flex items-center space-x-3">
          {/* Theme toggle */}
          <ThemeToggle size="sm" />

          {/* User menu */}
          <div className="flex items-center space-x-2">
            <div className="h-8 w-8 bg-primary-600 rounded-full flex items-center justify-center">
              <User className="h-4 w-4 text-white" />
            </div>
            <span className="text-sm font-medium text-slate-300 hidden sm:block">
              Trading User
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
