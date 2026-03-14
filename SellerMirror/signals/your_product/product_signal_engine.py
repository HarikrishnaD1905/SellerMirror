"""
Product Signal Engine
Computes 6 weekly-aggregated signals for 'my_product' over the 90-day period.

Signals
-------
sentiment_score        — VADER compound score on review_text, averaged per week
ghost_rate             — (daily_views - daily_purchases) / daily_views, weekly avg
cart_abandonment_rate  — (cart_adds - cart_completions) / cart_adds, weekly avg
three_star_ratio       — count(rating==3) / total reviews that week
repeat_purchase_rate   — repeat_purchases / daily_purchases, weekly avg
return_rate            — returns / daily_purchases, weekly avg

Each signal returns: latest_value, prev_value, trend ('improving'/'worsening'/'stable')
Everything is collected into a single dict: my_signals
"""

import nltk
import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer

nltk.download("vader_lexicon", quiet=True)

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ingestion.product_data_loader import load_product_data

# ── Constants ─────────────────────────────────────────────────────────────────
TREND_THRESHOLD = 0.02   # minimum delta to call a direction


# ── Helpers ───────────────────────────────────────────────────────────────────

def _trend(latest: float, prev: float, higher_is_better: bool) -> str:
    """Return 'improving', 'worsening', or 'stable' based on delta."""
    delta = latest - prev
    if abs(delta) < TREND_THRESHOLD:
        return "stable"
    improved = delta > 0 if higher_is_better else delta < 0
    return "improving" if improved else "worsening"


def _pack(weekly: pd.Series, higher_is_better: bool) -> dict:
    """Extract latest, prev, trend from a weekly-indexed Series."""
    clean = weekly.dropna()
    latest = float(clean.iloc[-1]) if len(clean) >= 1 else float("nan")
    prev   = float(clean.iloc[-2]) if len(clean) >= 2 else latest
    return {
        "latest":    round(latest, 4),
        "prev":      round(prev, 4),
        "trend":     _trend(latest, prev, higher_is_better),
        "weekly":    clean,           # full weekly series kept for downstream use
    }


# ── Signal calculators ────────────────────────────────────────────────────────

def _sentiment_score(reviews_df: pd.DataFrame) -> dict:
    """VADER compound score averaged per ISO week."""
    sid = SentimentIntensityAnalyzer()

    df = reviews_df[["date", "review_text"]].copy()
    df["compound"] = df["review_text"].apply(
        lambda t: sid.polarity_scores(str(t))["compound"]
    )
    df["week"] = df["date"].dt.to_period("W")
    weekly = df.groupby("week")["compound"].mean()
    return _pack(weekly, higher_is_better=True)


def _ghost_rate(metrics_df: pd.DataFrame) -> dict:
    """(daily_views - daily_purchases) / daily_views, weekly avg."""
    df = metrics_df[["date", "daily_views", "daily_purchases"]].copy()
    df["ghost"] = (df["daily_views"] - df["daily_purchases"]) / df["daily_views"].clip(lower=1)
    df["week"]  = df["date"].dt.to_period("W")
    weekly = df.groupby("week")["ghost"].mean()
    return _pack(weekly, higher_is_better=False)   # lower ghost_rate is better


def _cart_abandonment_rate(metrics_df: pd.DataFrame) -> dict:
    """(cart_adds - cart_completions) / cart_adds, weekly avg."""
    df = metrics_df[["date", "cart_adds", "cart_completions"]].copy()
    df["abandon"] = (df["cart_adds"] - df["cart_completions"]) / df["cart_adds"].clip(lower=1)
    df["week"]    = df["date"].dt.to_period("W")
    weekly = df.groupby("week")["abandon"].mean()
    return _pack(weekly, higher_is_better=False)   # lower abandonment is better


def _three_star_ratio(reviews_df: pd.DataFrame) -> dict:
    """Proportion of 3-star reviews per week."""
    df = reviews_df[["date", "rating"]].copy()
    df["week"]    = df["date"].dt.to_period("W")
    df["is_3"]    = (df["rating"] == 3).astype(int)
    weekly = df.groupby("week").apply(
        lambda g: g["is_3"].sum() / len(g) if len(g) > 0 else float("nan")
    )
    return _pack(weekly, higher_is_better=False)   # lower 3-star ratio is better


def _repeat_purchase_rate(metrics_df: pd.DataFrame) -> dict:
    """repeat_purchases / daily_purchases, weekly avg."""
    df = metrics_df[["date", "repeat_purchases", "daily_purchases"]].copy()
    df["repeat_rate"] = df["repeat_purchases"] / df["daily_purchases"].clip(lower=1)
    df["week"]        = df["date"].dt.to_period("W")
    weekly = df.groupby("week")["repeat_rate"].mean()
    return _pack(weekly, higher_is_better=True)    # higher repeat rate is better


def _return_rate(metrics_df: pd.DataFrame) -> dict:
    """returns / daily_purchases, weekly avg."""
    df = metrics_df[["date", "returns", "daily_purchases"]].copy()
    df["ret_rate"] = df["returns"] / df["daily_purchases"].clip(lower=1)
    df["week"]     = df["date"].dt.to_period("W")
    weekly = df.groupby("week")["ret_rate"].mean()
    return _pack(weekly, higher_is_better=False)   # lower return rate is better


# ── Main entry point ──────────────────────────────────────────────────────────

def compute_product_signals() -> dict:
    """
    Load data and compute all 6 signals.

    Returns
    -------
    my_signals : dict
        Keys: sentiment_score, ghost_rate, cart_abandonment_rate,
              three_star_ratio, repeat_purchase_rate, return_rate
        Each value is a dict with: latest, prev, trend, weekly (pd.Series)
    """
    reviews_df, metrics_df = load_product_data()

    my_signals = {
        "sentiment_score":       _sentiment_score(reviews_df),
        "ghost_rate":            _ghost_rate(metrics_df),
        "cart_abandonment_rate": _cart_abandonment_rate(metrics_df),
        "three_star_ratio":      _three_star_ratio(reviews_df),
        "repeat_purchase_rate":  _repeat_purchase_rate(metrics_df),
        "return_rate":           _return_rate(metrics_df),
    }
    return my_signals


# ── Test print ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    my_signals = compute_product_signals()

    TREND_EMOJI = {"improving": "📈", "worsening": "📉", "stable": "➡️"}

    print("=" * 52)
    print("  MY PRODUCT — Weekly Signal Summary")
    print("=" * 52)
    fmt = "{:<26}  {:>7}  {:>7}  {}"
    print(fmt.format("Signal", "Latest", "Prev", "Trend"))
    print("-" * 52)
    for name, sig in my_signals.items():
        emoji = TREND_EMOJI.get(sig["trend"], "")
        print(fmt.format(
            name,
            f"{sig['latest']:.4f}",
            f"{sig['prev']:.4f}",
            f"{emoji} {sig['trend']}",
        ))
    print("=" * 52)
