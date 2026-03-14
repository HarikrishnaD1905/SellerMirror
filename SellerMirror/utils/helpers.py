"""
Utility helpers for SellerMirror
"""

import pandas as pd
import numpy as np
from pathlib import Path


def normalize_series(s: pd.Series, clip_min: float = 0.0, clip_max: float = 1.0) -> pd.Series:
    """Min-max normalize a pandas Series to [clip_min, clip_max]."""
    rng = s.max() - s.min()
    if rng == 0:
        return pd.Series(np.zeros(len(s)), index=s.index)
    return ((s - s.min()) / rng).clip(clip_min, clip_max)


def rolling_slope(series: pd.Series, window: int = 7) -> pd.Series:
    """Compute rolling linear slope of a time series."""
    def slope(x):
        if len(x) < 2:
            return np.nan
        return np.polyfit(range(len(x)), x, 1)[0]
    return series.rolling(window, min_periods=2).apply(slope, raw=True)


def ensure_dir(path: str):
    """Create directory if it doesn't exist."""
    Path(path).mkdir(parents=True, exist_ok=True)


def safe_pct_change(series: pd.Series) -> pd.Series:
    """Percentage change, safe against division by zero."""
    return series.pct_change().replace([np.inf, -np.inf], np.nan)
