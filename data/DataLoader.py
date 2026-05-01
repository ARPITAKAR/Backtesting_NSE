# ============================================================
#  DataLoader.py  –  Load & validate CSV OHLCV data
# ============================================================
import os
import pandas as pd
from utils.Constants import (
    COL_DATE, COL_OPEN, COL_HIGH, COL_LOW, COL_CLOSE, COL_VOLUME,
    DATE_FORMAT,
)
from utils.Display import print_info, print_warn, print_error


REQUIRED_COLS = [COL_OPEN, COL_HIGH, COL_LOW, COL_CLOSE]


class DataLoader:
    """
    Loads OHLCV data from a CSV file, validates columns,
    parses dates and returns a clean DataFrame.

    Usage
    -----
    loader = DataLoader("data/RELIANCE.csv")
    df     = loader.load()
    """

    def __init__(self, filepath: str):
        self.filepath = filepath

    # ----------------------------------------------------------
    def load(self) -> pd.DataFrame:
        if not os.path.exists(self.filepath):
            print_error(f"File not found: {self.filepath}")
            raise FileNotFoundError(self.filepath)

        print_info(f"Loading data from: {self.filepath}")
        df = pd.read_csv(self.filepath)

        df = self._validate_columns(df)
        df = self._parse_dates(df)
        df = self._clean(df)

        print_info(f"Loaded {len(df)} rows  |  "
                   f"{df.index[0]}  →  {df.index[-1]}")
        return df

    # ----------------------------------------------------------
    def _validate_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        # Normalise column names (strip whitespace, title-case)
        df.columns = [c.strip() for c in df.columns]

        missing = [c for c in REQUIRED_COLS if c not in df.columns]
        if missing:
            print_error(f"Missing columns: {missing}")
            raise ValueError(f"CSV is missing required columns: {missing}")

        if COL_VOLUME not in df.columns:
            print_warn("Volume column not found – filling with 0")
            df[COL_VOLUME] = 0

        return df

    # ----------------------------------------------------------
    def _parse_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        if COL_DATE in df.columns:
            try:
                df[COL_DATE] = pd.to_datetime(df[COL_DATE],format=DATE_FORMAT)
                df = df.set_index(COL_DATE).sort_index()
            except Exception as e:
                print_warn(f"Could not parse Date column: {e}")
        else:
            print_warn("No 'Date' column found – using integer index")

        return df

    # ----------------------------------------------------------
    def _clean(self, df: pd.DataFrame) -> pd.DataFrame:
        before = len(df)
        df = df[REQUIRED_COLS + ([COL_VOLUME] if COL_VOLUME in df.columns else [])]
        df = df.dropna(subset=REQUIRED_COLS)
        df = df.astype({c: float for c in REQUIRED_COLS})
        after = len(df)
        if before != after:
            print_warn(f"Dropped {before - after} rows with NaN values")
        return df
