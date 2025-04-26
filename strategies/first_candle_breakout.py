from backtester.strategy_base import StrategyBase
import pandas as pd

class FirstCandleBreakoutStrategy(StrategyBase):
    def __init__(self, params=None):
        super().__init__(params)
        self.target_points = params.get('target_points', 20) if params else 20
        self.session_start = params.get('session_start', '09:15') if params else '09:15'
        self.signal_candle_idx = params.get('signal_candle_idx', 0) if params else 0
        # Persistent state for SL and direction
        self.active_stop_loss = None
        self.active_position = None

    def indicator_config(self):
        """
        Returns a list of indicator configs for plotting. Plots signal candle high/low if present.
        """
        return [
            {"column": "signal_high", "label": "Signal High", "plot": True, "color": "purple", "type": "dash", "panel": 1},
            {"column": "signal_low", "label": "Signal Low", "plot": True, "color": "brown", "type": "dash", "panel": 1}
        ]

    def generate_signals(self, data):
        """
        Adds 'signal' column to data:
        1 = Long Entry, -1 = Short Entry, 0 = No Entry/Flat
        Only one active trade at a time, and only one TP trade per day.
        """
        import logging
        df = data.copy()
        df['signal'] = 0
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        df['time'] = pd.to_datetime(df['timestamp']).dt.time
        df['signal_high'] = None
        df['signal_low'] = None

        debug = self.params.get('debug', False)
        logger = logging.getLogger('FirstCandleBreakoutStrategy')
        if debug:
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.WARNING)

        # Prepare to track per-day state
        last_date = None
        in_position = False
        day_done = False
        signal_high = None
        signal_low = None
        signal_candle_time = None
        entry_idx = None

        for idx, row in df.iterrows():
            cur_date = row['date']
            cur_time = row['time']
            if last_date != cur_date:
                # New day, reset state
                in_position = False
                day_done = False
                signal_high = None
                signal_low = None
                signal_candle_time = None
                entry_idx = None
                last_date = cur_date

            if signal_candle_time is None:
                # Find the first candle at or after session_start
                if cur_time.strftime('%H:%M') >= self.session_start:
                    signal_high = row['high']
                    signal_low = row['low']
                    signal_candle_time = cur_time
                    if debug:
                        logger.info(f"{row['timestamp']} | Signal Candle: HIGH={signal_high:.2f}, LOW={signal_low:.2f}")
                    continue

            df.at[idx, 'signal_high'] = signal_high
            df.at[idx, 'signal_low'] = signal_low

            if day_done or in_position or signal_high is None:
                continue

            # Entry logic
            if row['close'] > signal_high:
                df.at[idx, 'signal'] = 1
                in_position = True
                entry_idx = idx
                # Set persistent SL and direction
                self.active_stop_loss = row['low']
                self.active_position = 'long'
                if debug:
                    logger.info(f"{row['timestamp']} | LONG ENTRY @ {row['close']:.2f} | Signal HIGH={signal_high:.2f} | SL={row['low']:.2f} | TP={row['close'] + self.target_points:.2f}")
            elif row['close'] < signal_low:
                df.at[idx, 'signal'] = -1
                in_position = True
                entry_idx = idx
                # Set persistent SL and direction
                self.active_stop_loss = row['high']
                self.active_position = 'short'
                if debug:
                    logger.info(f"{row['timestamp']} | SHORT ENTRY @ {row['close']:.2f} | Signal LOW={signal_low:.2f} | SL={row['high']:.2f} | TP={row['close'] - self.target_points:.2f}")
        return df

    def should_exit(self, position, row, entry_price):
        import logging
        debug = self.params.get('debug', False)
        logger = logging.getLogger('FirstCandleBreakoutStrategy')
        if debug:
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.WARNING)
        exit_now = False
        reason = ''
        # Use persistent SL
        sl = self.active_stop_loss
        if position == 'long':
            tp = entry_price + self.target_points
            if row.high >= tp:
                exit_now = True
                reason = 'Target'
            elif sl is not None and row.low <= sl:
                exit_now = True
                reason = 'Stop Loss'
        elif position == 'short':
            tp = entry_price - self.target_points
            if row.low <= tp:
                exit_now = True
                reason = 'Target'
            elif sl is not None and row.high >= sl:
                exit_now = True
                reason = 'Stop Loss'
        if exit_now:
            # Reset persistent SL and direction
            self.active_stop_loss = None
            self.active_position = None
            if debug:
                sl_str = f"{sl:.2f}" if sl is not None else "N/A"
                tp_str = f"{tp:.2f}" if tp is not None else "N/A"
                logger.info(f"{row.timestamp} | EXIT {position.upper()} @ {row.close:.2f} | SL={sl_str} | TP={tp_str} | Reason={reason}")
        return exit_now, reason
