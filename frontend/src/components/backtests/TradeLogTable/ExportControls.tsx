import type { Trade } from './types';

export const useExportCSV = () => {
  const exportToCSV = (trades: Trade[], backtestId: string) => {
    if (!trades?.length) return;

    const headers = [
      'Entry Time',
      'Exit Time', 
      'Symbol',
      'Side',
      'Entry Price',
      'Exit Price',
      'Quantity',
      'P&L',
      'P&L %',
      'Duration (min)',
      'Fees'
    ];

    const csvContent = [
      headers.join(','),
      ...trades.map(trade => [
        trade.entry_time,
        trade.exit_time,
        trade.symbol,
        trade.side,
        trade.entry_price?.toFixed(2) || '',
        trade.exit_price?.toFixed(2) || '',
        trade.quantity?.toString() || '',
        trade.pnl?.toFixed(2) || '',
        trade.pnl_pct?.toFixed(2) || '',
        trade.duration?.toFixed(0) || '',
        trade.fees?.toFixed(2) || ''
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trades_backtest_${backtestId}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return { exportToCSV };
};
