# ============================================================
#  FinancialData.py  –  Trade record + analytics engine
# ============================================================
import os
import csv
import pandas as pd
from dataclasses import dataclass, field, asdict
from datetime import datetime
from utils.Constants import  OUTPUT_DIR
from utils.Display import print_info


# ─────────────────────────────────────────────────────────────
@dataclass
class Trade:
    trade_id    : int
    asset       : str
    direction   : str        # "BUY" or "SELL"
    entry_date  : str
    entry_price : float
    quantity    : int
    exit_date   : str  = ""
    exit_price  : float = 0.0
    pnl         : float = 0.0
    brokerage   : float = 0.0
    net_pnl     : float = 0.0
    status      : str   = "OPEN"   # "OPEN" | "CLOSED"
    exit_reason : str   = ""       # "SIGNAL" | "TRAILING_STOP" | "EOD"


# ─────────────────────────────────────────────────────────────
class FinancialData:
    """
    Maintains the live trade book and computes all analytics.

    Usage
    -----
    fd = FinancialData(asset="RELIANCE", initial_capital=100_000)
    fd.open_trade(...)
    fd.close_trade(...)
    result = fd.compute_metrics()
    fd.save_to_csv("REPORT_TF_1_")
    """

    def __init__(self, asset: str = "RELIANCE",
                 initial_capital: float = 100_000.0):
        self.asset           = asset
        self.initial_capital = initial_capital
        self._trades: list[Trade] = []
        self._trade_counter  = 0

    # ── trade management ──────────────────────────────────────
    def open_trade(self, direction: str, entry_date,
                   entry_price: float, quantity: int) -> Trade:
        self._trade_counter += 1
        t = Trade(
            trade_id    = self._trade_counter,
            asset       = self.asset,
            direction   = direction.upper(),
            entry_date  = str(entry_date),
            entry_price = entry_price,
            quantity    = quantity,
            brokerage   = 0.0,
        )
        self._trades.append(t)
        return t

    def close_trade(self, trade: Trade, exit_date,
                    exit_price: float, reason: str = "SIGNAL") -> None:
        trade.exit_date   = str(exit_date)
        trade.exit_price  = exit_price
        trade.exit_reason = reason
        BROKERAGE_PER_TRADE= self._calculate_charges(
            trade.entry_price,
            exit_price,
            trade.quantity
        )
        trade.brokerage  = BROKERAGE_PER_TRADE   # exit leg

        if trade.direction == "BUY":
            trade.pnl = (exit_price - trade.entry_price) * trade.quantity
        else:
            trade.pnl = (trade.entry_price - exit_price) * trade.quantity

        trade.net_pnl = trade.pnl - trade.brokerage
        trade.status  = "CLOSED"

    # ── analytics ─────────────────────────────────────────────
    def compute_metrics(self) -> dict:
        closed = [t for t in self._trades if t.status == "CLOSED"]
        open_  = [t for t in self._trades if t.status == "OPEN"]

        if not closed:
            return self._empty_metrics(open_)

        wins   = [t for t in closed if t.net_pnl > 0]
        losses = [t for t in closed if t.net_pnl <= 0]
        buys   = [t for t in closed if t.direction == "BUY"]
        sells  = [t for t in closed if t.direction == "SELL"]

        gross_profit   = sum(t.net_pnl for t in wins)
        gross_loss     = sum(t.net_pnl for t in losses)
        net_pnl        = gross_profit + gross_loss
        total_brokerage= sum(t.brokerage for t in closed)
        actual_return  = self.initial_capital + net_pnl

        win_pct = (len(wins) / len(closed) * 100) if closed else 0.0

        pnl_series = [t.net_pnl for t in closed]
        max_gain   = max(pnl_series, default=0.0)
        max_loss   = min(pnl_series, default=0.0)

        win_streak  = self._max_streak(pnl_series, positive=True)
        loss_streak = self._max_streak(pnl_series, positive=False)
        max_dd      = self._max_drawdown(pnl_series)

        return {
            "winning_trades"  : len(wins),
            "losing_trades"   : len(losses),
            "total_trades"    : len(closed),
            "win_pct"         : round(win_pct, 2),
            "buy_trades"      : len(buys),
            "sell_trades"     : len(sells),
            "open_trades"     : len(open_),
            "closed_trades"   : len(closed),
            "gross_profit"    : round(gross_profit, 4),
            "gross_loss"      : round(gross_loss, 4),
            "net_pnl"         : round(net_pnl, 2),
            "total_brokerage" : round(total_brokerage, 2),
            "actual_return"   : round(actual_return, 2),
            "win_streak"      : win_streak,
            "loss_streak"     : loss_streak,
            "max_drawdown"    : round(max_dd, 2),
            "max_gain"        : round(max_gain, 2),
            "max_loss"        : round(max_loss, 2),
        }

    # ── CSV export ────────────────────────────────────────────
    def save_to_csv(self, prefix: str = "REPORT_") -> str:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        ts       = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{prefix}{self.asset}_{ts}.csv"
        filepath = os.path.join(OUTPUT_DIR, filename)

        if not self._trades:
            print_info("No trades to save.")
            return filepath

        fieldnames = list(asdict(self._trades[0]).keys())
        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for t in self._trades:
                writer.writerow(asdict(t))

        print_info(f"File saved to: ./{filepath}")
        return filepath

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([asdict(t) for t in self._trades])

    # ── helpers ───────────────────────────────────────────────
    @staticmethod
    def _max_streak(pnl_list: list, positive: bool) -> int:
        best = cur = 0
        for p in pnl_list:
            if (p > 0) == positive:
                cur += 1
                best = max(best, cur)
            else:
                cur = 0
        return best

    @staticmethod
    def _max_drawdown(pnl_list: list) -> float:
        cumulative = 0.0
        peak       = 0.0
        max_dd     = 0.0
        for p in pnl_list:
            cumulative += p
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd
        return max_dd

    @staticmethod
    def _empty_metrics(open_trades) -> dict:
        return {k: 0 for k in [
            "winning_trades","losing_trades","total_trades","win_pct",
            "buy_trades","sell_trades","gross_profit","gross_loss",
            "net_pnl","total_brokerage","actual_return",
            "win_streak","loss_streak","max_drawdown","max_gain","max_loss",
        ]} | {"open_trades": len(open_trades), "closed_trades": 0}


    def _calculate_charges(self,entry_price,exit_price,qty):
        
        buy_value= entry_price * qty
        sell_value= exit_price * qty
        turnover= buy_value + sell_value
        
        # STT (Delivery)
        stt= 0.001 * buy_value + 0.001 * sell_value
        
        # Exchange txn charge
        exch= 0.000345 * turnover
        
        # GST (18% on transaction)
        GST= 0.18 * exch
        
        # SEBI Charge
        sebi= turnover * 0.000001
        
        # Stamp duty (Only on Buy)
        stamp= 0.00015 * buy_value
        
        total= stt + exch + GST + sebi + stamp
        return total