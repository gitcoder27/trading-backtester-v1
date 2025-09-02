import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

interface LayoutProps {
  children?: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="h-screen flex overflow-hidden bg-slate-900">
      <Sidebar />
      
      <div className="flex flex-col w-0 flex-1 overflow-hidden">
        <Header />
        
        <main className="flex-1 relative overflow-y-auto focus:outline-none p-6">
          <div className="max-w-7xl mx-auto">
            {children ? children : <Outlet />}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;
