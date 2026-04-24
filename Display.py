# ============================================================
#  Display.py  –  Console output helpers
# ============================================================
from datetime import datetime


_SEP  = "=" * 55
_DASH = "-" * 55


def print_header(title: str) -> None:
    print(f"\n{_SEP}")
    print(f"  {title}")
    print(_SEP)


def print_section(title: str) -> None:
    print(f"\n{_DASH}")
    print(f"  {title}")
    print(_DASH)


def print_kv(label: str, value, width: int = 32) -> None:
    """Print a key-value pair with aligned columns."""
    print(f"  {label:<{width}}: {value}")


def print_trade_summary(result: dict) -> None:
    """Pretty-print the full backtest result dict."""
    print_header("BACKTEST RESULTS")

    print_section("Trade Statistics")
    print_kv("Total Winning Trades",   result.get("winning_trades", 0))
    print_kv("Total Loss Trades",      result.get("losing_trades", 0))
    print_kv("Total Trades",           result.get("total_trades", 0))
    print_kv("Win/Loss Percentage %",  f"{result.get('win_pct', 0.0):.2f}")
    print_kv("Buy Trades",             result.get("buy_trades", 0))
    print_kv("Sell Trades",            result.get("sell_trades", 0))
    print_kv("Open Trades",            result.get("open_trades", 0))
    print_kv("Closed Trades",          result.get("closed_trades", 0))

    print_section("Profit & Loss")
    print_kv("Gain Point/PnL",         f"{result.get('gross_profit', 0.0):.4f}")
    print_kv("Loss Point/PnL",         f"{result.get('gross_loss', 0.0):.4f}")
    print_kv("NET Point/PnL",          f"{result.get('net_pnl', 0.0):.2f}")
    print_kv("Brokerage Cost (total)", f"{result.get('total_brokerage', 0.0):.2f}")
    print_kv("Actual Return (₹)",      f"{result.get('actual_return', 0.0):.2f}")

    print_section("Streaks & Drawdown")
    print_kv("Winning Streak",         result.get("win_streak", 0))
    print_kv("Losing Streak",          result.get("loss_streak", 0))
    print_kv("Max DrawDown Point/PnL", f"{result.get('max_drawdown', 0.0):.2f}")
    print_kv("Maximum Point Gain",     f"{result.get('max_gain', 0.0):.2f}")
    print_kv("Maximum Point Loss",     f"{result.get('max_loss', 0.0):.2f}")

    print(f"\n{_SEP}")
    print("  Trade Bank Completed")
    print(_SEP)


def print_info(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] INFO  : {msg}")


def print_warn(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] WARN  : {msg}")


def print_error(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] ERROR : {msg}")
