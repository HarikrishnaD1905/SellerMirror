"""
Competitor Signal Engine
Computes 6 weekly-aggregated signals for 'competitor' over the 90-day period.

Signals
-------
sentiment_score        — VADER compound score on review_text, averaged per week
price_velocity         — avg daily price change per week (negative = dropping = worsening)
rating_velocity        — avg rating this week minus avg rating last week (negative = worsening)
review_volume_trend    — review count this week minus last week (negative = worsening)
discount_frequency     — days where is_on_sale==True / total days that week (higher = worse)
unanswered_rate        — sum(unanswered_questions) / days that week, averaged (higher = worse)

Each signal returns: latest, prev, trend ('improving'/'worsening'/'stable'), weekly Series.
Everything collected into comp_signals dict.
"""

import nltk
import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer

nltk.download("vader_lexicon", quiet=True)

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ingestion.competitor_data_loader import load_competitor_data

# ── Constants ─────────────────────────────────────────────────────────────────
TREND_THRESHOLD = 0.02


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
        "latest":  round(latest, 4),
        "prev":    round(prev, 4),
        "trend":   _trend(latest, prev, higher_is_better),
        "weekly":  clean,
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


def _price_velocity(metrics_df: pd.DataFrame) -> dict:
    """
    Avg daily price change per week.
    Negative = price is dropping = competitor discounting = worsening for them.
    """
    df = metrics_df[["date", "price"]].copy().sort_values("date")
    df["price_change"] = df["price"].diff()          # daily delta
    df["week"] = df["date"].dt.to_period("W")
    weekly = df.groupby("week")["price_change"].mean()
    # For price_velocity: negative (dropping) is worsening → higher_is_better=True
    return _pack(weekly, higher_is_better=True)


def _rating_velocity(reviews_df: pd.DataFrame) -> dict:
    """
    Avg rating this week minus avg rating the previous week.
    Negative = rating falling = worsening.
    """
    df = reviews_df[["date", "rating"]].copy()
    df["week"] = df["date"].dt.to_period("W")
    weekly_avg = df.groupby("week")["rating"].mean()
    velocity = weekly_avg.diff()                     # week-over-week change
    # Positive velocity = improving; higher_is_better=True
    return _pack(velocity, higher_is_better=True)


def _review_volume_trend(reviews_df: pd.DataFrame) -> dict:
    """
    Review count this week minus last week.
    Negative = fewer reviews = worsening momentum.
    """
    df = reviews_df[["date"]].copy()
    df["week"] = df["date"].dt.to_period("W")
    weekly_count = df.groupby("week").size()
    volume_change = weekly_count.diff()              # week-over-week delta
    return _pack(volume_change, higher_is_better=True)


def _discount_frequency(metrics_df: pd.DataFrame) -> dict:
    """
    Proportion of days in each week where is_on_sale == True.
    Higher = more desperate discounting = worsening.
    """
    df = metrics_df[["date", "is_on_sale"]].copy()
    df["on_sale"] = df["is_on_sale"].astype(int)
    df["week"] = df["date"].dt.to_period("W")
    weekly = df.groupby("week")["on_sale"].mean()
    return _pack(weekly, higher_is_better=False)     # lower discount freq = better


def _unanswered_rate(metrics_df: pd.DataFrame) -> dict:
    """
    Sum of unanswered_questions per week / days in that week.
    Higher = worse seller responsiveness.
    """
    df = metrics_df[["date", "unanswered_questions"]].copy()
    df["week"] = df["date"].dt.to_period("W")
    weekly = df.groupby("week")["unanswered_questions"].mean()
    return _pack(weekly, higher_is_better=False)     # lower = better


# ── Main entry point ──────────────────────────────────────────────────────────

def compute_competitor_signals() -> dict:
    """
    Load competitor data and compute all 6 signals.

    Returns
    -------
    comp_signals : dict
        Keys: sentiment_score, price_velocity, rating_velocity,
              review_volume_trend, discount_frequency, unanswered_rate
        Each value: dict with latest, prev, trend, weekly (pd.Series)
    """
    reviews_df, metrics_df = load_competitor_data()

    comp_signals = {
        "sentiment_score":    _sentiment_score(reviews_df),
        "price_velocity":     _price_velocity(metrics_df),
        "rating_velocity":    _rating_velocity(reviews_df),
        "review_volume_trend":_review_volume_trend(reviews_df),
        "discount_frequency": _discount_frequency(metrics_df),
        "unanswered_rate":    _unanswered_rate(metrics_df),
    }
    return comp_signals


# ── Test print ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    comp_signals = compute_competitor_signals()

    TREND_EMOJI = {"improving": "📈", "worsening": "📉", "stable": "➡️"}

    print("=" * 55)
    print("  COMPETITOR — Weekly Signal Summary")
    print("=" * 55)
    fmt = "{:<22}  {:>8}  {:>8}  {}"
    print(fmt.format("Signal", "Latest", "Prev", "Trend"))
    print("-" * 55)
    for name, sig in comp_signals.items():
        emoji = TREND_EMOJI.get(sig["trend"], "")
        print(fmt.format(
            name,
            f"{sig['latest']:.4f}",
            f"{sig['prev']:.4f}",
            f"{emoji} {sig['trend']}",
        ))
    print("=" * 55)
