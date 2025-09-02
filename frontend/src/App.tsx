import { Routes, Route } from 'react-router-dom';
import { useEffect } from 'react';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard/Dashboard';
import Strategies from './pages/Strategies/Strategies';
import Datasets from './pages/Datasets/Datasets';
import Backtests from './pages/Backtests/Backtests';
import BacktestDetail from './pages/Backtests/BacktestDetail';
import Analytics from './pages/Analytics/Analytics';
import ErrorBoundary from './components/ui/ErrorBoundary';
import ToastProvider from './components/ui/Toast';
import { useThemeStore } from './stores/themeStore';

function App() {
  const { setTheme } = useThemeStore();

  // Force dark mode on every app load
  useEffect(() => {
    setTheme('dark');
    // Also ensure the document element has the dark class
    document.documentElement.classList.add('dark');
  }, [setTheme]);

  return (
    <ErrorBoundary>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/strategies" element={<Strategies />} />
          <Route path="/datasets" element={<Datasets />} />
          <Route path="/backtests" element={<Backtests />} />
          <Route path="/backtests/:id" element={<BacktestDetail />} />
          <Route path="/analytics" element={<Analytics />} />
        </Routes>
      </Layout>
      <ToastProvider />
    </ErrorBoundary>
  );
}

export default App;