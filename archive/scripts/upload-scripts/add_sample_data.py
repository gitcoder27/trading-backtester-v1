"""
Quick script to add sample backtest data for testing the frontend charts
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import sqlite3
import json
from datetime import datetime, timedelta
import numpy as np

# Connect to the database
db_path = 'backend/database/backtester.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create tables if they don't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS backtests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_name TEXT NOT NULL,
    dataset_name TEXT,
    initial_capital REAL DEFAULT 100000,
    parameters TEXT,
    results TEXT,
    performance_metrics TEXT,
    equity_curve TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'completed'
)
''')

# Generate sample equity curve data
def generate_sample_equity_curve(days=252, initial_capital=100000):
    """Generate realistic equity curve data"""
    dates = []
    equity = []
    
    # Generate dates for the last year
    start_date = datetime.now() - timedelta(days=days)
    
    current_equity = initial_capital
    equity.append(current_equity)
    dates.append(start_date.isoformat())
    
    # Generate returns with some trend and volatility
    for i in range(1, days):
        daily_return = np.random.normal(0.0008, 0.015)  # 0.08% average daily return, 1.5% volatility
        current_equity = current_equity * (1 + daily_return)
        equity.append(current_equity)
        
        current_date = start_date + timedelta(days=i)
        dates.append(current_date.isoformat())
    
    return dates, equity

# Generate sample performance metrics
def generate_sample_metrics(equity_curve):
    """Generate realistic performance metrics"""
    returns = np.diff(equity_curve) / equity_curve[:-1]
    
    total_return = (equity_curve[-1] - equity_curve[0]) / equity_curve[0]
    volatility = np.std(returns) * np.sqrt(252)
    sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)
    
    # Calculate drawdown
    peak = np.maximum.accumulate(equity_curve)
    drawdown = (equity_curve - peak) / peak
    max_drawdown = np.min(drawdown)
    
    # Trade statistics
    total_trades = np.random.randint(150, 300)
    win_rate = np.random.uniform(0.55, 0.75)
    profit_factor = np.random.uniform(1.2, 2.5)
    
    return {
        'total_return': total_return,
        'volatility': volatility,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'total_trades': total_trades,
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'calmar_ratio': total_return / abs(max_drawdown) if max_drawdown != 0 else 0,
        'sortino_ratio': sharpe_ratio * 1.2,  # Approximation
        'avg_trade_duration': np.random.uniform(1.5, 4.5)
    }

# Sample strategies
strategies = [
    'EMA Crossover Strategy',
    'RSI Mean Reversion',
    'Bollinger Bands Breakout',
    'MACD Signal Strategy',
    'Moving Average Scalper'
]

# Insert sample data
for i, strategy in enumerate(strategies, 1):
    dates, equity = generate_sample_equity_curve()
    metrics = generate_sample_metrics(equity)
    
    # Generate sample returns data
    returns = np.diff(equity) / equity[:-1]
    
    # Generate sample trade data
    winning_trades = []
    losing_trades = []
    
    for j in range(int(metrics['total_trades'] * metrics['win_rate'])):
        trade_date = np.random.choice(dates[:-1])
        pnl_percent = np.random.uniform(0.005, 0.05)  # 0.5% to 5% profit
        winning_trades.append({
            'entry_date': trade_date,
            'pnl_percent': pnl_percent
        })
    
    for j in range(int(metrics['total_trades'] * (1 - metrics['win_rate']))):
        trade_date = np.random.choice(dates[:-1])
        pnl_percent = -np.random.uniform(0.005, 0.03)  # 0.5% to 3% loss
        losing_trades.append({
            'entry_date': trade_date,
            'pnl_percent': pnl_percent
        })
    
    # Create the data structures expected by the frontend
    equity_curve_data = {
        'dates': dates,
        'equity': equity
    }
    
    drawdown_curve = []
    peak = equity[0]
    for eq in equity:
        if eq > peak:
            peak = eq
        drawdown_curve.append((eq - peak) / peak)
    
    drawdown_data = {
        'dates': dates,
        'drawdown': drawdown_curve
    }
    
    returns_data = {
        'returns': returns.tolist()
    }
    
    trades_data = {
        'winning_trades': winning_trades,
        'losing_trades': losing_trades
    }
    
    # Prepare chart data for all endpoints
    chart_data = {
        'equity': equity_curve_data,
        'drawdown': drawdown_data,
        'returns': returns_data,
        'trades': trades_data
    }
    
    cursor.execute('''
        INSERT INTO backtests (
            strategy_name, 
            dataset_name, 
            initial_capital, 
            parameters, 
            performance_metrics,
            equity_curve,
            status
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        strategy,
        f'NIFTY_1min_sample_{i}.csv',
        100000,
        json.dumps({'lookback': 20 + i * 5, 'threshold': 0.02 + i * 0.005}),
        json.dumps(metrics),
        json.dumps(chart_data),
        'completed'
    ))

conn.commit()
conn.close()

print("Sample backtest data inserted successfully!")
print(f"Added {len(strategies)} sample backtests with realistic performance data.")
print("You can now test the frontend charts with this data.")
