# ============================================================
#  RiskManagement.py  –  Stop-loss, trailing stop, position
# ============================================================
from utils.Constants import (
    TRAILING_STOP_PCT, MAX_OPEN_TRADES, INITIAL_CAPITAL, LOT_SIZE
)


# ─────────────────────────────────────────────────────────────
class RiskManagement:
    """
    Base risk checks applied before each new entry.

    Parameters
    ----------
    capital          : float   Available capital.
    max_open_trades  : int     Max simultaneous positions.
    risk_pct_per_trade: float  Max % of capital to risk per trade.
    """

    def __init__(self,
                 capital: float            = INITIAL_CAPITAL,
                 max_open_trades: int      = MAX_OPEN_TRADES,
                 risk_pct_per_trade: float = 0.02):
        self.capital             = capital
        self.max_open_trades     = max_open_trades
        self.risk_pct_per_trade  = risk_pct_per_trade
        self.IsAllowed           = True

    def can_enter(self, open_trades: int, entry_price: float,
                  stop_price: float) -> bool:
        """Return True if entering a trade is allowed."""
        if open_trades >= self.max_open_trades:
            self.IsAllowed = False
            return False

        risk_amount  = self.capital * self.risk_pct_per_trade
        price_risk   = abs(entry_price - stop_price)
        if price_risk == 0:
            self.IsAllowed = False
            return False

        max_qty = int(risk_amount / price_risk)
        self.IsAllowed = max_qty > 0
        return self.IsAllowed

    def position_size(self, entry_price: float,
                      stop_price: float) -> int:
        """Calculate quantity based on risk %."""
        risk_amount = self.capital * self.risk_pct_per_trade
        price_risk  = abs(entry_price - stop_price)
        if price_risk == 0:
            return LOT_SIZE
        qty = int(risk_amount / price_risk)
        return max(qty, LOT_SIZE)


# ─────────────────────────────────────────────────────────────
class TrailingStopLoss:
    """
    Manages a per-trade trailing stop.

    Usage
    -----
    tsl = TrailingStopLoss(entry_price=1500, direction="BUY")
    tsl.update(current_price=1540)
    if tsl.is_triggered(current_price): exit_trade()
    """

    def __init__(self,
                 entry_price: float,
                 direction: str     = "BUY",   # "BUY" or "SELL"
                 threshold: float   = TRAILING_STOP_PCT,
                 trail_by_bars: int = 2):
        self.IsAllowed   = True
        self.Threshold   = threshold
        self.TrailBy     = trail_by_bars
        self.Next        = 1
        self._direction  = direction.upper()
        self._entry      = entry_price
        self._best       = entry_price
        self._stop       = self._calc_initial_stop(entry_price)

    # ── public ────────────────────────────────────────────────
    def update(self, current_price: float) -> None:
        """Call once per bar to ratchet the stop."""
        if self._direction == "BUY":
            if current_price > self._best:
                self._best = current_price
                self._stop = self._best * (1 - self.Threshold)
        else:
            if current_price < self._best:
                self._best = current_price
                self._stop = self._best * (1 + self.Threshold)

    def is_triggered(self, current_price: float) -> bool:
        if self._direction == "BUY":
            return current_price <= self._stop
        return current_price >= self._stop

    @property
    def stop_price(self) -> float:
        return round(self._stop, 2)

    # ── private ───────────────────────────────────────────────
    def _calc_initial_stop(self, price: float) -> float:
        if self._direction == "BUY":
            return price * (1 - self.Threshold)
        return price * (1 + self.Threshold)


# ─────────────────────────────────────────────────────────────
class TradingSymbol:
    """
    Configuration for a single trading instrument.

    Parameters
    ----------
    asset            : str    Ticker / symbol name (e.g. "RELIANCE")
    quantity         : int    Fixed lot size to trade
    noise_price_below: float  Ignore signals when price < this level
    """

    def __init__(self,
                 asset: str             = "RELIANCE",
                 quantity: int          = 1,
                 noise_price_below: float = 1100.0):
        self.Asset            = asset
        self.Quantity         = quantity
        self.NoisePriceBelow  = noise_price_below

    def is_valid_price(self, price: float) -> bool:
        return price >= self.NoisePriceBelow

    def __repr__(self) -> str:
        return (f"TradingSymbol(asset={self.Asset}, "
                f"qty={self.Quantity}, "
                f"noise_below={self.NoisePriceBelow})")
