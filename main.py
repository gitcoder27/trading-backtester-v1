"""
main.py
Entry point for running backtests and comparing trading strategies.
"""

import os
import sys
from backtester.data_loader import load_csv
from backtester.engine import BacktestEngine
from backtester.metrics import total_return, sharpe_ratio, max_drawdown, win_rate, profit_factor, largest_winning_trade, largest_losing_trade, average_holding_time, max_consecutive_wins, max_consecutive_losses
from backtester.reporting import plot_equity_curve, plot_trades_on_price, save_trade_log, generate_html_report
from strategies.ema44_scalper import EMA44ScalperStrategy
import argparse
import pandas as pd

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Run backtester with dynamic CSV and date range")
    parser.add_argument('-f','--file',help='Path to CSV data file',default=None)
    parser.add_argument('-s','--start',help='Start date (YYYY-MM-DD)',default=None)
    parser.add_argument('-e','--end',help='End date (YYYY-MM-DD)',default=None)
    parser.add_argument('-r','--report',help='Generate HTML report',action='store_true')
    args = parser.parse_args()

    # Load data
    if args.file:
        data_path = args.file
    else:
        files = [f for f in os.listdir("data") if f.endswith(".csv")]
        print("Available data files:")
        for i,f in enumerate(files): print(f"{i}: {f}")
        idx = int(input("Select file index: "))
        data_path = os.path.join("data",files[idx])
    data = load_csv(data_path)

    # Filter by date range (handle tz-naive vs tz-aware)
    if args.start:
        start_dt = pd.to_datetime(args.start)
        tz = data['timestamp'].dt.tz
        if tz is not None and start_dt.tzinfo is None:
            start_dt = start_dt.tz_localize(tz)
        data = data[data['timestamp'] >= start_dt]
    if args.end:
        end_dt = pd.to_datetime(args.end)
        tz = data['timestamp'].dt.tz
        if tz is not None and end_dt.tzinfo is None:
            end_dt = end_dt.tz_localize(tz)
        data = data[data['timestamp'] <= end_dt]

    # Initialize strategy
    strategy = EMA44ScalperStrategy()

    # Run backtest
    engine = BacktestEngine(data, strategy)
    results = engine.run()

    # Calculate metrics
    equity_curve = results['equity_curve']
    trade_log = results['trade_log']
    indicators = results['indicators']

    print("Performance Metrics:")
    start_amount = equity_curve['equity'].iloc[0]
    final_amount = equity_curve['equity'].iloc[-1]
    print(f"Start Amount: {start_amount:.2f}")
    print(f"Final Amount: {final_amount:.2f}")
    print(f"Total Return: {total_return(equity_curve)*100:.2f}%")
    print(f"Sharpe Ratio: {sharpe_ratio(equity_curve):.2f}")
    print(f"Max Drawdown: {max_drawdown(equity_curve)*100:.2f}%")
    print(f"Win Rate: {win_rate(trade_log)*100:.2f}%")
    print(f"Total Trades: {len(trade_log)}")
    print(f"Profit Factor: {profit_factor(trade_log):.2f}")
    print(f"Largest Winning Trade: {largest_winning_trade(trade_log):.2f}")
    print(f"Largest Losing Trade: {largest_losing_trade(trade_log):.2f}")
    avg_hold = average_holding_time(trade_log)
    print(f"Average Holding Time: {avg_hold:.2f} min" if avg_hold==avg_hold else "Average Holding Time: N/A")
    print(f"Max Consecutive Wins: {max_consecutive_wins(trade_log)}")
    print(f"Max Consecutive Losses: {max_consecutive_losses(trade_log)}")

    # Trade stats
    long_trades = trade_log[trade_log['direction'].str.lower().isin(['buy', 'long'])]
    short_trades = trade_log[trade_log['direction'].str.lower().isin(['sell', 'short'])]
    win_long_trades = long_trades[long_trades['pnl'] > 0]
    win_short_trades = short_trades[short_trades['pnl'] > 0]
    print(f"Total Long Trades: {len(long_trades)}")
    print(f"Total Short Trades: {len(short_trades)}")
    print(f"Total Winning Long Trades: {len(win_long_trades)}")
    print(f"Total Winning Short Trades: {len(win_short_trades)}")

    # Round numeric columns to 2 decimals before saving
    for col in ['entry_price', 'exit_price', 'pnl', 'final_pnl', 'day_pnl']:
        if col in trade_log.columns:
            trade_log[col] = trade_log[col].round(2)
    save_trade_log(trade_log, os.path.join("results", "ema44_scalper_trades.csv"))

    # Generate HTML report if requested
    if args.report:
        results_metrics = {
            'Start Amount': start_amount,
            'Final Amount': final_amount,
            'Total Return (%)': total_return(equity_curve)*100,
            'Sharpe Ratio': sharpe_ratio(equity_curve),
            'Max Drawdown (%)': max_drawdown(equity_curve)*100,
            'Win Rate (%)': win_rate(trade_log)*100,
            'Total Trades': len(trade_log),
            'Profit Factor': profit_factor(trade_log),
            'Largest Winning Trade': largest_winning_trade(trade_log),
            'Largest Losing Trade': largest_losing_trade(trade_log),
            'Average Holding Time (min)': avg_hold if avg_hold==avg_hold else None,
            'Max Consecutive Wins': max_consecutive_wins(trade_log),
            'Max Consecutive Losses': max_consecutive_losses(trade_log),
            'Total Long Trades': len(long_trades),
            'Total Short Trades': len(short_trades),
            'Winning Long Trades': len(win_long_trades),
            'Winning Short Trades': len(win_short_trades)
        }
        os.makedirs("results", exist_ok=True)
        report_path = os.path.join("results","report.html")
        generate_html_report(equity_curve, data, trade_log, indicators, results_metrics, report_path)
        print(f"HTML report saved to {report_path}")

    # Command loop for user actions
    while True:
        cmd = input("Enter command ([t]rades plot, [e]quity curve, [q]uit): ").strip().lower()
        if cmd == "t":
            from backtester.reporting import plot_trades_on_candlestick_plotly
            plot_trades_on_candlestick_plotly(data, trade_log, indicators=indicators, title="Trades on Candlestick Chart")
        elif cmd == "e":
            plot_equity_curve(equity_curve, trades=trade_log, indicators=indicators, title="EMA-10 Scalper Equity Curve", interactive=True)
        elif cmd == "q":
            print("Exiting program.")
            sys.exit(0)
        else:
            print("Unknown command. Please enter 't' for trades plot, 'e' for equity curve, or 'q' to quit.")
if __name__ == "__main__":
    main()