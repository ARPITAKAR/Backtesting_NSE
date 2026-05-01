# ============================================================
#  IndicatorMetrics.py  –  Technical indicator computation
# ============================================================
import pandas as pd
import numpy as np
from utils.Constants import (
    SMA_FAST, SMA_SLOW, EMA_FAST, EMA_SLOW,
    MACD_SIGNAL, RSI_PERIOD, BB_PERIOD, BB_STD,
    RSI_OVERBOUGHT, RSI_OVERSOLD,
    COL_CLOSE, COL_HIGH, COL_LOW,
)


# ─────────────────────────────────────────────────────────────
class IndicatorValue:
    """Default sentinel values – mirrors your original design."""
    SMA         = -1.0
    SMA_BARBACK = 50
    MACD_LINE   = -1.0
    SIGNAL_LINE = -1.0


# ─────────────────────────────────────────────────────────────
class Crossover:
    """
    Detects bullish / bearish crossovers between two series.

    Parameters
    ----------
    fast : pd.Series
    slow : pd.Series
    """

    def __init__(self, fast: pd.Series, slow: pd.Series):
        self.fast = fast
        self.slow = slow

    def bullish(self) -> pd.Series:
        """Fast crosses above slow (previous bar fast < slow)."""
        return (self.fast > self.slow) & (self.fast.shift(1) <= self.slow.shift(1))

    def bearish(self) -> pd.Series:
        """Fast crosses below slow."""
        return (self.fast < self.slow) & (self.fast.shift(1) >= self.slow.shift(1))


# ─────────────────────────────────────────────────────────────
class Range:
    """
    Price range helpers.

    Parameters
    ----------
    df : pd.DataFrame  (must contain High, Low, Close columns)
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def true_range(self) -> pd.Series:
        high  = self.df[COL_HIGH]
        low   = self.df[COL_LOW]
        close = self.df[COL_CLOSE].shift(1)
        tr = pd.concat([high - low,
                         (high - close).abs(),
                         (low  - close).abs()], axis=1).max(axis=1)
        return tr

    def atr(self, period: int = 14) -> pd.Series:
        return self.true_range().rolling(period).mean()

    def daily_range_pct(self) -> pd.Series:
        """(High - Low) / Low * 100"""
        return (self.df[COL_HIGH] - self.df[COL_LOW]) / self.df[COL_LOW] * 100


# ─────────────────────────────────────────────────────────────
class TimeCheck:
    """
    Entry / exit timing guard.

    Parameters
    ----------
    min_bars_between : int   Minimum bars required between two entries.
    max_open_trades  : int   Maximum simultaneous open positions.
    """

    def __init__(self,
                 min_bars_between: int = 3,
                 max_open_trades: int  = 4):
        self._min          = min_bars_between
        self.IsAllowed     = True
        self.NextRound     = self._min
        self.NextEntrySignal = -1
        self.TotalOpenTradesAtATime = max_open_trades

    def register_entry(self, bar_index: int) -> None:
        """Call this every time a trade is entered."""
        self.NextEntrySignal = bar_index + self._min
        self.IsAllowed       = False

    def update(self, bar_index: int, open_trades: int) -> None:
        """Call every bar to refresh IsAllowed."""
        self.IsAllowed = (
            bar_index >= self.NextEntrySignal
            and open_trades <= self.TotalOpenTradesAtATime
        )


# ─────────────────────────────────────────────────────────────
class IndicatorMetrics:
    """
    Computes all indicators for a given OHLCV DataFrame and
    attaches them as new columns.

    Usage
    -----
    im = IndicatorMetrics(df)
    df = im.compute_all()
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    # ── public ────────────────────────────────────────────────
    def compute_all(self) -> pd.DataFrame:
        self._sma()
        self._ema()
        self._macd()
        self._rsi()
        self._bollinger_bands()
        return self.df

    # ── SMA ───────────────────────────────────────────────────
    def _sma(self) -> None:
        c = self.df[COL_CLOSE]
        self.df["SMA_fast"] = c.rolling(SMA_FAST).mean()
        self.df["SMA_slow"] = c.rolling(SMA_SLOW).mean()

    # ── EMA ───────────────────────────────────────────────────
    def _ema(self) -> None:
        c = self.df[COL_CLOSE]
        self.df["EMA_fast"] = c.ewm(span=EMA_FAST, adjust=False).mean()
        self.df["EMA_slow"] = c.ewm(span=EMA_SLOW, adjust=False).mean()

    # ── MACD ──────────────────────────────────────────────────
    def _macd(self) -> None:
        c = self.df[COL_CLOSE]
        ema_fast = c.ewm(span=EMA_FAST, adjust=False).mean()
        ema_slow = c.ewm(span=EMA_SLOW, adjust=False).mean()
        self.df["MACD_line"]   = ema_fast - ema_slow
        self.df["MACD_signal"] = (
            self.df["MACD_line"].ewm(span=MACD_SIGNAL, adjust=False).mean()
        )
        self.df["MACD_hist"]   = self.df["MACD_line"] - self.df["MACD_signal"]

    # ── RSI ───────────────────────────────────────────────────
    def _rsi(self) -> None:
        delta = self.df[COL_CLOSE].diff()
        gain  = delta.clip(lower=0)
        loss  = (-delta).clip(lower=0)
        avg_gain = gain.ewm(com=RSI_PERIOD - 1, adjust=False).mean()
        avg_loss = loss.ewm(com=RSI_PERIOD - 1, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        self.df["RSI"] = 100 - (100 / (1 + rs))
        self.df["RSI_overbought"] = RSI_OVERBOUGHT
        self.df["RSI_oversold"]   = RSI_OVERSOLD

    # ── Bollinger Bands ───────────────────────────────────────
    def _bollinger_bands(self) -> None:
        c   = self.df[COL_CLOSE]
        mid = c.rolling(BB_PERIOD).mean()
        std = c.rolling(BB_PERIOD).std()
        self.df["BB_upper"]  = mid + BB_STD * std
        self.df["BB_middle"] = mid
        self.df["BB_lower"]  = mid - BB_STD * std
        self.df["BB_width"]  = (self.df["BB_upper"] - self.df["BB_lower"]) / mid
