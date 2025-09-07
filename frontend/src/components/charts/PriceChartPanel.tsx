import React, { useEffect, useMemo, useState } from 'react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import { useQuery } from '@tanstack/react-query';
import { BacktestService } from '../../services/backtest';
import PriceChartWithTrades from './PriceChartWithTrades';

interface PriceChartPanelProps {
  backtestId: string;
  title?: string;
  height?: number;
  defaultMaxCandles?: number;
  defaultTz?: string;
  singleDayDefault?: boolean;
}

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
  const [appliedStart, setAppliedStart] = useState<string | null>(null);
  const [appliedEnd, setAppliedEnd] = useState<string | null>(null);

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
    const ts = (firstCandleData as any)?.date_range?.start;
    if (!ts) return;
    const d = new Date((ts as number) * 1000);
    const yyyyMmDd = d.toISOString().slice(0, 10);
    if (!startDateInput) setStartDateInput(yyyyMmDd);
    if (!endDateInput) setEndDateInput(yyyyMmDd);
    if (!appliedStart || !appliedEnd) {
      setAppliedStart(yyyyMmDd);
      setAppliedEnd(yyyyMmDd);
    }
  }, [firstCandleData]);

  useEffect(() => {
    if (singleDay && startDateInput) setEndDateInput(startDateInput);
  }, [singleDay, startDateInput]);

  const canApply = useMemo(() => Boolean(startDateInput && endDateInput), [startDateInput, endDateInput]);

  const handleApply = () => {
    if (!canApply) return;
    setAppliedStart(startDateInput);
    setAppliedEnd(endDateInput);
  };

  const stepDay = (delta: number) => {
    if (!appliedStart) return;
    const base = new Date(appliedStart);
    base.setDate(base.getDate() + delta);
    const yyyyMmDd = base.toISOString().slice(0, 10);
    setStartDateInput(yyyyMmDd);
    setEndDateInput(yyyyMmDd);
    setAppliedStart(yyyyMmDd);
    setAppliedEnd(yyyyMmDd);
  };

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
              <Button variant="outline" size="sm" onClick={() => stepDay(-1)}>
                Prev Day
              </Button>
              <Button variant="outline" size="sm" onClick={() => stepDay(1)}>
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
        <Button variant="primary" size="sm" onClick={handleApply} disabled={!canApply}>
          Apply
        </Button>
      </div>
      <div className="h-[600px]">
        {appliedStart && appliedEnd ? (
          <PriceChartWithTrades
            backtestId={backtestId}
            height={height}
            start={appliedStart}
            end={appliedEnd}
            maxCandles={defaultMaxCandles}
            tz={defaultTz}
            title={title}
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

