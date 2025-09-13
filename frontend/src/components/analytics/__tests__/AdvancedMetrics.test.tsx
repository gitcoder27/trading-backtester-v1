import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import AdvancedMetrics from '../AdvancedMetrics';

vi.mock('../AdvancedMetrics/usePerformanceData', () => ({
  usePerformanceData: vi.fn(),
}));
import { usePerformanceData } from '../AdvancedMetrics/usePerformanceData';
const mockUsePerf = vi.mocked(usePerformanceData as any);

describe('AdvancedMetrics', () => {
  it('shows loading skeletons', () => {
    mockUsePerf.mockReturnValue({ isLoading: true });
    render(<AdvancedMetrics backtestId="1" />);
    // Expect multiple skeleton cards
    expect(document.querySelectorAll('.animate-pulse').length).toBeGreaterThan(0);
  });

  it('shows error state', () => {
    mockUsePerf.mockReturnValue({ isLoading: false, error: new Error('Nope'), data: { success: false } });
    render(<AdvancedMetrics backtestId="1" />);
    expect(screen.getByText(/Failed to load performance data/)).toBeInTheDocument();
  });

  it('renders metric sections when data available', () => {
    mockUsePerf.mockReturnValue({
      isLoading: false,
      error: null,
      data: { success: true },
      performance: {
        basic_metrics: { total_return_pct: 10, sharpe_ratio: 1.2, max_drawdown_pct: -5, win_rate: 60, profit_factor: 1.5, total_trades: 100 },
        advanced_analytics: { volatility_annualized: 12, skewness: 0.1, kurtosis: 3.2, downside_deviation: 5, sortino_ratio: 1.1, calmar_ratio: 0.9 },
        trade_analysis: { avg_win: 100, avg_loss: -50, largest_win: 500, largest_loss: -300, consecutive_wins: 3, consecutive_losses: 2, total_long_trades: 60, total_short_trades: 40, winning_long_trades: 40, winning_short_trades: 20 },
        risk_metrics: { var_95: -2, var_99: -4, cvar_95: -3, cvar_99: -5, max_consecutive_losses: 4 },
        daily_target_stats: { days_traded: 20, days_target_hit: 5, target_hit_rate: 0.25, max_daily_pnl: 800, min_daily_pnl: -400, avg_daily_pnl: 100 },
        drawdown_analysis: { max_drawdown: -5, max_drawdown_duration: 10, avg_drawdown: -2, drawdown_frequency: 0.1 },
        time_analysis: {}
      }
    });
    render(<AdvancedMetrics backtestId="1" />);
    expect(screen.getByText(/Core Performance Metrics/)).toBeInTheDocument();
    expect(screen.getByText(/Advanced Analytics/)).toBeInTheDocument();
    expect(screen.getByText(/Trade Analysis/)).toBeInTheDocument();
    expect(screen.getByText(/Risk Metrics/)).toBeInTheDocument();
  });
});
