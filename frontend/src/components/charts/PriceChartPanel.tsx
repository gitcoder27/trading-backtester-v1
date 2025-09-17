import React, { useCallback, useEffect, useMemo, useState } from 'react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import { useQuery } from '@tanstack/react-query';
import { BacktestService } from '../../services/backtest';
import PriceChartWithTrades from './PriceChartWithTrades';
import type { ChartQueryParams } from './PriceChartWithTrades';

interface PriceChartPanelProps {
  backtestId: string;
  title?: string;
  height?: number;
  defaultMaxCandles?: number;
  defaultTz?: string;
  singleDayDefault?: boolean;
}

type ChartNavigation = {
  available_dates?: string[];
  resolved_dates?: string[];
  previous_date?: string | null;
  next_date?: string | null;
  requested_start?: string | null;
  requested_end?: string | null;
  resolved_start?: string | null;
  resolved_end?: string | null;
  has_data?: boolean;
  requested_cursor?: string | null;
};

const PriceChartPanel: React.FC<PriceChartPanelProps> = ({
  backtestId,
  title = 'Price + Trades (TradingView Lightweight Chart)',
  height = 560,
  defaultMaxCandles = 5000,
  defaultTz = 'Asia/Kolkata',
  singleDayDefault = true,
}) => {
  const [singleDay, setSingleDay] = useState<boolean>(singleDayDefault);
  const [startDateInput, setStartDateInput] = useState<string | null>(null);
  const [endDateInput, setEndDateInput] = useState<string | null>(null);
  const [currentRange, setCurrentRange] = useState<{ start: string | null; end: string | null }>({
    start: null,
    end: null,
  });
  const [chartParams, setChartParams] = useState<ChartQueryParams | null>(null);
  const [navigation, setNavigation] = useState<ChartNavigation | null>(null);

  const { data: firstCandleData } = useQuery({
    queryKey: ['chart-first-day', backtestId, defaultTz],
    queryFn: async () =>
      BacktestService.getChartData(backtestId, {
        includeTrades: false,
        includeIndicators: false,
        maxCandles: 1,
        tz: defaultTz,
      }),
    enabled: !!backtestId,
    staleTime: 5 * 60 * 1000,
  });

  useEffect(() => {
    if (!firstCandleData) return;

    const nav = (firstCandleData as any)?.navigation;

    let resolvedStart: string | null = nav?.resolved_start ?? nav?.resolved_dates?.[0] ?? null;
    let resolvedEnd: string | null = nav?.resolved_end ?? nav?.resolved_dates?.slice(-1)?.[0] ?? null;

    if (!resolvedStart) {
      const ts = (firstCandleData as any)?.date_range?.start;
      if (typeof ts === 'number') {
        const d = new Date(ts * 1000);
        resolvedStart = d.toISOString().slice(0, 10);
      }
    }

    if (!resolvedEnd) {
      resolvedEnd = resolvedStart;
    }

    if (!resolvedStart) return;

    if (!startDateInput) {
      setStartDateInput(resolvedStart);
    }
    if (!endDateInput) {
      setEndDateInput(singleDay ? resolvedStart : resolvedEnd);
    }
    if (!currentRange.start) {
      setCurrentRange({ start: resolvedStart, end: resolvedEnd });
    }
    if (!chartParams) {
      setChartParams({
        start: resolvedStart,
        end: singleDay ? resolvedStart : resolvedEnd,
        cursor: resolvedStart,
        navigate: singleDay ? 'current' : undefined,
        singleDay,
        tz: defaultTz,
        maxCandles: defaultMaxCandles,
      });
    }
  }, [firstCandleData, singleDay, startDateInput, endDateInput, currentRange.start, currentRange.end, chartParams, defaultTz, defaultMaxCandles]);

  useEffect(() => {
    if (singleDay && startDateInput) setEndDateInput(startDateInput);
  }, [singleDay, startDateInput]);

  const canApply = useMemo(() => Boolean(startDateInput && endDateInput), [startDateInput, endDateInput]);

  const handleApply = () => {
    if (!canApply || !startDateInput) return;
    const startValue = startDateInput;
    const endValue = singleDay ? startValue : endDateInput;

    setChartParams({
      start: startValue,
      end: endValue ?? startValue,
      cursor: startValue,
      navigate: singleDay ? 'current' : undefined,
      singleDay,
      tz: defaultTz,
      maxCandles: defaultMaxCandles,
    });
  };

  const stepDay = (delta: number) => {
    if (!navigation) return;
    const direction = delta > 0 ? 'next' : 'previous';
    const cursorCandidate =
      direction === 'next'
        ? navigation.resolved_end || navigation.resolved_start || currentRange.end || currentRange.start
        : navigation.resolved_start || navigation.resolved_end || currentRange.start || currentRange.end;

    if (!cursorCandidate) return;

    setStartDateInput(cursorCandidate);
    if (singleDay) {
      setEndDateInput(cursorCandidate);
    }

    setChartParams({
      cursor: cursorCandidate,
      navigate: direction,
      singleDay: true,
      tz: defaultTz,
      maxCandles: defaultMaxCandles,
    });
  };

  const handleNavigationChange = useCallback((nav: Record<string, any> | null) => {
    if (!nav) {
      setNavigation(null);
      return;
    }
    setNavigation(nav as ChartNavigation);
  }, []);

  useEffect(() => {
    if (!navigation) return;

    const resolvedStartRaw = navigation.resolved_start ?? navigation.resolved_dates?.[0] ?? currentRange.start;
    const resolvedEndRaw = navigation.resolved_end ?? navigation.resolved_dates?.slice(-1)?.[0] ?? resolvedStartRaw;

    const normalizedStart = resolvedStartRaw ?? null;
    const normalizedEnd = resolvedEndRaw ?? normalizedStart ?? null;

    if (!normalizedStart && !normalizedEnd) {
      return;
    }

    const rangeChanged = Boolean(normalizedStart) && (
      currentRange.start !== normalizedStart || currentRange.end !== normalizedEnd
    );

    if (rangeChanged) {
      setCurrentRange({ start: normalizedStart, end: normalizedEnd });
    }

    const shouldSyncStart = rangeChanged || startDateInput === null;
    if (shouldSyncStart && normalizedStart && startDateInput !== normalizedStart) {
      setStartDateInput(normalizedStart);
    }

    const shouldSyncEnd = rangeChanged || endDateInput === null;
    if (singleDay) {
      if (shouldSyncEnd && normalizedStart && endDateInput !== normalizedStart) {
        setEndDateInput(normalizedStart);
      }
    } else if (normalizedEnd && shouldSyncEnd && endDateInput !== normalizedEnd) {
      setEndDateInput(normalizedEnd);
    }
  }, [navigation, singleDay, currentRange.start, currentRange.end, startDateInput, endDateInput]);

  useEffect(() => {
    if (!chartParams) return;
    if (!startDateInput) return;

    if (singleDay && chartParams.singleDay !== true) {
      setChartParams({
        start: startDateInput,
        end: startDateInput,
        cursor: startDateInput,
        navigate: 'current',
        singleDay: true,
        tz: defaultTz,
        maxCandles: defaultMaxCandles,
      });
      return;
    }

    if (!singleDay && chartParams.singleDay !== false) {
      const targetEnd = endDateInput ?? currentRange.end ?? startDateInput;
      if (!targetEnd) return;
      setChartParams({
        start: startDateInput,
        end: targetEnd,
        cursor: startDateInput,
        navigate: undefined,
        singleDay: false,
        tz: defaultTz,
        maxCandles: defaultMaxCandles,
      });
    }
  }, [singleDay, chartParams, startDateInput, endDateInput, defaultTz, defaultMaxCandles]);

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          {title}
        </h3>
        <div className="flex items-center space-x-2">
          <label className="flex items-center space-x-2 text-sm text-gray-700 dark:text-gray-300">
            <input type="checkbox" checked={singleDay} onChange={(e) => setSingleDay(e.target.checked)} />
            <span>Single day</span>
          </label>
          {singleDay && (
            <>
              <Button
                variant="nav"
                size="sm"
                onClick={() => stepDay(-1)}
                disabled={!navigation?.previous_date}
              >
                Prev Day
              </Button>
              <Button
                variant="nav"
                size="sm"
                onClick={() => stepDay(1)}
                disabled={!navigation?.next_date}
              >
                Next Day
              </Button>
            </>
          )}
        </div>
      </div>
      <div className="flex flex-wrap items-end gap-3 mb-4">
        <div className="flex flex-col">
          <label className="text-xs text-gray-500 dark:text-gray-400 mb-1">Start Date</label>
          <input
            type="date"
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            value={startDateInput || ''}
            onChange={(e) => setStartDateInput(e.target.value)}
          />
        </div>
        <div className="flex flex-col">
          <label className="text-xs text-gray-500 dark:text-gray-400 mb-1">End Date</label>
          <input
            type="date"
            disabled={singleDay}
            className={`px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-transparent ${singleDay ? 'opacity-60 cursor-not-allowed' : ''}`}
            value={endDateInput || ''}
            onChange={(e) => setEndDateInput(e.target.value)}
          />
        </div>
        <div className="flex-1" />
        <Button variant="action" size="sm" onClick={handleApply} disabled={!canApply}>
          Apply
        </Button>
      </div>
      <div className="h-[600px]">
        {chartParams ? (
          <PriceChartWithTrades
            backtestId={backtestId}
            height={height}
            title={title}
            queryParams={chartParams}
            onNavigationChange={handleNavigationChange}
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <p className="text-gray-400">Preparing date range…</p>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

export default PriceChartPanel;
