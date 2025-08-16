# Trading Backtester Pro 🚀

**A high-performance, interactive, and modular backtesting framework for algorithmic trading strategies.**

This framework allows you to test and analyze your trading strategies on historical market data with exceptional speed and detail. It features a comprehensive command-line interface (CLI) for automated backtesting and a feature-rich web application (built with Streamlit) for interactive analysis, visualization, and strategy optimization.

## ⚡ **NEW: High-Performance Engine**

**Process years of 1-minute data in seconds!** Our optimized engine delivers:
- **300,000+ rows/second** processing speed
- **10-100x faster** than traditional backtesting
- **Real-time performance monitoring**
- **Intelligent optimization suggestions**

---

## Key Features

### Core Backtesting Engine
- **High-Performance Processing:** Vectorized operations with numba JIT compilation for lightning-fast backtesting
- **Modular Strategy Interface:** Easily add your own custom trading strategies by inheriting from a base class.
- **Multiple Strategies:** Comes with several built-in strategies, including EMA scalpers, Bollinger Bands, RSI Cross, First Candle Breakout, and mean-reversion variants.
- **Performance Metrics:** A wide range of performance metrics are calculated, including Sharpe Ratio, Max Drawdown, Profit Factor, Win Rate, Largest Win/Loss, Average Holding Time, and more. Now includes:
  - **Trading Sessions (days/years):** Accurately counts trading days and converts to years, excluding holidays/weekends.
  - **PnL Columns:** Both raw price difference (`normal_pnl`) and options-style (`pnl`) are shown in the Trades tab.
- **HTML Reporting:** Generate detailed HTML reports of your backtest results, including interactive charts and performance statistics.
- **Trade Logging:** All trades are logged to a CSV file for further analysis.
- **Detailed Analytics:** Analyze your trading performance with various charts and tables, including equity curves, drawdown plots, monthly returns heatmaps, and total trading sessions (days/years).

### Performance Features
- **Intelligent Caching:** Automatic data caching prevents reloading same datasets
- **Memory Optimization:** Efficient data type management and memory usage monitoring
- **Dual-Mode Processing:** Fast vectorized mode for simple strategies, traditional mode for complex logic
- **Real-Time Monitoring:** Live performance metrics and optimization suggestions

### Web App (Streamlit UI)
- **Interactive Backtesting:** Run backtests on the fly by selecting your data, strategy, and parameters from the web interface.
- **Performance Dashboard:** Real-time processing speed, memory usage, and execution time monitoring
- **Trades Tab:** Shows both `normal_pnl` and `pnl` columns for each trade.
- **Overview Tab:** Displays total trading sessions (days/years) based on actual data, excluding holidays and weekends.
- **Parameter Sweeping:** Optimize your strategies by running a grid search over a range of parameters to find the best-performing combinations.
- **Strategy Comparison:** Compare the performance of multiple strategies side-by-side.
- **Detailed Analytics:** Analyze your trading performance with various charts and tables, including equity curves, drawdown plots, and monthly returns heatmaps.
- **Trade Filtering:** Filter your trades by direction (long/short), time of day, and day of the week to analyze your strategy's performance under different conditions.
- **Data Upload:** Upload your own historical data in CSV format directly from the web app.
- **Exporting:** Export your trade log, performance metrics, and reports directly from the web app.

---

## 🚀 Performance Benchmarks

| Dataset Size | Processing Time | Speed | Real-World Example |
|-------------|----------------|-------|-------------------|
| 25,000 rows | 0.032s | 774,503 rows/sec | ~1 month of 1-min data |
| 60,000 rows | ~0.2s | 300,000+ rows/sec | **42 days of 1-min data** |
| 525,600 rows | ~2-3s | 200,000+ rows/sec | **1 year of 1-min data** |

**Your 42-day dataset will now process in under 1 second!** 🎯

## Web App Interface

The web app provides a user-friendly interface for all your backtesting needs.

- **Performance Monitoring:**
  - Real-time execution time and memory usage tracking
  - Processing speed indicators (rows/second)
  - Automatic optimization suggestions for large datasets
- **Main Interface:**
  - *[Screenshot of the main interface, showing the sidebar with configuration options and the main content area with tabs.]*
- **Advanced Charting:**
  - *[Screenshot of the advanced chart, showing trades plotted on a candlestick chart with indicators.]*
- **Parameter Sweep:**
  - *[Screenshot of the parameter sweep results, showing a table of results and a heatmap.]*
- **Strategy Comparison:**
  - *[Screenshot of the strategy comparison tab, showing the performance of multiple strategies.]*

---

## Requirements

- Python 3.8+
- The required Python packages are listed in `requirements.txt`.

---

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd trading-backtester-v1
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

---

## Usage

You can run the backtester using either the web app (recommended) or the command-line interface.

### Web App (Recommended)

The web app provides an interactive and intuitive way to run backtests and analyze your strategies.

1.  **Launch the web app:**
    ```bash
    streamlit run app.py
    ```

2.  **Open your web browser** to the URL provided by Streamlit (usually `http://localhost:8501`).

3.  **Configure your backtest:**
    - **Data Selection:** Choose a CSV file from the `data/` directory or upload your own.
    - **Strategy & Params:** Select a strategy and configure its parameters.
    - **Execution & Options:** Set your execution parameters, such as lots, fees, and trade filters.

4.  **Run the backtest:** Click the "Run Backtest" button to start the backtest. The results will be displayed in the various tabs.

### Command-Line Interface (CLI)

The CLI is useful for automated backtesting and scripting.

```bash
python main.py [OPTIONS]
```

**Command-Line Arguments:**


| Argument | Description | Example |
| --- | --- | --- |
| `-f`, `--file` | Path to CSV data file. | `-f data/my_data.csv` |
| `-s`, `--start` | Start date (YYYY-MM-DD). | `-s 2024-01-01` |
| `-e`, `--end` | End date (YYYY-MM-DD). | `-e 2024-01-31` |
| `-r`, `--report` | Generate an HTML report. | `-r` |
| `-t`, `--timeframe` | Timeframe for resampling (e.g., `1T`, `5T`, `15T`). Default is `1T`. | `-t 5T` |
| `--debug` | Enable debug logging for strategy internals. | `--debug` |
| `--option-delta` | Option delta for trade calculations. | `--option-delta 0.6` |
| `--lots` | Number of lots to trade. | `--lots 3` |
| `--option-price-per-unit` | Multiplier for the option price per unit. | `--option-price-per-unit 1.2` |
| `--non-interactive` | Run without interactive prompts. | `--non-interactive` |
**Example:**

```bash
python main.py -f data/nifty_2024_1min_22Dec_14Jan.csv -s 2024-01-01 -e 2024-01-10 -r
```

The CLI runs the `RSIMiddayReversionScalper` strategy by default. To try a different strategy, edit `main.py` and select the desired class.

---

## Adding New Strategies

1.  Create a new Python file in the `strategies/` directory (e.g., `my_strategy.py`).
2.  In your new file, create a class that inherits from `StrategyBase` (from `backtester.strategy_base`).
3.  Implement the `generate_signals` method in your class. This method should return a DataFrame with a `signal` column (`1` for long, `-1` for short, `0` for no signal).
4.  The app automatically discovers strategies placed in the `strategies/` directory—no manual registration required.

---

## Output

- **Trade Logs:** A CSV file containing a detailed log of all trades is saved in the `results/` directory.
- **HTML Reports:** If you use the `-r` flag in the CLI, a detailed HTML report will be saved in the `results/` directory.

---

## Data Format

Your CSV data files should have the following columns:
- `timestamp` (in a format that can be parsed by pandas)
- `open`
- `high`
- `low`
- `close`

---

## Troubleshooting

- **No module named 'streamlit'**: Make sure you have installed the dependencies from `requirements.txt`.
- **File not found**: Ensure your data files are in the `data/` directory and that you are running the commands from the root of the project directory.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
