# ============================================================
#  BackTest.py  –  Core back-testing engine
# ============================================================
import pandas as pd
from data.DataLoader import DataLoader
from indicators.IndicatorMetrics import IndicatorMetrics, TimeCheck
from risk.RiskManagement import RiskManagement, TrailingStopLoss, TradingSymbol
from analytics.FinancialData import FinancialData
from strategy.StrategyLogic import BaseStrategy, get_strategy
from utils.Display import print_info, print_warn, print_trade_summary
from utils.Constants import INITIAL_CAPITAL, MAX_OPEN_TRADES, MIN_BARS_BETWEEN


class BackTest:
    """
    Main back-testing engine.

    Parameters
    ----------
    symbol    : TradingSymbol   Asset config (name, qty, noise floor)
    strategy  : BaseStrategy    Signal generator (or str key from registry)
    csv_path  : str             Path to OHLCV CSV file
    capital   : float           Starting capital

    Usage
    -----
    bt = BackTest("RELIANCE")           # uses SMA crossover by default
    bt = BackTest("RELIANCE", strategy="macd", csv_path="data/REL.csv")
    result = bt.run()
    bt.PrintToCsv("REPORT_TF_1_")
    """

    def __init__(self,
                 asset_name : str                = "ULTRACEMCO",
                 strategy                        = "sma",
                 csv_path   : str                = "",
                 capital    : float              = INITIAL_CAPITAL,
                 quantity   : int                = 1,
                 noise_below: float              = 0.0):

        self.symbol   = TradingSymbol(asset_name, quantity, noise_below)
        self.strategy = (get_strategy(strategy)
                         if isinstance(strategy, str) else strategy)
        self.csv_path = csv_path or f"C:/Users/Arpit/Desktop/Backtesting/data/{asset_name}.csv"
        self.capital  = capital

        self._fd      : FinancialData | None = None
        self._result  : dict                 = {}

    # ── public API ────────────────────────────────────────────
    def run(self) -> dict:
        print_info(f"BackTest starting  |  {self.symbol}  |  {self.strategy}")

        df = self._load_and_prepare()
        self._fd = FinancialData(self.symbol.Asset, self.capital)

        rm = RiskManagement(self.capital, MAX_OPEN_TRADES)
        tc = TimeCheck(MIN_BARS_BETWEEN, MAX_OPEN_TRADES)

        open_positions: list[dict] = []     # list of {trade, tsl}

        for i, (idx, row) in enumerate(df.iterrows()):
            close = row["Close"]
            tc.update(i, len(open_positions))

            # ── update trailing stops & check exits ──────────
            still_open = []
            for pos in open_positions:
                tsl: TrailingStopLoss = pos["tsl"]
                tsl.update(close)

                exit_triggered = False
                exit_reason    = ""

                if tsl.is_triggered(close):
                    exit_triggered = True
                    exit_reason    = "TRAILING_STOP"
                elif row["signal"] == -1 and pos["trade"].direction == "BUY":
                    exit_triggered = True
                    exit_reason    = "SIGNAL"
                elif row["signal"] == 1 and pos["trade"].direction == "SELL":
                    exit_triggered = True
                    exit_reason    = "SIGNAL"

                if exit_triggered:
                    self._fd.close_trade(pos["trade"], idx, close, exit_reason)
                else:
                    still_open.append(pos)

            open_positions = still_open

            # ── check entry ──────────────────────────────────
            if not tc.IsAllowed:
                continue
            if not self.symbol.is_valid_price(close):
                continue

            direction = None
            if row["signal"] == 1:
                direction = "BUY"
            elif row["signal"] == -1:
                direction = "SELL"

            if direction:
                qty = self.symbol.Quantity
                if not rm.can_enter(len(open_positions), close,
                                    close * 0.98):
                    print_warn(f"[{idx}] Entry blocked by RiskManagement")
                    continue

                trade = self._fd.open_trade(direction, idx, close, qty)
                tsl   = TrailingStopLoss(close, direction)
                open_positions.append({"trade": trade, "tsl": tsl})
                tc.register_entry(i)

        # ── close any remaining open positions at last bar ────
        if len(df) > 0:
            last_idx   = df.index[-1]
            last_close = df.iloc[-1]["Close"]
            for pos in open_positions:
                self._fd.close_trade(pos["trade"], last_idx,
                                     last_close, "EOD")

        self._result = self._fd.compute_metrics()
        print_trade_summary(self._result)
        return self._result

    def PrintToCsv(self, prefix: str = "REPORT_") -> str:
        if self._fd is None:
            print_warn("Run the backtest first with .run()")
            return ""
        return self._fd.save_to_csv(prefix)

    def get_trade_log(self) -> pd.DataFrame:
        if self._fd is None:
            return pd.DataFrame()
        return self._fd.to_dataframe()

    # ── private ───────────────────────────────────────────────
    # 1: private method
    def _load_and_prepare(self) -> pd.DataFrame:
        # 2: load data
        loader = DataLoader(self.csv_path)
        df     = loader.load()
        # 3: add indicators
        df     = IndicatorMetrics(df).compute_all()
        # 4: generate trading signals
        df     = self.strategy.generate_signals(df)
        # 5: drop rows without signals
        df     = df.dropna(subset=["signal"])
        # 6: return final dataframe
        return df
