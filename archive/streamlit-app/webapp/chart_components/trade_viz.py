"""
Trade visualization data processing.
"""

from __future__ import annotations
import pandas as pd
from typing import List, Union
import logging

from .models import TradeData, TradePoint, ChartOptions

logger = logging.getLogger(__name__)


class TradeVisualizer:
    """Handles trade data processing for chart visualization."""
    
    REQUIRED_TRADE_COLUMNS = {'entry_time', 'entry_price', 'exit_time', 'exit_price'}
    
    @staticmethod
    def process_trades_for_chart(
        trades: pd.DataFrame,
        options: ChartOptions
    ) -> TradeData:
        """Process trades DataFrame into chart visualization data."""
        trade_data = TradeData()
        
        if trades is None or trades.empty:
            return trade_data
        
        if not TradeVisualizer.REQUIRED_TRADE_COLUMNS.issubset(trades.columns):
            logger.warning(f"Trades missing required columns: {TradeVisualizer.REQUIRED_TRADE_COLUMNS}")
            return trade_data
        
        trades_df = trades.copy()
        trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'], errors='coerce')
        trades_df['exit_time'] = pd.to_datetime(trades_df['exit_time'], errors='coerce')
        
        entries = []
        exits = []
        win_lines = []
        loss_lines = []
        
        for _, trade in trades_df.iterrows():
            if pd.isna(trade['entry_time']) or pd.isna(trade['exit_time']):
                continue
            
            # Extract trade information
            direction = str(trade.get('direction', 'long')).lower()
            pnl = float(trade.get('pnl', 0) or 0)
            
            # Determine colors based on direction and outcome
            entry_color = (options.long_entry_color if direction == 'long' 
                          else options.short_entry_color)
            exit_color = (options.profit_exit_color if pnl >= 0 
                         else options.loss_exit_color)
            
            # Convert timestamps to milliseconds for ECharts
            entry_time_ms = int(trade['entry_time'].value // 10**6)
            exit_time_ms = int(trade['exit_time'].value // 10**6)
            entry_price = float(trade.get('entry_price', 0))
            exit_price = float(trade.get('exit_price', 0))
            
            # Create entry and exit points
            entry_point = TradePoint(
                value=[entry_time_ms, entry_price],
                itemStyle={
                    'color': entry_color,
                    'borderColor': '#ffffff',
                    'borderWidth': 2
                }
            )
            
            exit_point = TradePoint(
                value=[exit_time_ms, exit_price],
                itemStyle={
                    'color': exit_color,
                    'borderColor': '#ffffff',
                    'borderWidth': 2
                }
            )
            
            entries.append(entry_point)
            exits.append(exit_point)
            
            # Add trade line to appropriate list (win/loss)
            trade_line = [entry_time_ms, entry_price], [exit_time_ms, exit_price], None
            if pnl >= 0:
                win_lines.extend(trade_line)
            else:
                loss_lines.extend(trade_line)
        
        trade_data.entries = entries
        trade_data.exits = exits
        trade_data.win_lines = win_lines
        trade_data.loss_lines = loss_lines
        
        logger.info(f"Processed {len(entries)} trade entries and {len(exits)} exits")
        
        return trade_data
    
    @staticmethod
    def get_trade_statistics(trade_data: TradeData) -> dict:
        """Get statistics about processed trade data."""
        return {
            'total_entries': len(trade_data.entries),
            'total_exits': len(trade_data.exits),
            'winning_trades': len([line for line in trade_data.win_lines if line is not None]) // 3,
            'losing_trades': len([line for line in trade_data.loss_lines if line is not None]) // 3,
            'has_trades': trade_data.has_trades
        }
