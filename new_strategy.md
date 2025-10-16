### **Strategy Class: `EmaBbandScalper`**

This strategy will be implemented in a new file named `ema_bband_scalper.py` within your `strategies` directory.

-----

### **1. Initialization (`__init__`)**

  * **Indicators:**
      * Initialize an **Exponential Moving Average (EMA)** with a period of **12**.
      * Initialize an **EMA** with a period of **26**.
      * Initialize **Bollinger Bands (BBands)** with a period of **20** and a standard deviation of **2**.
  * **State Variables:**
      * Create boolean flags to track the state of the EMA crossover:
          * `self.ema_crossed_above = False`
          * `self.ema_crossed_below = False`

-----

### **2. Per-Candle Logic (`next`)**

For each incoming data point (candle), the following logic should be executed in order:

#### **a. Consolidation Check**

  * **Condition:** Before checking for any trade signals, determine if the market is consolidating.
  * **Rule:** Calculate the percentage difference between the **EMA 12** and **EMA 26** values. If this difference is less than a small threshold (e.g., **0.1%**), it indicates that the EMAs are very close together (i.e., the market is consolidating).
  * **Action:** If the market is consolidating, **ignore all buy and sell signals** for the current candle and proceed to the next one.

#### **b. EMA Crossover Detection**

  * **Bullish Crossover:**
      * **Condition:** Check if the **EMA 12** has crossed *above* the **EMA 26** on the *previous* candle.
      * **Action:** If a bullish crossover is detected, set `self.ema_crossed_above = True` and `self.ema_crossed_below = False`.
  * **Bearish Crossover:**
      * **Condition:** Check if the **EMA 12** has crossed *below* the **EMA 26** on the *previous* candle.
      * **Action:** If a bearish crossover is detected, set `self.ema_crossed_below = True` and `self.ema_crossed_above = False`.

#### **c. Buy Signal**

A buy signal is generated if **all** of the following conditions are met:

1.  **Bullish Crossover State:** The `self.ema_crossed_above` flag must be `True`.
2.  **Price Pullback:** The **low** of the current candle must be *less than or equal to* the **middle Bollinger Band**.
3.  **Confirmation Candle:** The current candle must be **bullish** (i.e., `close > open`).

<!-- end list -->

  * **Action:** If a buy signal is generated, execute a **buy** order.
  * **Stop-Loss:** Place the stop-loss at the **most recent swing low**.
  * **Take-Profit:** Set the take-profit target at the **upper Bollinger Band**.
  * **Reset State:** After placing the trade, reset `self.ema_crossed_above = False` to avoid multiple trades on the same signal.

#### **d. Sell Signal**

A sell signal is generated if **all** of the following conditions are met:

1.  **Bearish Crossover State:** The `self.ema_crossed_below` flag must be `True`.
2.  **Price Pullback:** The **high** of the current candle must be *greater than or equal to* the **middle Bollinger Band**.
3.  **Confirmation Candle:** The current candle must be **bearish** (i.e., `close < open`).

<!-- end list -->

  * **Action:** If a sell signal is generated, execute a **sell** order.
  * **Stop-Loss:** Place the stop-loss at the **most recent swing high**.
  * **Take-Profit:** Set the take-profit target at the **lower Bollinger Band**.
  * **Reset State:** After placing the trade, reset `self.ema_crossed_below = False`.

