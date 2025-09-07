import React from 'react';
import { useQuery } from '@tanstack/react-query';
import TradingViewChart from './TradingViewChart';
import { BacktestService } from '../../services/backtest';

interface PriceChartWithTradesProps {
  backtestId: string;
  height?: number;
  title?: string;
  start?: string; // ISO datetime or YYYY-MM-DD
  end?: string;   // ISO datetime or YYYY-MM-DD
  maxCandles?: number;
  tz?: string;
}

const PriceChartWithTrades: React.FC<PriceChartWithTradesProps> = ({ backtestId, height = 600, title = 'Price + Trades', start, end, maxCandles, tz }) => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['tv-chart', backtestId, start || null, end || null, maxCandles || null, tz || null],
    queryFn: async () => BacktestService.getChartData(backtestId, { 
      includeTrades: true, 
      includeIndicators: true, 
      maxCandles: maxCandles ?? 3000,
      start,
      end,
      tz,
    }),
    enabled: !!backtestId,
    staleTime: 5 * 60 * 1000,
  });

  const candleData = React.useMemo(() => (data?.candlestick_data ?? []) as any[], [data]);
  const tradeMarkers = React.useMemo(() => (data?.trade_markers ?? []) as any[], [data]);
  const indicators = React.useMemo(() => (data?.indicators ?? []) as any[], [data]);

  const dataBadge = React.useMemo(() => {
    const name = (data as any)?.dataset_name as string | undefined;
    if (!name) return undefined;
    return name.toLowerCase().includes('simulated') ? 'Sim' : 'Real';
  }, [data]);

  return (
    <TradingViewChart
      candleData={candleData}
      tradeMarkers={tradeMarkers}
      indicators={indicators}
      height={height}
      title={title}
      timeZone={tz}
      loading={isLoading}
      showControls
      autoFit
      dataBadge={dataBadge}
    />
  );
};

export default PriceChartWithTrades;
