import type { UTCTimestamp, LineData, SeriesMarker } from 'lightweight-charts';

export interface CandleData {
  time: UTCTimestamp;
  open: number;
  high: number;
  low: number;
  close: number;
}

export type TradeMarker = SeriesMarker<UTCTimestamp> & {
  time: UTCTimestamp;
  position: 'belowBar' | 'aboveBar';
  color: string;
  shape: 'arrowUp' | 'arrowDown' | 'circle' | 'square';
  text: string;
  size?: number;
};

export interface IndicatorLine {
  name: string;
  color: string;
  data: LineData[]; // time/value pairs
  lineWidth?: number;
  visible?: boolean;
  // Optional pane hint: 'separate' will render in a dedicated pane (e.g., RSI/MACD)
  pane?: 'overlay' | 'separate';
}

export interface ChartTrade {
  id?: string | number;
  symbol?: string | null;
  side?: string | null;
  direction?: string | null;
  quantity?: number | null;
  qty?: number | null;
  size?: number | null;
  entry_time?: string | null;
  exit_time?: string | null;
  entry_price?: number | null;
  exit_price?: number | null;
  pnl?: number | null;
  profit_loss?: number | null;
  [key: string]: unknown;
}

export interface TradeListMeta {
  total: number;
  returned: number;
  limit: number;
  has_more: boolean;
  timezone: string;
}
