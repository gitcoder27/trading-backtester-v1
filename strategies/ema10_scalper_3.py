"""
This script implements the EMA10ScalperStrategy, a scalping strategy based on the 10-period Exponential Moving Average (EMA).

Strategy Logic:
- The core idea is to trade based on price crossovers of the 10 EMA, which acts as a dynamic support and resistance level.
- Long Entry: A long position is initiated when the price crosses above the 10 EMA, suggesting a potential uptrend.
- Short Entry: A short position is taken when the price crosses below the 10 EMA, indicating a potential downtrend.
- Exits:
  - A long position is exited if the price closes below the 10 EMA.
  - A short position is exited if the price closes above the 10 EMA.
  - A fixed profit target of 20 points from the entry price.
  - A fixed stop loss of 15 points from the entry price.
"""

import pandas as pd
from backtester.strategy_base import StrategyBase

class EMA10ScalperStrategyV3(StrategyBase):
    def __init__(self, params=None):
        super().__init__(params)
        self.ema_period = params.get('ema_period', 10) if params else 10
        self.profit_target = params.get('profit_target', 20) if params else 20
        self.stop_loss = params.get('stop_loss', 15) if params else 15
        self.atr_period = params.get('atr_period', 14) if params else 14
        self.atr_mult_target = params.get('atr_mult_target', 1.5) if params else 1.5
        self.atr_mult_stop = params.get('atr_mult_stop', 1.0) if params else 1.0
        self.min_atr = params.get('min_atr', 5) if params else 5
        self.daily_max_loss = params.get('daily_max_loss', 2000) if params else 2000
        self.trade_start_time = params.get('trade_start_time', '09:30') if params else '09:30'
        self.trade_end_time = params.get('trade_end_time', '15:00') if params else '15:00'
        self.trailing_stop_mult = params.get('trailing_stop_mult', 0.7) if params else 0.7
        self.cooldown_losses = params.get('cooldown_losses', 3) if params else 3
        self.max_daily_range = params.get('max_daily_range', 600) if params else 600
        self.max_trades_per_day = params.get('max_trades_per_day', 15) if params else 15

    @staticmethod
    def get_params_config():
        return [
            {
                "name": "ema10_ema_period", "param_key": "ema_period", "type": "number_input",
                "label": "EMA Period", "default": 10, "min": 5, "max": 200, "step": 1
            },
            {
                "name": "ema10_pt", "param_key": "profit_target", "type": "number_input",
                "label": "Profit Target (pts)", "default": 20, "min": 1, "max": 400, "step": 1
            },
            {
                "name": "ema10_sl", "param_key": "stop_loss", "type": "number_input",
                "label": "Stop Loss (pts)", "default": 15, "min": 1, "max": 400, "step": 1
            },
            {
                "name": "ema10_atr_period", "param_key": "atr_period", "type": "number_input",
                "label": "ATR Period", "default": 14, "min": 5, "max": 100, "step": 1
            },
            {
                "name": "ema10_atr_mult_target", "param_key": "atr_mult_target", "type": "number_input",
                "label": "ATR Multiplier for Target", "default": 1.5, "min": 0.5, "max": 5.0, "step": 0.1
            },
            {
                "name": "ema10_atr_mult_stop", "param_key": "atr_mult_stop", "type": "number_input",
                "label": "ATR Multiplier for Stop Loss", "default": 1.0, "min": 0.5, "max": 5.0, "step": 0.1
            },
            {
                "name": "ema10_min_atr", "param_key": "min_atr", "type": "number_input",
                "label": "Minimum ATR to Trade", "default": 5.0, "min": 0.0, "max": 50.0, "step": 0.5
            },
            {
                "name": "ema10_daily_max_loss", "param_key": "daily_max_loss", "type": "number_input",
                "label": "Daily Max Loss Limit", "default": 3000, "min": 500, "max": 20000, "step": 100
            },
            {
                "name": "ema10_trade_start_time", "param_key": "trade_start_time", "type": "text_input",
                "label": "Trade Start Time (HH:MM)", "default": "09:30"
            },
            {
                "name": "ema10_trade_end_time", "param_key": "trade_end_time", "type": "text_input",
                "label": "Trade End Time (HH:MM)", "default": "15:00"
            },
            {
                "name": "ema10_trailing_stop_mult", "param_key": "trailing_stop_mult", "type": "number_input",
                "label": "Trailing Stop Multiplier (ATR)", "default": 0.7, "min": 0.2, "max": 2.0, "step": 0.1
            },
            {
                "name": "ema10_cooldown_losses", "param_key": "cooldown_losses", "type": "number_input",
                "label": "Consecutive Losses for Cooldown", "default": 3, "min": 1, "max": 10, "step": 1
            },
        ]

    def indicator_config(self):
        """
        Configuration describing which indicators to plot and how.
        Used by the engine to expose indicator columns and by plotting to render overlays.
        """
        return [
            {
                "column": "ema",
                "label": f"EMA({self.ema_period})",
                "plot": True,
                "color": "orange",
                "type": "solid",
                "panel": 1,
            }
        ]

    def generate_signals(self, data):
        """
        Optimized signal generation using vectorized operations.
        Adds 'signal' column to data:
        1 = Long Entry, -1 = Short Entry, 0 = No Entry/Flat
        Also adds ATR column and uses minimum ATR filter for signals.
        Filters signals by time window, daily max loss, volatility, and max trades per day.
        ATR-based intraday volatility filter: skip trades when ATR > 1.5x rolling median ATR.
        """
        df = data.copy()
        # Vectorized EMA calculation
        df['ema'] = df['close'].ewm(span=self.ema_period, adjust=False).mean()
        # ATR calculation
        high = df['high']
        low = df['low']
        close = df['close']
        prev_close = close.shift(1)
        tr1 = (high - low).abs()
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['atr'] = tr.rolling(self.atr_period).mean()
        # ATR-based volatility filter
        median_atr = df['atr'].rolling(50, min_periods=1).median()
        valid_atr = df['atr'] <= 1.5 * median_atr
        # Time filter
        df['trade_time'] = df['timestamp'].dt.strftime('%H:%M') if 'timestamp' in df.columns else None
        valid_time = (df['trade_time'] >= self.trade_start_time) & (df['trade_time'] <= self.trade_end_time) if df['trade_time'] is not None else True
        # Volatility filter: skip days with range > max_daily_range
        df['date'] = df['timestamp'].dt.date if 'timestamp' in df.columns else None
        daily_range = df.groupby('date').apply(lambda x: x['high'].max() - x['low'].min()) if df['date'] is not None else None
        valid_vol = df['date'].map(lambda d: daily_range[d] <= self.max_daily_range if daily_range is not None and d in daily_range else True) if df['date'] is not None else True
        # Signal conditions
        prev_ema = df['ema'].shift(1)
        prev_close = df['close'].shift(1)
        long_condition = (prev_close < prev_ema) & (df['close'] > df['ema']) & (df['atr'] >= self.min_atr) & valid_time & valid_vol & valid_atr
        short_condition = (prev_close > prev_ema) & (df['close'] < df['ema']) & (df['atr'] >= self.min_atr) & valid_time & valid_vol & valid_atr
        df['signal'] = 0
        df.loc[long_condition, 'signal'] = 1
        df.loc[short_condition, 'signal'] = -1
        # Limit trades per day
        if df['date'] is not None:
            for d in df['date'].unique():
                idx = df[df['date'] == d].index
                signals = df.loc[idx, 'signal']
                trade_idx = signals[signals != 0].index
                if len(trade_idx) > self.max_trades_per_day:
                    # Zero out excess signals
                    df.loc[trade_idx[self.max_trades_per_day:], 'signal'] = 0
        # Daily max loss filter (handled in engine, but add info column for engine)
        df['daily_max_loss'] = self.daily_max_loss
        return df

    def should_exit(self, position, row, entry_price, highest_price=None, lowest_price=None):
        price = row.close if hasattr(row, 'close') else row['close']
        ema = row.ema if hasattr(row, 'ema') else row['ema']
        atr = row.atr if hasattr(row, 'atr') else row.get('atr', self.stop_loss)
        # Use ATR-based dynamic targets
        dynamic_target = self.atr_mult_target * atr if atr and not pd.isna(atr) else self.profit_target
        dynamic_stop = self.atr_mult_stop * atr if atr and not pd.isna(atr) else self.stop_loss
        trailing_stop = self.trailing_stop_mult * atr if atr and not pd.isna(atr) else self.stop_loss
        exit_reason = ''
        if position == 'long':
            if price < ema:
                exit_reason = 'EMA exit'
            elif price >= entry_price + dynamic_target:
                exit_reason = 'Target'
            elif price <= entry_price - dynamic_stop:
                exit_reason = 'Stop Loss'
            elif highest_price is not None and price <= highest_price - trailing_stop:
                exit_reason = 'Trailing Stop'
        elif position == 'short':
            if price > ema:
                exit_reason = 'EMA exit'
            elif price <= entry_price - dynamic_target:
                exit_reason = 'Target'
            elif price >= entry_price + dynamic_stop:
                exit_reason = 'Stop Loss'
            elif lowest_price is not None and price >= lowest_price + trailing_stop:
                exit_reason = 'Trailing Stop'
        return (exit_reason != ''), exit_reason

# max-profit target as 50