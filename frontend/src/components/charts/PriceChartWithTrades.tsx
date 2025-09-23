import React, { useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { UTCTimestamp } from 'lightweight-charts';
import TradingViewChart from './TradingViewChart';
import { BacktestService } from '../../services/backtest';
import type { CandleData, TradeMarker } from '../../types/chart';

export type ChartQueryParams = {
  start?: string | null;
  end?: string | null;
  maxCandles?: number | null;
  tz?: string | null;
  singleDay?: boolean | null;
  cursor?: string | null;
  navigate?: 'next' | 'previous' | 'current' | null;
};

interface PriceChartWithTradesProps {
  backtestId: string;
  height?: number;
  title?: string;
  queryParams: ChartQueryParams | null;
  onNavigationChange?: (navigation: Record<string, any> | null) => void;
}

const PriceChartWithTrades: React.FC<PriceChartWithTradesProps> = ({
  backtestId,
  height = 600,
  title = 'Price + Trades',
  queryParams,
  onNavigationChange,
}) => {
  const queryKey = useMemo(() => {
    if (!queryParams) {
      return ['tv-chart', backtestId, 'idle'];
    }

    return [
      'tv-chart',
      backtestId,
      queryParams.start ?? null,
      queryParams.end ?? null,
      queryParams.cursor ?? null,
      queryParams.navigate ?? null,
      queryParams.singleDay ?? null,
      queryParams.maxCandles ?? null,
      queryParams.tz ?? null,
    ];
  }, [backtestId, queryParams]);

  const enabled = Boolean(backtestId && queryParams);

  const { data, isLoading } = useQuery({
    queryKey,
    queryFn: async () => {
      if (!queryParams) return null;
      return BacktestService.getChartData(backtestId, {
        includeTrades: true,
        includeIndicators: true,
        maxCandles: queryParams.maxCandles ?? 3000,
        start: queryParams.start ?? undefined,
        end: queryParams.end ?? undefined,
        tz: queryParams.tz ?? undefined,
        singleDay: queryParams.singleDay ?? undefined,
        cursor: queryParams.cursor ?? undefined,
        navigate: queryParams.navigate ?? undefined,
      });
    },
    enabled,
    staleTime: 5 * 60 * 1000,
  });

  useEffect(() => {
    if (!onNavigationChange) return;
    const nav = (data as any)?.navigation ?? null;
    onNavigationChange(nav);
  }, [data, onNavigationChange]);

  const candleData = useMemo(() => {
    const candles = Array.isArray(data?.candlestick_data) ? (data!.candlestick_data as Array<Record<string, unknown>>) : [];
    const normalized = candles
      .map((candle) => {
        const timeValue = Number(candle.time);
        if (!Number.isFinite(timeValue)) return null;

        const result: CandleData = {
          time: timeValue as UTCTimestamp,
          open: Number(candle.open ?? 0),
          high: Number(candle.high ?? 0),
          low: Number(candle.low ?? 0),
          close: Number(candle.close ?? 0),
        };
        return result;
      })
      .filter((candle): candle is CandleData => candle !== null);
    return normalized;
  }, [data]);

  const tradeMarkers = useMemo(() => {
    if (!Array.isArray(data?.trade_markers)) return [] as TradeMarker[];

    return (data!.trade_markers as Array<Record<string, unknown>>)
      .map((marker) => {
        const timeValue = Number(marker.time);
        if (!Number.isFinite(timeValue)) {
          return null;
        }

        const priceValue = Number(marker.price);
        const allowedShapes: TradeMarker['shape'][] = ['arrowUp', 'arrowDown', 'circle', 'square'];
        const shapeValue = typeof marker.shape === 'string' && allowedShapes.includes(marker.shape as TradeMarker['shape'])
          ? (marker.shape as TradeMarker['shape'])
          : 'circle';

        const normalized: TradeMarker = {
          time: timeValue as UTCTimestamp,
          position: marker.position === 'aboveBar' ? 'aboveBar' : 'belowBar',
          color: typeof marker.color === 'string' ? marker.color : '#ff9800',
          shape: shapeValue,
          text: typeof marker.text === 'string' ? marker.text : '',
          size: Number.isFinite(Number(marker.size)) ? Number(marker.size) : 1,
        };

        if (Number.isFinite(priceValue)) {
          normalized.price = priceValue;
        }

        return normalized;
      })
      .filter((marker): marker is TradeMarker => Boolean(marker));
  }, [data]);

  const indicators = useMemo(() => (data?.indicators ?? []) as any[], [data]);

  const dataBadge = useMemo(() => {
    const name = (data as any)?.dataset_name as string | undefined;
    if (!name) return undefined;
    return name.toLowerCase().includes('simulated') ? 'Sim' : 'Real';
  }, [data]);

  const timeZone = queryParams?.tz ?? undefined;

  return (
    <TradingViewChart
      candleData={candleData}
      tradeMarkers={tradeMarkers}
      indicators={indicators}
      height={height}
      title={title}
      timeZone={timeZone}
      loading={isLoading}
      showControls
      autoFit
      dataBadge={dataBadge}
    />
  );
};

export default PriceChartWithTrades;
