# Trading Backtester v1

A modular backtesting framework for algorithmic trading strategies on historical market data. Supports running, analyzing, and reporting on multiple strategies with flexible CLI options.

---

## Features
- Run backtests on historical CSV data
- Modular strategy interface (add your own strategies easily)
- Performance metrics (Sharpe, drawdown, profit factor, etc.)
- Interactive plots and HTML reporting (Plotly, Matplotlib)

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

All arguments are optional. If no file is provided, you will be prompted to select a CSV from the `data/` directory.

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

## Web App (Streamlit)
Run an interactive web UI to select strategies, tweak parameters, pick CSVs, and view plots/metrics.

1) Install dependencies:

```powershell
pip install -r requirements.txt
```

2) Launch the app:

```powershell
streamlit run app.py
```

3) In the browser, choose a CSV from data/ or upload, select strategy and params, and click Run Backtest.

---

## Adding New Strategies
- Add your strategy as a new Python file in the `strategies/` directory.
- Inherit from `StrategyBase` and implement `generate_signals(self, data)`.
- Register/import your strategy in `main.py` or your own runner script.

---

## Output
- Trade logs are saved in `results/` as CSV files.
- HTML reports (if `-r` is used) are saved in `results/report.html`.

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
