"""
main.py
Entry point for running backtests and comparing trading strategies.
"""

import os
import sys
from backtester.data_loader import load_csv
from backtester.engine import BacktestEngine
from backtester.metrics import total_return, sharpe_ratio, max_drawdown, win_rate, profit_factor, largest_winning_trade, largest_losing_trade, average_holding_time, max_consecutive_wins, max_consecutive_losses, trading_sessions_days, trading_sessions_years
from backtester.reporting import plot_equity_curve, plot_trades_on_price, save_trade_log, generate_html_report
from strategies.bbands_scalper import BBandsScalperStrategy
from strategies.bbands_rsi_stochastic import BBandsRSIStochasticStrategy
from strategies.ema10_scalper import EMA10ScalperStrategy
from strategies.ema44_scalper import EMA44ScalperStrategy
from strategies.first_candle_breakout import FirstCandleBreakoutStrategy
from strategies.rsi_cross_strategy import RSICrossStrategy
from strategies.ema50_scalper import EMA50ScalperStrategy
from strategies.mean_reversion_scalper import MeanReversionScalper
from strategies.mean_reversion_confirmed_scalper import MeanReversionConfirmedScalper
from strategies.awesome_scalper import AwesomeScalperStrategy
from strategies.intraday_ema_trade import IntradayEmaTradeStrategy
from strategies.rsi_midday_reversion_scalper import RSIMiddayReversionScalper
import argparse
import pandas as pd

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Run backtester with dynamic CSV and date range")
    parser.add_argument('-f','--file',help='Path to CSV data file',default=None)
    parser.add_argument('-s','--start',help='Start date (YYYY-MM-DD)',default=None)
    parser.add_argument('-e','--end',help='End date (YYYY-MM-DD)',default=None)
    parser.add_argument('-r','--report',help='Generate HTML report',action='store_true')
    parser.add_argument('-t','--timeframe',help="Timeframe for resampling (e.g. '1min', '2min', '5min', '10min')",default='1min')
    parser.add_argument('--debug', action='store_true', help='Enable debug/info logging for strategy internals')
    parser.add_argument('--option-delta', type=float, default=0.5, help='ATM option delta (e.g. 0.5 for ATM, 0.7 for ITM)')
    parser.add_argument('--lots', type=int, default=2, help='Number of lots to trade (1 lot = 75 units)')
    parser.add_argument('--option-price-per-unit', type=float, default=1.0, help='Multiplier for option price per unit (default 1.0)')
    parser.add_argument('--non-interactive', action='store_true', help='Run in non-interactive mode')
    parser.add_argument(
        '--no-intraday',
        dest='intraday',
        action='store_false',
        help='Disable intraday mode and allow trades past 15:15',
    )
    parser.set_defaults(intraday=True)
    args = parser.parse_args()

    # Set up logging for debug/info output
    import logging
    if args.debug:
        logging.basicConfig(level=logging.INFO, format="%(message)s")
    else:
        logging.basicConfig(level=logging.WARNING)

    # Load data
    if args.file:
        data_path = args.file
    else:
        files = [f for f in os.listdir("data") if f.endswith(".csv")]
        print("Available data files:")
        for i,f in enumerate(files): print(f"{i}: {f}")
        idx = int(input("Select file index: "))
        data_path = os.path.join("data",files[idx])
    data = load_csv(data_path, timeframe=args.timeframe)

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
    strategy_params = {'debug': args.debug}
    strategy = RSIMiddayReversionScalper(params=strategy_params)
    # strategy = BBandsRSIStochasticStrategy(params=strategy_params)
    # strategy = AwesomeScalperStrategy(params=strategy_params)
    # strategy = IntradayEmaTradeStrategy(params=strategy_params)
    # strategy = MeanReversionConfirmedScalper(params=strategy_params)
    # strategy = MomentumScalperStrategy(params=strategy_params)
    # strategy = EMA44ScalperStrategy()
    # strategy = BBandsScalperStrategy()
    # strategy = FirstCandleBreakoutStrategy(params=strategy_params)
    # strategy = RSICrossStrategy(params=strategy_params)
    # strategy = EMA50ScalperStrategy(params=strategy_params)
    # strategy = EMA10ScalperStrategy(params=strategy_params)

    # Run backtest
    engine = BacktestEngine(
        data,
        strategy,
        option_delta=args.option_delta,
        lots=args.lots,
        option_price_per_unit=args.option_price_per_unit,
        intraday=args.intraday,
    )
    results = engine.run()

    # Calculate metrics
    equity_curve = results['equity_curve']
    trade_log = results['trade_log']
    indicators = results['indicators'] if 'indicators' in results else None

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
    print(f"Trading Sessions (days): {trading_sessions_days(equity_curve)}")
    print(f"Trading Sessions (years): {trading_sessions_years(equity_curve):.2f}")

    # Trade stats
    if len(trade_log) > 0:
        long_trades = trade_log[trade_log['direction'].str.lower().isin(['buy', 'long'])]
        short_trades = trade_log[trade_log['direction'].str.lower().isin(['sell', 'short'])]
        win_long_trades = long_trades[long_trades['pnl'] > 0]
        win_short_trades = short_trades[short_trades['pnl'] > 0]
        print(f"Total Long Trades: {len(long_trades)}")
        print(f"Total Short Trades: {len(short_trades)}")
        print(f"Total Winning Long Trades: {len(win_long_trades)}")
        print(f"Total Winning Short Trades: {len(win_short_trades)}")
    else:
        long_trades = pd.DataFrame()
        short_trades = pd.DataFrame()
        win_long_trades = pd.DataFrame()
        win_short_trades = pd.DataFrame()
        print(f"Total Long Trades: 0")
        print(f"Total Short Trades: 0")
        print(f"Total Winning Long Trades: 0")
        print(f"Total Winning Short Trades: 0")

    # Round numeric columns to 2 decimals before saving
    for col in ['entry_price', 'exit_price', 'pnl', 'final_pnl', 'day_pnl']:
        if col in trade_log.columns:
            trade_log[col] = trade_log[col].round(2)
    # Ensure the filename is specific to the strategy
    strategy_name = strategy.__class__.__name__.lower().replace("strategy", "")
    save_trade_log(trade_log, os.path.join("results", f"{strategy_name}_trades.csv"))

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
        # Attach indicator configuration for HTML report
        if hasattr(strategy, 'indicator_config'): # Check if method exists
            results_metrics['indicator_cfg'] = strategy.indicator_config()
        else:
            results_metrics['indicator_cfg'] = {} # Default empty config

        os.makedirs("results", exist_ok=True)
        report_path = os.path.join("results","report.html")
        generate_html_report(equity_curve, data, trade_log, indicators, results_metrics, report_path)
        print(f"HTML report saved to {report_path}")

    # Command loop for user actions
    if not args.non_interactive:
        pass
if __name__ == "__main__":
    main()
