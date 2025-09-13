"""
Chart Generator
Handles all chart creation for analytics visualization
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
import json
from typing import Dict, Any, List, Optional
from .data_formatter import DataFormatter


class ChartGenerator:
    """Generator for all chart types used in analytics"""
    
    def __init__(self):
        self.formatter = DataFormatter()
        
        # Color schemes for charts
        self.colors = {
            'primary': '#2196F3',
            'secondary': '#FF9800', 
            'success': '#4CAF50',
            'danger': '#F44336',
            'warning': '#FF5722',
            'info': '#00BCD4',
            'purple': '#9C27B0',
            'pink': '#E91E63'
        }
    
    def create_equity_chart(self, equity_curve: pd.DataFrame, max_points: Optional[int] = None) -> str:
        """Create equity curve chart"""
        if equity_curve.empty or 'equity' not in equity_curve.columns:
            return self._create_empty_chart("Equity Curve")
        
        # Downsample if needed
        data = self._downsample_timeseries(equity_curve, max_points)
        
        fig = go.Figure()
        
        # Add equity line
        fig.add_trace(go.Scatter(
            x=data['timestamp'] if 'timestamp' in data.columns else data.index,
            y=data['equity'],
            mode='lines',
            name='Equity',
            line=dict(color=self.colors['primary'], width=2),
            hovertemplate='<b>Equity</b>: %{y:,.2f}<br><b>Time</b>: %{x}<extra></extra>'
        ))
        
        # Update layout
        fig.update_layout(
            title='Portfolio Equity Curve',
            xaxis_title='Time',
            yaxis_title='Equity ($)',
            hovermode='x unified',
            template='plotly_white',
            height=400
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)
    
    def create_drawdown_chart(self, equity_curve: pd.DataFrame, max_points: Optional[int] = None) -> str:
        """Create drawdown chart with underwater curve"""
        if equity_curve.empty or 'equity' not in equity_curve.columns:
            return self._create_empty_chart("Drawdown")
        
        # Calculate drawdown
        drawdown_data = self._compute_drawdown(equity_curve)
        drawdown_data = self._downsample_timeseries(drawdown_data, max_points)
        
        fig = go.Figure()
        
        # Add drawdown fill
        fig.add_trace(go.Scatter(
            x=drawdown_data['timestamp'] if 'timestamp' in drawdown_data.columns else drawdown_data.index,
            y=drawdown_data['drawdown'] * 100,  # Convert to percentage
            mode='lines',
            name='Drawdown',
            fill='tonexty',
            line=dict(color=self.colors['danger'], width=1),
            fillcolor='rgba(244, 67, 54, 0.3)',
            hovertemplate='<b>Drawdown</b>: %{y:.2f}%<br><b>Time</b>: %{x}<extra></extra>'
        ))
        
        # Add zero line
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        # Update layout
        fig.update_layout(
            title='Drawdown Analysis (Underwater Curve)',
            xaxis_title='Time',
            yaxis_title='Drawdown (%)',
            hovermode='x unified',
            template='plotly_white',
            height=400,
            yaxis=dict(range=[drawdown_data['drawdown'].min() * 110, 5])  # Show a bit above zero
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)
    
    def create_returns_distribution_chart(self, equity_curve: pd.DataFrame) -> str:
        """Create returns distribution histogram"""
        returns = self.formatter.normalize_returns_data(equity_curve)
        
        if returns.empty:
            return self._create_empty_chart("Returns Distribution")
        
        fig = go.Figure()
        
        # Create histogram
        fig.add_trace(go.Histogram(
            x=returns * 100,  # Convert to percentage
            nbinsx=50,
            name='Returns Distribution',
            opacity=0.7,
            marker_color=self.colors['primary'],
            hovertemplate='<b>Return Range</b>: %{x:.2f}%<br><b>Frequency</b>: %{y}<extra></extra>'
        ))
        
        # Add mean line
        mean_return = returns.mean() * 100
        fig.add_vline(x=mean_return, line_dash="dash", line_color=self.colors['success'], 
                     annotation_text=f"Mean: {mean_return:.2f}%")
        
        # Update layout
        fig.update_layout(
            title='Returns Distribution',
            xaxis_title='Returns (%)',
            yaxis_title='Frequency',
            template='plotly_white',
            height=400,
            showlegend=False
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)
    
    def create_trades_scatter_chart(self, trades: pd.DataFrame, equity_curve: pd.DataFrame, max_points: Optional[int] = None) -> str:
        """Create trades scatter plot on equity curve"""
        fig = go.Figure()
        
        # Add equity curve as background
        if not equity_curve.empty and 'equity' in equity_curve.columns:
            data = self._downsample_timeseries(equity_curve, max_points)
            fig.add_trace(go.Scatter(
                x=data['timestamp'] if 'timestamp' in data.columns else data.index,
                y=data['equity'],
                mode='lines',
                name='Equity Curve',
                line=dict(color=self.colors['primary'], width=2),
                opacity=0.7
            ))
        
        # Add trade markers
        if not trades.empty and 'entry_time' in trades.columns:
            self._add_trade_markers(fig, trades)
        
        # Update layout
        fig.update_layout(
            title='Trades on Equity Curve',
            xaxis_title='Time',
            yaxis_title='Value',
            hovermode='closest',
            template='plotly_white',
            height=400
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)
    
    def create_monthly_returns_heatmap(self, equity_curve: pd.DataFrame) -> str:
        """Create monthly returns heatmap"""
        returns = self.formatter.normalize_returns_data(equity_curve)
        
        if returns.empty:
            return self._create_empty_chart("Monthly Returns")
        
        try:
            # Resample to monthly returns
            monthly_returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
            
            # Create year-month matrix
            monthly_returns.index = pd.to_datetime(monthly_returns.index)
            monthly_returns_pct = monthly_returns * 100
            
            # Pivot data for heatmap
            heatmap_data = monthly_returns_pct.groupby([
                monthly_returns_pct.index.year,
                monthly_returns_pct.index.month
            ]).first().unstack(fill_value=0)
            
            if heatmap_data.empty:
                return self._create_empty_chart("Monthly Returns")
            
            fig = go.Figure(data=go.Heatmap(
                z=heatmap_data.values,
                x=[f"Month {i}" for i in heatmap_data.columns],
                y=[f"Year {i}" for i in heatmap_data.index],
                colorscale='RdYlGn',
                zmid=0,
                hovertemplate='<b>Year</b>: %{y}<br><b>Month</b>: %{x}<br><b>Return</b>: %{z:.2f}%<extra></extra>'
            ))
            
            fig.update_layout(
                title='Monthly Returns Heatmap',
                template='plotly_white',
                height=400
            )
            
            return json.dumps(fig, cls=PlotlyJSONEncoder)
            
        except Exception:
            # Fallback to simple line chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=returns.index,
                y=returns * 100,
                mode='lines',
                name='Monthly Returns'
            ))
            fig.update_layout(title='Returns Over Time', template='plotly_white')
            return json.dumps(fig, cls=PlotlyJSONEncoder)
    
    def create_comparison_chart(self, equity_curves: Dict[str, pd.DataFrame]) -> str:
        """Create comparison chart for multiple strategies"""
        if not equity_curves:
            return self._create_empty_chart("Strategy Comparison")
        
        fig = go.Figure()
        
        colors = [self.colors['primary'], self.colors['danger'], self.colors['success'], 
                 self.colors['warning'], self.colors['purple']]
        
        for i, (name, equity_curve) in enumerate(equity_curves.items()):
            if equity_curve.empty or 'equity' not in equity_curve.columns:
                continue
            
            # Normalize to percentage returns
            initial_value = equity_curve['equity'].iloc[0]
            if initial_value > 0:
                normalized_equity = (equity_curve['equity'] / initial_value - 1) * 100
                
                fig.add_trace(go.Scatter(
                    x=equity_curve['timestamp'] if 'timestamp' in equity_curve.columns else equity_curve.index,
                    y=normalized_equity,
                    mode='lines',
                    name=name,
                    line=dict(color=colors[i % len(colors)], width=2),
                    hovertemplate=f'<b>{name}</b><br><b>Return</b>: %{{y:.2f}}%<br><b>Time</b>: %{{x}}<extra></extra>'
                ))
        
        # Update layout
        fig.update_layout(
            title='Strategy Comparison (Normalized Returns)',
            xaxis_title='Time',
            yaxis_title='Returns (%)',
            hovermode='x unified',
            template='plotly_white',
            height=400
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)
    
    def create_rolling_metrics_chart(self, rolling_data: pd.DataFrame, metric: str = 'rolling_sharpe') -> str:
        """Create rolling metrics chart"""
        if rolling_data.empty or metric not in rolling_data.columns:
            return self._create_empty_chart(f"Rolling {metric.replace('_', ' ').title()}")
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=rolling_data['timestamp'] if 'timestamp' in rolling_data.columns else rolling_data.index,
            y=rolling_data[metric],
            mode='lines',
            name=metric.replace('_', ' ').title(),
            line=dict(color=self.colors['secondary'], width=2),
            hovertemplate=f'<b>{metric}</b>: %{{y:.3f}}<br><b>Time</b>: %{{x}}<extra></extra>'
        ))
        
        # Add zero line for Sharpe ratio
        if 'sharpe' in metric.lower():
            fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        # Update layout
        fig.update_layout(
            title=f'Rolling {metric.replace("_", " ").title()}',
            xaxis_title='Time',
            yaxis_title=metric.replace('_', ' ').title(),
            template='plotly_white',
            height=400
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)
    
    def _add_trade_markers(self, fig: go.Figure, trades: pd.DataFrame):
        """Add trade markers to chart"""
        if 'pnl' not in trades.columns:
            return
        
        try:
            # Separate winning and losing trades
            winning_trades = trades[trades['pnl'] > 0]
            losing_trades = trades[trades['pnl'] <= 0]
            
            # Add winning trade markers
            if not winning_trades.empty:
                fig.add_trace(go.Scatter(
                    x=winning_trades['entry_time'],
                    y=winning_trades.get('entry_price', winning_trades.get('price', [0] * len(winning_trades))),
                    mode='markers',
                    name='Winning Trades',
                    marker=dict(
                        color=self.colors['success'],
                        size=8,
                        symbol='triangle-up',
                        line=dict(width=1, color='white')
                    ),
                    hovertemplate='<b>Entry</b><br><b>Time</b>: %{x}<br><b>Price</b>: %{y:.2f}<br><b>PnL</b>: Positive<extra></extra>'
                ))
            
            # Add losing trade markers
            if not losing_trades.empty:
                fig.add_trace(go.Scatter(
                    x=losing_trades['entry_time'],
                    y=losing_trades.get('entry_price', losing_trades.get('price', [0] * len(losing_trades))),
                    mode='markers',
                    name='Losing Trades',
                    marker=dict(
                        color=self.colors['danger'],
                        size=8,
                        symbol='triangle-down',
                        line=dict(width=1, color='white')
                    ),
                    hovertemplate='<b>Entry</b><br><b>Time</b>: %{x}<br><b>Price</b>: %{y:.2f}<br><b>PnL</b>: Negative<extra></extra>'
                ))
                
        except Exception:
            # Skip adding markers if there's an error
            pass
    
    def _compute_drawdown(self, equity_curve: pd.DataFrame) -> pd.DataFrame:
        """Compute drawdown from equity curve"""
        if equity_curve.empty or 'equity' not in equity_curve.columns:
            return pd.DataFrame()
        
        equity_values = equity_curve['equity'].astype(float)
        cummax = equity_values.cummax()
        drawdown = (equity_values / cummax) - 1.0
        
        result = pd.DataFrame({
            'drawdown': drawdown
        })
        
        if 'timestamp' in equity_curve.columns:
            result['timestamp'] = equity_curve['timestamp']
        
        return result
    
    def _create_empty_chart(self, title: str) -> str:
        """Create an empty placeholder chart"""
        fig = go.Figure()
        
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        
        fig.update_layout(
            title=title,
            template='plotly_white',
            height=400,
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False)
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)

    def _downsample_timeseries(self, df: pd.DataFrame, max_points: Optional[int]) -> pd.DataFrame:
        """Downsample a time series DataFrame to at most max_points rows.

        Preserves the last point and samples evenly across the series.
        """
        if max_points is None:
            return df
        try:
            n = len(df)
            if n <= 0 or max_points <= 0 or n <= max_points:
                return df
            step = int(np.ceil(n / float(max_points)))
            sampled = df.iloc[::step].copy()
            # Ensure last row is included
            if sampled.index[-1] != df.index[-1]:
                sampled = pd.concat([sampled, df.iloc[[-1]]])
            return sampled
        except Exception:
            # Fallback to original data on any error
            return df
