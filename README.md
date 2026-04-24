# BackTesting Framework

A modular Python backtesting engine for Indian equities using local OHLCV CSV data.

## Project Structure

```
BackTesting/
├── main.py                    ← Entry point – configure & run here
├── BackTest.py                ← Core engine loop
│
├── data/
│   ├── DataLoader.py          ← CSV loader & validator
│   └── RELIANCE.csv           ← Sample data (replace with your own)
│
├── indicators/
│   └── IndicatorMetrics.py    ← SMA, EMA, MACD, RSI, Bollinger Bands
│
├── risk/
│   └── RiskManagement.py      ← Position sizing, trailing stop, symbol config
│
├── strategy/
│   └── StrategyLogic.py       ← 5 built-in strategies + base class to extend
│
├── analytics/
│   └── FinancialData.py       ← Trade book, PnL, metrics, CSV export
│
├── utils/
│   ├── Constants.py           ← All tunable parameters in one place
│   └── Display.py             ← Console pretty-printer
│
└── output/                    ← Auto-created; CSV reports saved here
```

## Quick Start

### 1. Install dependencies
```bash
pip install pandas numpy
```

### 2. Add your CSV
Place your OHLCV file in `data/` — columns must include:
`Date, Open, High, Low, Close, Volume`

### 3. Run
```bash
cd BackTesting
python main.py
```

## Configuration (`utils/Constants.py`)

| Parameter | Default | Description |
|---|---|---|
| `INITIAL_CAPITAL` | 100,000 | Starting capital ₹ |
| `BROKERAGE_PER_TRADE` | 20 | Flat fee per order |
| `SMA_FAST / SMA_SLOW` | 20 / 50 | SMA crossover periods |
| `RSI_PERIOD` | 14 | RSI lookback |
| `TRAILING_STOP_PCT` | 0.02 | 2% trailing stop |
| `MAX_OPEN_TRADES` | 4 | Max simultaneous positions |

## Available Strategies

| Key | Strategy |
|---|---|
| `"sma"` | SMA Fast/Slow Crossover |
| `"ema"` | EMA Fast/Slow Crossover |
| `"macd"` | MACD Line/Signal Crossover |
| `"rsi"` | RSI Overbought/Oversold Reversal |
| `"bollinger"` | Bollinger Band Mean Reversion |

## Creating a Custom Strategy

```python
# strategy/StrategyLogic.py  (add your own class)
class MyStrategy(BaseStrategy):
    name = "My Custom Strategy"

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["signal"] = 0
        # +1 = BUY,  -1 = SELL,  0 = no action
        df.loc[df["RSI"] < 25, "signal"] = 1
        df.loc[df["RSI"] > 75, "signal"] = -1
        return df
```

Then run it:
```python
from strategy.StrategyLogic import MyStrategy
bt = BackTest("RELIANCE", strategy=MyStrategy())
bt.run()
```

## Output

Console:
```
=======================================================
  BACKTEST RESULTS
=======================================================
  Trade Statistics
  -------------------------------------------------------
  Total Winning Trades            : 347
  Total Loss Trades               : 465
  ...
```

CSV report saved to `output/REPORT_TF_1_RELIANCE_<timestamp>.csv`
Each row = one trade with entry/exit date, price, PnL, brokerage, net PnL.
