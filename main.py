# ============================================================
#  main.py  –  Entry point  (mirrors your original design)
# ============================================================
import faulthandler
from BackTest import BackTest

if __name__ == '__main__':
    faulthandler.enable()
    print("starting..")

    # ── Configure your run here ───────────────────────────────
    #
    #  BackTest(
    #      asset_name  = "RELIANCE",   # must match CSV filename in data/
    #      strategy    = "sma",        # sma | ema | macd | rsi | bollinger
    #      csv_path    = "",           # leave blank → auto: data/RELIANCE.csv
    #      capital     = 100_000,      # starting capital ₹
    #      quantity    = 1,            # shares per trade
    #      noise_below = 1400.0,       # ignore signals below this price
    #  )
    # ─────────────────────────────────────────────────────────

    run1 = BackTest("RELIANCE")
    run1.run()
    run1.PrintToCsv("REPORT_TF_1_")

    # ── Run multiple strategies on the same symbol ────────────
    # for strat in ["sma", "ema", "macd", "rsi", "bollinger"]:
    #     bt = BackTest("RELIANCE", strategy=strat)
    #     bt.run()
    #     bt.PrintToCsv(f"REPORT_{strat.upper()}_")
