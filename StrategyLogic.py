# ============================================================
#  StrategyLogic.py  –  Strategy base class + built-in strategies
# ============================================================
import pandas as pd
from abc import ABC, abstractmethod
from indicators.IndicatorMetrics import Crossover


# ─────────────────────────────────────────────────────────────
class BaseStrategy(ABC):
    """
    Inherit from this class to create a custom strategy.

    Required overrides
    ------------------
    generate_signals(df) -> pd.DataFrame
        Must add a 'signal' column with values:
            +1  →  BUY
            -1  →  SELL / SHORT
             0  →  No action
    """

    name: str = "BaseStrategy"

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        ...

    def __repr__(self) -> str:
        return f"<Strategy: {self.name}>"


# ─────────────────────────────────────────────────────────────
class SMACrossoverStrategy(BaseStrategy):
    """
    Classic SMA fast / slow crossover.

    BUY  when SMA_fast crosses above SMA_slow
    SELL when SMA_fast crosses below SMA_slow
    """

    name = "SMA Crossover"

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        xo = Crossover(df["SMA_fast"], df["SMA_slow"])
        df["signal"] = 0
        df.loc[xo.bullish(), "signal"] = 1
        df.loc[xo.bearish(), "signal"] = -1
        return df


# ─────────────────────────────────────────────────────────────
class EMACrossoverStrategy(BaseStrategy):
    """EMA_fast / EMA_slow crossover."""

    name = "EMA Crossover"

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        xo = Crossover(df["EMA_fast"], df["EMA_slow"])
        df["signal"] = 0
        df.loc[xo.bullish(), "signal"] = 1
        df.loc[xo.bearish(), "signal"] = -1
        return df


# ─────────────────────────────────────────────────────────────
class MACDStrategy(BaseStrategy):
    """
    MACD line crosses above / below Signal line.

    BUY  when MACD_line crosses above MACD_signal
    SELL when MACD_line crosses below MACD_signal
    """

    name = "MACD Crossover"

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        xo = Crossover(df["MACD_line"], df["MACD_signal"])
        df["signal"] = 0
        df.loc[xo.bullish(), "signal"] = 1
        df.loc[xo.bearish(), "signal"] = -1
        return df


# ─────────────────────────────────────────────────────────────
class RSIStrategy(BaseStrategy):
    """
    RSI mean-reversion.

    BUY  when RSI crosses above oversold level (default 30)
    SELL when RSI crosses below overbought level (default 70)
    """

    name = "RSI Reversal"

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        rsi  = df["RSI"]
        ob   = df["RSI_overbought"]
        os_  = df["RSI_oversold"]

        df["signal"] = 0
        # Crossed above oversold → BUY
        buy_cond  = (rsi > os_)  & (rsi.shift(1) <= os_.shift(1))
        # Crossed below overbought → SELL
        sell_cond = (rsi < ob)   & (rsi.shift(1) >= ob.shift(1))
        df.loc[buy_cond,  "signal"] = 1
        df.loc[sell_cond, "signal"] = -1
        return df


# ─────────────────────────────────────────────────────────────
class BollingerBandStrategy(BaseStrategy):
    """
    Bollinger Band breakout / reversal.

    BUY  when Close crosses above lower band (mean-reversion entry)
    SELL when Close crosses below upper band
    """

    name = "Bollinger Band"

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        close = df["Close"]
        lower = df["BB_lower"]
        upper = df["BB_upper"]

        df["signal"] = 0
        buy_cond  = (close > lower) & (close.shift(1) <= lower.shift(1))
        sell_cond = (close < upper) & (close.shift(1) >= upper.shift(1))
        df.loc[buy_cond,  "signal"] = 1
        df.loc[sell_cond, "signal"] = -1
        return df


# ─────────────────────────────────────────────────────────────
# Registry – add new strategies here for easy lookup
STRATEGY_REGISTRY: dict[str, type[BaseStrategy]] = {
    "sma"       : SMACrossoverStrategy,
    "ema"       : EMACrossoverStrategy,
    "macd"      : MACDStrategy,
    "rsi"       : RSIStrategy,
    "bollinger" : BollingerBandStrategy,
}


def get_strategy(name: str) -> BaseStrategy:
    key = name.lower().strip()
    if key not in STRATEGY_REGISTRY:
        raise ValueError(
            f"Unknown strategy '{name}'. "
            f"Available: {list(STRATEGY_REGISTRY.keys())}"
        )
    return STRATEGY_REGISTRY[key]()
