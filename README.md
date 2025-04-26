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

All arguments are optional. If no file is provided, you will be prompted to select a CSV from the `data/` directory.

#### Example: Full Run

```bash
python main.py -f data/nifty_2024_1min_22Dec_14Jan.csv -s 2024-01-01 -e 2024-01-10 -r
```

---

## Interactive Commands (After Backtest)
After running a backtest, you can enter the following commands at the prompt:

- `t` : Show trades plotted on candlestick chart (Plotly)
- `e` : Show equity curve plot
- `q` : Quit the program

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
