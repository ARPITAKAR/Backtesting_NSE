# ============================================================
#  Constants.py  –  Central config for the BackTesting engine
# ============================================================

# ---------- Capital & Brokerage ----------
INITIAL_CAPITAL      = 100_000      # Starting capital in ₹
BROKERAGE_PER_TRADE  = 20           # Flat ₹20 per executed order (Zerodha style)
LOT_SIZE             = 1            # Default lot / quantity multiplier

# ---------- CSV Column Names (change to match your file) ----------
COL_DATE   = "Date"
COL_OPEN   = "Open"
COL_HIGH   = "High"
COL_LOW    = "Low"
COL_CLOSE  = "Close"
COL_VOLUME = "Volume"

# ---------- Indicator Defaults ----------
SMA_FAST        = 20
SMA_SLOW        = 50
EMA_FAST        = 12
EMA_SLOW        = 26
MACD_SIGNAL     = 9
RSI_PERIOD      = 14
RSI_OVERBOUGHT  = 70
RSI_OVERSOLD    = 30
BB_PERIOD       = 20
BB_STD          = 2.0

# ---------- Risk Defaults ----------
TRAILING_STOP_PCT   = 0.02     # 2 % trailing stop
MAX_OPEN_TRADES     = 4
MIN_BARS_BETWEEN    = 3        # Minimum bars between two entries

# ---------- Output ----------
OUTPUT_DIR          = "output"
DATE_FORMAT         = "%Y-%m-%d"
