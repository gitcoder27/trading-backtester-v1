# Trading Backtester v1

A modular backtesting framework for algorithmic trading strategies on historical market data. Supports running, analyzing, and reporting on multiple strategies with flexible CLI options.

---

## Features
- Run backtests on historical CSV data using various strategies (e.g., EMA Crossover, Bollinger Bands, RSI, First Candle Breakout).
- Modular strategy interface (add your own strategies easily).
- Detailed performance metrics (Sharpe, drawdown, profit factor, etc.).
- Interactive plots (Plotly) and comprehensive HTML reporting.
- Customizable timeframe resampling for historical data.
- Debug logging for in-depth strategy analysis.
- Indicator configurations included in HTML reports for better reproducibility.

---

## Requirements
- Python 3.8+
- Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Usage

### Debug Logging

You can enable detailed debug logging for strategy internals (signal prices, entries, exits, SL/TP) by passing the `--debug` flag to the script:

```sh
python main.py -f data/yourfile.csv -s 2024-12-24 -e 2024-12-30 --debug
```

When enabled, logs will show signal candle high/low, entry/exit points, SL/TP, and reasons for exits.

### Plotting Signal Candle Lines

For the First Candle Breakout strategy, the signal candle's high/low are plotted as indicator lines on the chart for easy visual debugging.

Run the main program using your Python interpreter:

```bash
python main.py [OPTIONS]
```

Or, if using a virtual environment:

```bash
tradeEnv\Scripts\python.exe main.py [OPTIONS]
```

### Command-Line Arguments

| Argument           | Description                                    | Example                        |
|--------------------|------------------------------------------------|--------------------------------|
| `-f`, `--file`     | Path to CSV data file                          | `-f data/my_data.csv`          |
| `-s`, `--start`    | Start date (YYYY-MM-DD)                        | `-s 2024-01-01`                |
| `-e`, `--end`      | End date (YYYY-MM-DD)                          | `-e 2024-01-31`                |
| `-r`, `--report`   | Generate HTML report (saved in `results/`)     | `-r`                           |
| `-t`, `--timeframe`| Timeframe for resampling (e.g. `1T`, `2T`, `5T`, `10T`, `15T`, or `1min`, `2min`, etc.). Default is `1T` (1 minute). | `-t 5T`                        |
| `--debug`          | Enable detailed debug logging for strategy internals. | `--debug`                      |

All arguments are optional. If no file is provided, you will be prompted to select a CSV from the `data/` directory.

*Note: To use a specific strategy, you currently need to modify `main.py` to instantiate the desired strategy class. By default, it uses `EMA50ScalperStrategy`.*

#### Example: Full Run (Default 1-Minute Data)

```bash
python main.py -f data/nifty_2024_1min_22Dec_14Jan.csv -s 2024-01-01 -e 2024-01-10 -r
```

#### Example: Run on 2-Minute or 5-Minute Candles

```bash
python main.py -f data/nifty_2024_1min_22Dec_14Jan.csv -s 2024-12-24 -e 2024-12-25 -r -t 2T
python main.py -f data/nifty_2024_1min_22Dec_14Jan.csv -t 5T
```

- The `-t` / `--timeframe` option lets you resample your 1-minute historical data to any higher timeframe supported by pandas offset aliases (e.g. `2T` for 2 minutes, `5T` for 5 minutes, or `10min` for 10 minutes).
- If you see a warning about `'T'` being deprecated, you can use `'min'` instead (e.g. `2min`).

---

## Interactive Commands (After Backtest)
After running a backtest, you can enter the following commands at the prompt:

- `t` : Show trades plotted on candlestick chart (Plotly)
- `e` : Show equity curve plot
- `q` : Quit the program

---

## Adding New Strategies
- Add your strategy as a new Python file in the `strategies/` directory (e.g., `my_strategy.py`).
- Your strategy class should inherit from `StrategyBase` (from `backtester.strategy_base`).
- Implement the `generate_signals(self, data)` method. This method should return a DataFrame with a 'signal' column (1 for buy, -1 for sell, 0 for hold).
- Optionally, implement an `indicator_config(self)` method to return a dictionary describing indicators to be plotted (see existing strategies for examples). This helps in visualizing strategy parameters on charts and in reports.
- To use your new strategy, import it in `main.py` and instantiate it, assigning it to the `strategy` variable.

Example of importing and using a custom strategy in `main.py`:
```python
# In main.py
# from strategies.my_strategy import MyStrategy # Import your strategy
...
# strategy = MyStrategy(params={'debug': args.debug}) # Instantiate your strategy
```

---

## Output
- **Trade Logs**: Saved in the `results/` directory as CSV files. The filename will be specific to the strategy used (e.g., `ema50scalper_trades.csv`, `mycustomstrategy_trades.csv`).
- **HTML Reports**: If the `-r` option is used, a comprehensive HTML report named `report.html` is saved in `results/`. This report includes performance metrics, equity curves, trade lists, and potentially strategy indicator configurations.

---

## Data Format
CSV files must have at least the following columns:
- `timestamp` (parseable datetime)
- `open`, `high`, `low`, `close`

---

## Troubleshooting
- Ensure your CSV files are correctly formatted and in the `data/` directory.
- If you encounter errors, check for missing columns or NaN values in your data.

---

## License
MIT
