"""
Trade Analyzer
Specialized analysis of individual trades and trading patterns
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from .data_formatter import DataFormatter


class TradeAnalyzer:
    """Analyzer for trade patterns and individual trade analysis"""
    
    def __init__(self):
        self.formatter = DataFormatter()
    
    def analyze_trades_comprehensive(self, trades: pd.DataFrame) -> Dict[str, Any]:
        """Comprehensive analysis of all trades"""
        if trades.empty:
            return self._get_empty_trade_analysis()
        
        # Basic trade metrics
        basic_metrics = self._calculate_basic_trade_metrics(trades)
        
        # Time-based analysis
        time_analysis = self._analyze_trades_by_time(trades)
        
        # Performance analysis
        performance_analysis = self._analyze_trade_performance(trades)
        
        # Direction analysis
        direction_analysis = self._analyze_trades_by_direction(trades)
        
        return {
            **basic_metrics,
            'time_analysis': time_analysis,
            'performance_analysis': performance_analysis,
            'direction_analysis': direction_analysis
        }
    
    def _calculate_basic_trade_metrics(self, trades: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic trade statistics"""
        total_trades = len(trades)
        
        if 'pnl' not in trades.columns:
            return {
                'total_trades': total_trades,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0
            }
        
        # Convert PnL to numeric
        pnl = pd.to_numeric(trades['pnl'], errors='coerce').fillna(0)
        
        winning_trades = len(pnl[pnl > 0])
        losing_trades = len(pnl[pnl <= 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': float(win_rate)
        }
    
    def _analyze_trades_by_time(self, trades: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trades by time patterns"""
        if 'entry_time' not in trades.columns:
            return {}
        
        try:
            # Convert entry time to datetime
            trades_copy = trades.copy()
            trades_copy['entry_time'] = pd.to_datetime(trades_copy['entry_time'])
            
            # Extract time components
            trades_copy['hour'] = trades_copy['entry_time'].dt.hour
            trades_copy['weekday'] = trades_copy['entry_time'].dt.day_name()
            trades_copy['month'] = trades_copy['entry_time'].dt.month_name()
            
            analysis = {}
            
            # Hourly analysis
            if 'pnl' in trades_copy.columns:
                hourly_pnl = trades_copy.groupby('hour')['pnl'].agg(['sum', 'count', 'mean']).reset_index()
                analysis['hourly_performance'] = self.formatter.clean_dataframe_for_json(hourly_pnl)
                
                # Weekday analysis
                weekday_pnl = trades_copy.groupby('weekday')['pnl'].agg(['sum', 'count', 'mean']).reset_index()
                analysis['weekday_performance'] = self.formatter.clean_dataframe_for_json(weekday_pnl)
                
                # Monthly analysis
                monthly_pnl = trades_copy.groupby('month')['pnl'].agg(['sum', 'count', 'mean']).reset_index()
                analysis['monthly_performance'] = self.formatter.clean_dataframe_for_json(monthly_pnl)
            
            # Best and worst hours
            if 'hourly_performance' in analysis and analysis['hourly_performance']:
                hourly_data = analysis['hourly_performance']
                best_hour = max(hourly_data, key=lambda x: x.get('sum', 0))
                worst_hour = min(hourly_data, key=lambda x: x.get('sum', 0))
                
                analysis['best_trading_hour'] = best_hour.get('hour', 'N/A')
                analysis['worst_trading_hour'] = worst_hour.get('hour', 'N/A')
            
            return analysis
            
        except Exception:
            return {}
    
    def _analyze_trade_performance(self, trades: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trade performance distribution"""
        if 'pnl' not in trades.columns:
            return {}
        
        try:
            pnl = pd.to_numeric(trades['pnl'], errors='coerce').fillna(0)
            
            # Performance distribution
            performance_stats = {
                'total_pnl': float(pnl.sum()),
                'avg_pnl': float(pnl.mean()),
                'median_pnl': float(pnl.median()),
                'std_pnl': float(pnl.std()),
                'min_pnl': float(pnl.min()),
                'max_pnl': float(pnl.max())
            }
            
            # Percentile analysis
            percentiles = [10, 25, 75, 90, 95, 99]
            for p in percentiles:
                performance_stats[f'pnl_p{p}'] = float(pnl.quantile(p/100))
            
            # Profit factor
            gross_profit = pnl[pnl > 0].sum()
            gross_loss = abs(pnl[pnl <= 0].sum())
            profit_factor = float(gross_profit / gross_loss) if gross_loss > 0 else float('inf')
            
            performance_stats['gross_profit'] = float(gross_profit)
            performance_stats['gross_loss'] = float(gross_loss)
            performance_stats['profit_factor'] = profit_factor
            
            # Trade size analysis
            if 'quantity' in trades.columns or 'size' in trades.columns:
                size_col = 'quantity' if 'quantity' in trades.columns else 'size'
                sizes = pd.to_numeric(trades[size_col], errors='coerce').fillna(0)
                
                performance_stats['avg_trade_size'] = float(sizes.mean())
                performance_stats['max_trade_size'] = float(sizes.max())
                performance_stats['min_trade_size'] = float(sizes.min())
            
            return performance_stats
            
        except Exception:
            return {}
    
    def _analyze_trades_by_direction(self, trades: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trades by direction (long/short)"""
        direction_col = None
        
        # Find direction column
        for col in ['direction', 'side', 'type']:
            if col in trades.columns:
                direction_col = col
                break
        
        if direction_col is None:
            return {}
        
        try:
            trades_copy = trades.copy()
            trades_copy[direction_col] = trades_copy[direction_col].astype(str).str.lower()
            
            direction_analysis = {}
            
            # Count by direction
            direction_counts = trades_copy[direction_col].value_counts().to_dict()
            direction_analysis['trade_counts'] = direction_counts
            
            # PnL by direction
            if 'pnl' in trades_copy.columns:
                pnl_by_direction = trades_copy.groupby(direction_col)['pnl'].agg([
                    'sum', 'count', 'mean', 'std', 'min', 'max'
                ]).reset_index()
                
                direction_analysis['pnl_by_direction'] = self.formatter.clean_dataframe_for_json(pnl_by_direction)
                
                # Win rate by direction
                win_rates = {}
                for direction in trades_copy[direction_col].unique():
                    direction_trades = trades_copy[trades_copy[direction_col] == direction]
                    if len(direction_trades) > 0:
                        winning = len(direction_trades[direction_trades['pnl'] > 0])
                        win_rate = (winning / len(direction_trades)) * 100
                        win_rates[direction] = float(win_rate)
                
                direction_analysis['win_rates'] = win_rates
            
            return direction_analysis
            
        except Exception:
            return {}
    
    def get_trades_data_paginated(
        self,
        trades: pd.DataFrame,
        page: int = 1,
        page_size: int = 100,
        sort_by: str = "entry_time",
        sort_order: str = "desc",
        filter_profitable: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Get paginated and filtered trade data"""
        
        if trades.empty:
            return {
                'trades': [],
                'total_trades': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0
            }
        
        trades_df = trades.copy()
        
        # Convert datetime columns
        for col in ['entry_time', 'exit_time']:
            if col in trades_df.columns:
                trades_df[col] = pd.to_datetime(trades_df[col], errors='coerce')
        
        # Calculate duration if not present
        if ('duration' not in trades_df.columns and 
            'entry_time' in trades_df.columns and 
            'exit_time' in trades_df.columns):
            
            try:
                duration_seconds = (trades_df['exit_time'] - trades_df['entry_time']).dt.total_seconds()
                trades_df['duration'] = duration_seconds / 60  # Convert to minutes
            except Exception:
                trades_df['duration'] = 0
        
        # Filter by profitability
        if filter_profitable is not None and 'pnl' in trades_df.columns:
            if filter_profitable:
                trades_df = trades_df[trades_df['pnl'] > 0]
            else:
                trades_df = trades_df[trades_df['pnl'] <= 0]
        
        # Sort trades
        if sort_by in trades_df.columns:
            ascending = (sort_order.lower() == 'asc')
            trades_df = trades_df.sort_values(by=sort_by, ascending=ascending)
        
        # Paginate
        total_trades = len(trades_df)
        total_pages = (total_trades + page_size - 1) // page_size
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        trades_page = trades_df.iloc[start_idx:end_idx]
        
        # Convert to JSON-safe format
        trades_list = self.formatter.clean_dataframe_for_json(trades_page)
        
        return {
            'trades': trades_list,
            'total_trades': total_trades,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
            'sort_by': sort_by,
            'sort_order': sort_order,
            'filter_profitable': filter_profitable
        }
    
    def calculate_trade_streaks(self, trades: pd.DataFrame) -> Dict[str, Any]:
        """Calculate winning and losing streaks"""
        if trades.empty or 'pnl' not in trades.columns:
            return {
                'max_winning_streak': 0,
                'max_losing_streak': 0,
                'current_streak': 0,
                'current_streak_type': 'none'
            }
        
        try:
            # Ensure trades are sorted by entry time
            if 'entry_time' in trades.columns:
                trades_sorted = trades.sort_values('entry_time')
            else:
                trades_sorted = trades.copy()
            
            pnl = pd.to_numeric(trades_sorted['pnl'], errors='coerce').fillna(0)
            
            # Calculate streaks
            is_winning = pnl > 0
            
            max_winning_streak = 0
            max_losing_streak = 0
            current_winning_streak = 0
            current_losing_streak = 0
            
            for is_win in is_winning:
                if is_win:
                    current_winning_streak += 1
                    current_losing_streak = 0
                    max_winning_streak = max(max_winning_streak, current_winning_streak)
                else:
                    current_losing_streak += 1
                    current_winning_streak = 0
                    max_losing_streak = max(max_losing_streak, current_losing_streak)
            
            # Determine current streak
            if len(pnl) > 0:
                if pnl.iloc[-1] > 0:
                    current_streak = current_winning_streak
                    current_streak_type = 'winning'
                else:
                    current_streak = current_losing_streak
                    current_streak_type = 'losing'
            else:
                current_streak = 0
                current_streak_type = 'none'
            
            return {
                'max_winning_streak': max_winning_streak,
                'max_losing_streak': max_losing_streak,
                'current_streak': current_streak,
                'current_streak_type': current_streak_type
            }
            
        except Exception:
            return {
                'max_winning_streak': 0,
                'max_losing_streak': 0,
                'current_streak': 0,
                'current_streak_type': 'none'
            }
    
    def _get_empty_trade_analysis(self) -> Dict[str, Any]:
        """Return empty trade analysis structure"""
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'time_analysis': {},
            'performance_analysis': {},
            'direction_analysis': {}
        }
