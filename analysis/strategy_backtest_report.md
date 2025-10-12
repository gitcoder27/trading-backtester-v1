# Strategy Backtest Report (NIFTY 2024)

## Methodology
- Ran `python cli.py` for each of the 25 strategy classes in `strategies/`, pointing to `data/market_data/nifty_2024_1min_01Jan_31Dec.csv`.
- Used the default engine configuration from the CLI with position sizing set to `--lots 6`; no daily target flag was supplied per instructions.
- Each run emitted JSON metrics (`analysis/results/*.json`) that were aggregated into `analysis/summary.json` for comparison.

## Best Performing Strategies
- **AwesomeScalperStrategy** delivered the highest total return (323.44%) and Sharpe ratio (2.51) with a manageable 35.05% max drawdown, making it the top performer on both absolute and risk-adjusted bases.
- **MeanReversionScalper** followed closely with a 314.19% total return and a Sharpe of 1.98, albeit with a slightly higher drawdown (43.45%).
- **BBandsScalperStrategy** provided a balanced profile (145.09% return, 1.92 Sharpe, 29.26% drawdown) and is a solid lower-volatility alternative.

## Detailed Metrics (sorted by total return %)
| Strategy                                         | Final Equity | Total Return % | Sharpe | Max DD % | Win Rate % | Profit Factor | Trades |
| ------------------------------------------------ | ------------ | -------------- | ------ | -------- | ---------- | ------------- | ------ |
| AwesomeScalperStrategy                           | 423440.64    | 323.44         | 2.51   | 35.05    | 64.85      | 1.36          | 478    |
| MeanReversionScalper                             | 414188.89    | 314.19         | 1.98   | 43.45    | 58.10      | 1.13          | 1093   |
| EMA10ScalperStrategyV3                           | 290912.47    | 190.91         | 1.49   | 72.41    | 31.16      | 1.11          | 1380   |
| RSIMiddayReversionScalper                        | 263855.05    | 163.86         | 0.29   | 104.31   | 73.66      | 1.14          | 467    |
| OpeningRangeBreakoutScalper                      | 248296.64    | 148.30         | 1.55   | 86.74    | 37.67      | 1.08          | 653    |
| BBandsScalperStrategy                            | 245092.35    | 145.09         | 1.92   | 29.26    | 51.42      | 1.15          | 1480   |
| EMA10ScalperStrategyV2                           | 221143.37    | 121.14         | 1.32   | 83.48    | 29.13      | 1.04          | 3302   |
| EMA10ScalperStrategyV4                           | 195799.02    | 95.80          | 1.22   | 52.61    | 30.16      | 1.10          | 998    |
| MeanReversionConfirmedScalperDailyTargetStrategy | 168220.17    | 68.22          | 1.31   | 33.68    | 65.97      | 1.11          | 814    |
| AdaptiveTrendPullbackScalperStrategy             | 150954.53    | 50.95          | 1.44   | 19.21    | 61.49      | 1.29          | 148    |
| EMA10ScalperStrategyV1                           | 122349.80    | 22.35          | 0.72   | 56.83    | 29.88      | 1.02          | 937    |
| EMA10ScalperStrategyV5                           | 122349.80    | 22.35          | 0.72   | 56.83    | 29.88      | 1.02          | 937    |
| HighWinScalperStrategy                           | 105284.36    | 5.28           | 0.34   | 23.61    | 50.41      | 1.03          | 246    |
| TrendRecoveryScalperStrategy                     | 97370.66     | -2.63          | -1.39  | 2.63     | 0.00       | 0.00          | 2      |
| EMA10ScalperStrategyV6                           | 74540.05     | -25.46         | -2.13  | 307.62   | 29.00      | 0.99          | 4065   |
| EMARsiSwingStrategy                              | 65243.56     | -34.76         | -0.27  | 49.40    | 35.97      | 0.87          | 139    |
| EMA50_100StochasticStrategy                      | -11286.88    | -111.29        | 0.62   | 122.93   | 34.02      | 0.83          | 435    |
| HeikenAshiDualSupertrendRSIStrategy              | -19289.30    | -119.29        | 0.17   | 181.10   | 34.40      | 0.95          | 1090   |
| EMA50ScalperStrategy                             | -22788.58    | -122.79        | 0.42   | 156.33   | 27.07      | 0.94          | 1548   |
| RSICrossStrategy                                 | -28888.27    | -128.89        | 0.79   | 134.67   | 57.79      | 0.91          | 552    |
| EMACrossoverDailyTargetStrategy                  | -32041.91    | -132.04        | 0.71   | 142.74   | 39.06      | 0.94          | 1572   |
| IntradayEmaTradeStrategy                         | -58922.49    | -158.92        | 0.74   | 204.44   | 38.93      | 0.89          | 655    |
| EMAPullbackScalperDailyTargetStrategy            | -86713.46    | -186.71        | -0.58  | 230.25   | 41.78      | 0.92          | 1417   |
| EMA44ScalperStrategy                             | -684391.77   | -784.39        | -0.65  | 589.97   | 20.26      | 0.84          | 3757   |
| FirstCandleBreakoutStrategy                      | -736707.74   | -836.71        | 1.16   | 797.74   | 79.10      | 0.52          | 244    |

## Observations
- Strategies with built-in scalping logic (AwesomeScalperStrategy, MeanReversionScalper) significantly outperformed crossover-based systems under the 6-lot configuration.
- High trade-frequency variants (e.g., EMA10ScalperStrategyV2/V3) produced strong nominal returns but at the cost of very deep drawdowns (>70%), which may be unsuitable without tighter risk controls.
- Multiple daily-target strategies underperformed or went deeply negative, indicating their risk caps may rely on the daily target parameter that was intentionally disabled for this evaluation.
- TrendRecoveryScalperStrategy triggered CLI validation warnings (missing the `next` hook) and traded only twice, suggesting the implementation needs review before production use.

## Recommendation
Focus on **AwesomeScalperStrategy** as the primary candidate given its superior return-to-risk profile. If a lower drawdown is preferred, consider **BBandsScalperStrategy** as an alternative with materially lower volatility while retaining triple-digit returns.
