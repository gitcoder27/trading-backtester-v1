"""
main.py
Entry point for running backtests and comparing trading strategies.
"""

import os
import sys
from backtester.data_loader import load_csv
from backtester.engine import BacktestEngine
from backtester.metrics import total_return, sharpe_ratio, max_drawdown, win_rate
from backtester.reporting import plot_equity_curve, plot_trades_on_price, save_trade_log
from strategies.ema10_scalper import EMA10ScalperStrategy

def main():
    # Load data
    data_path = os.path.join("data", "nifty_2024_1min_22Dec_14Jan.csv")
    data = load_csv(data_path)

    # Initialize strategy
    strategy = EMA10ScalperStrategy()

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

    # Trade stats
    long_trades = trade_log[trade_log['direction'].str.lower().isin(['buy', 'long'])]
    short_trades = trade_log[trade_log['direction'].str.lower().isin(['sell', 'short'])]
    win_long_trades = long_trades[long_trades['pnl'] > 0]
    win_short_trades = short_trades[short_trades['pnl'] > 0]
    print(f"Total Long Trades: {len(long_trades)}")
    print(f"Total Short Trades: {len(short_trades)}")
    print(f"Total Winning Long Trades: {len(win_long_trades)}")
    print(f"Total Winning Short Trades: {len(win_short_trades)}")

    # Save trade log
    save_trade_log(trade_log, os.path.join("results", "ema10_scalper_trades.csv"))

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