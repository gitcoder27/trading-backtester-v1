import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  BarChart3, 
  Database, 
  Target, 
  TrendingUp, 
  Settings,
  X
} from 'lucide-react';
import { useUIStore } from '../../stores/uiStore';

const navigation = [
  { name: 'Dashboard', href: '/', icon: BarChart3 },
  { name: 'Strategies', href: '/strategies', icon: Target },
  { name: 'Datasets', href: '/datasets', icon: Database },
  { name: 'Backtests', href: '/backtests', icon: TrendingUp },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
];

const Sidebar: React.FC = () => {
  const { sidebarOpen, setSidebarOpen } = useUIStore();

  return (
    <>
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm lg:hidden z-40"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-slate-800 shadow-lg border-r border-slate-700 transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex flex-col h-full">
          {/* Logo and close button */}
          <div className="flex items-center justify-between h-16 px-6 border-b border-slate-700">
            <h1 className="text-xl font-bold text-slate-50">Trading Backtester</h1>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden p-2 rounded-md text-slate-400 hover:text-slate-300 hover:bg-slate-700 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 py-6 space-y-1">
            {navigation.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) =>
                  `group flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary-600 text-white shadow-sm'
                      : 'text-slate-300 hover:bg-slate-700 hover:text-slate-100'
                  }`
                }
              >
                <item.icon className="mr-3 h-5 w-5 flex-shrink-0" />
                {item.name}
              </NavLink>
            ))}
          </nav>

          {/* Settings */}
          <div className="px-3 pb-6">
            <NavLink
              to="/settings"
              className={({ isActive }) =>
                `group flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                  isActive
                    ? 'bg-primary-600 text-white shadow-sm'
                    : 'text-slate-300 hover:bg-slate-700 hover:text-slate-100'
                }`
              }
            >
              <Settings className="mr-3 h-5 w-5 flex-shrink-0" />
              Settings
            </NavLink>
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;
