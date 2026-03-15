"""
Analytics Module
Three competitive intelligence functions:

1. complaint_mirror      — shared complaint categories, who's winning per category
2. trust_gap_race        — repeat purchase rate vs competitor rating velocity
3. momentum_shift        — consecutive price drop + review volume decline detection

Entry point: run_comparison() — loads all data, runs all three, returns results tuple.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd  # type: ignore
from transformers import pipeline as hf_pipeline  # type: ignore
from trend_validator.trend_validator import validate_both  # type: ignore
from ingestion.product_data_loader import load_product_data  # type: ignore
from ingestion.competitor_data_loader import load_competitor_data  # type: ignore


# ── Complaint categories (AI zero-shot classification) ────────────────────────

import torch  # type: ignore

# AI: zero-shot transformer classification — no hardcoded keyword rules
device = 0 if torch.cuda.is_available() else -1
complaint_classifier = hf_pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli",
    device=device,
)

CANDIDATE_LABELS = [
    "product quality issue",
    "delivery or shipping problem",
    "packaging damage",
    "listing inaccurate or misleading",
]

# Map from full candidate label → short name used everywhere else
LABEL_MAP = {
    "product quality issue":            "quality",
    "delivery or shipping problem":      "delivery",
    "packaging damage":                  "packaging",
    "listing inaccurate or misleading":  "listing",
}

LABEL_NAMES = list(LABEL_MAP.values())  # ["quality", "delivery", "packaging", "listing"]


def _count_complaints(reviews_df: pd.DataFrame) -> dict[str, int]:
    """Run zero-shot classification on low-rated reviews (rating ≤ 3) and count per category."""
    counts = {cat: 0 for cat in LABEL_NAMES}
    low_rated = reviews_df[reviews_df["rating"] <= 3]["review_text"].dropna()
    for review_text in low_rated:
        result = complaint_classifier(str(review_text), candidate_labels=CANDIDATE_LABELS)
        top_label = result["labels"][0]          # highest-score label
        short_name = LABEL_MAP[top_label]
        counts[short_name] += 1
    return counts


# ── 1. Complaint Mirror ────────────────────────────────────────────────────────

def complaint_mirror(
    validated_my_signals: dict,
    validated_comp_signals: dict,
    my_reviews_df: pd.DataFrame,
    comp_reviews_df: pd.DataFrame,
) -> dict:
    """
    Classify reviews into complaint categories for both sellers.
    Find shared complaint categories and determine winner per category.

    Returns
    -------
    {
        shared_categories    : list[str],
        my_complaint_counts  : dict[str, int],
        comp_complaint_counts: dict[str, int],
        winner_per_category  : dict[str, str]   ('my_product' | 'competitor' | 'tie')
    }
    """
    my_counts   = _count_complaints(my_reviews_df)
    comp_counts = _count_complaints(comp_reviews_df)

    # Shared = both have at least 1 complaint in that category
    shared = [cat for cat in LABEL_NAMES
              if my_counts[cat] > 0 and comp_counts[cat] > 0]

    winner_per_category = {}
    for cat in shared:
        my_c   = my_counts[cat]
        comp_c = comp_counts[cat]
        if my_c < comp_c:
            winner_per_category[cat] = "my_product"   # fewer complaints = winning
        elif comp_c < my_c:
            winner_per_category[cat] = "competitor"
        else:
            winner_per_category[cat] = "tie"

    return {
        "shared_categories":     shared,
        "my_complaint_counts":   my_counts,
        "comp_complaint_counts": comp_counts,
        "winner_per_category":   winner_per_category,
    }


# ── 2. Trust Gap Race ─────────────────────────────────────────────────────────

def trust_gap_race(
    validated_my_signals: dict,
    validated_comp_signals: dict,
) -> dict:
    """
    Compare my repeat_purchase_rate (latest) vs competitor rating_velocity (weekly mean).

    Winner rules
    ------------
    'my_product'  — my repeat_rate > 0.15  AND comp rating_velocity < -0.1
    'competitor'  — comp rating_velocity > 0 AND my repeat_rate < 0.10
    'neutral'     — everything else

    Returns
    -------
    {
        my_repeat_rate        : float,
        comp_rating_vel_mean  : float,
        winner                : str
    }
    """
    # My repeat purchase rate — use latest
    my_sig = validated_my_signals.get("repeat_purchase_rate", {})
    my_repeat = my_sig.get("latest", float("nan"))

    # Competitor rating velocity — use weekly mean (same logic as scorer)
    comp_sig = validated_comp_signals.get("rating_velocity", {})
    weekly   = comp_sig.get("weekly")
    if weekly is not None and not weekly.dropna().empty:
        comp_rating_vel_mean = float(weekly.dropna().mean())
    else:
        comp_rating_vel_mean = float("nan")

    # Determine winner
    import math
    if (not math.isnan(my_repeat) and not math.isnan(comp_rating_vel_mean)):
        if my_repeat > 0.15 and comp_rating_vel_mean < -0.1:
            winner = "my_product"
        elif comp_rating_vel_mean > 0 and my_repeat < 0.10:
            winner = "competitor"
        else:
            winner = "neutral"
    else:
        winner = "neutral"

    return {
        "my_repeat_rate":       round(float(my_repeat), 4) if not math.isnan(my_repeat) else None,  # type: ignore
        "comp_rating_vel_mean": round(float(comp_rating_vel_mean), 4) if not math.isnan(comp_rating_vel_mean) else None,  # type: ignore
        "winner":               winner,
    }


# ── 3. Momentum Shift ─────────────────────────────────────────────────────────

def momentum_shift(
    validated_comp_signals: dict,
    comp_metrics_df: pd.DataFrame,
) -> dict:
    """
    Two checks for competitor momentum loss:

    Check A — price_drop_streak:
        Did the competitor's price drop for 5+ consecutive days in the last 30 days?

    Check B — review_volume_decline:
        Is review count in last 3 weeks lower than first 3 weeks of the dataset?

    momentum_lost : True  if both checks pass
    partial       : True  if exactly one check passes

    Returns
    -------
    {
        price_drop_streak       : bool,
        price_drop_streak_days  : int,
        review_volume_decline   : bool,
        early_review_avg        : float,
        late_review_avg         : float,
        momentum_lost           : bool,
        partial                 : bool,
    }
    """
    # ── Check A: consecutive price drop streak in last 30 days ────────────────
    df = comp_metrics_df[["date", "price"]].copy().sort_values("date")
    last_30 = df[df["date"] >= df["date"].max() - pd.Timedelta(days=30)].copy()
    last_30["price_diff"] = last_30["price"].diff()

    max_streak = 0
    current_streak = 0
    for diff in last_30["price_diff"].dropna():
        if diff < 0:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0

    price_drop_streak      = max_streak >= 5
    price_drop_streak_days = max_streak

    # ── Check B: review volume — first 3 weeks vs last 3 weeks ───────────────
    comp_weekly = validated_comp_signals.get("review_volume_trend", {}).get("weekly")

    if comp_weekly is not None and len(comp_weekly.dropna()) >= 6:
        clean = comp_weekly.dropna()
        # Reconstruct cumulative counts from diff series by using raw review counts
        # We'll fall back to comparing weekly trend values directly
        first_3_avg = float(clean.iloc[:3].mean())
        last_3_avg  = float(clean.iloc[-3:].mean())
        review_volume_decline = last_3_avg < first_3_avg
    else:
        # Fallback: count reviews directly from comp_metrics_df proxy
        # (use daily_purchases as a volume proxy if reviews not available)
        df_m = comp_metrics_df[["date", "daily_purchases"]].copy().sort_values("date")
        df_m["week"] = df_m["date"].dt.to_period("W")
        weekly_vol = df_m.groupby("week")["daily_purchases"].sum()
        if len(weekly_vol) >= 6:
            first_3_avg = float(weekly_vol.iloc[:3].mean())
            last_3_avg  = float(weekly_vol.iloc[-3:].mean())
        else:
            first_3_avg = last_3_avg = float("nan")
        review_volume_decline = last_3_avg < first_3_avg if (first_3_avg == first_3_avg) else False

    # ── Combine ───────────────────────────────────────────────────────────────
    momentum_lost = price_drop_streak and review_volume_decline
    partial       = (price_drop_streak != review_volume_decline)   # XOR

    return {
        "price_drop_streak":       price_drop_streak,
        "price_drop_streak_days":  price_drop_streak_days,
        "review_volume_decline":   review_volume_decline,
        "early_vol_avg":           round(float(first_3_avg), 2),  # type: ignore
        "late_vol_avg":            round(float(last_3_avg), 2),  # type: ignore
        "momentum_lost":           momentum_lost,
        "partial":                 partial,
    }


# ── Combined entry point ──────────────────────────────────────────────────────

def run_comparison() -> tuple[dict, dict, dict]:
    """
    Load all data, run all three analytics functions.

    Returns
    -------
    (complaint_mirror_result, trust_gap_result, momentum_shift_result)
    """
    my_reviews_df,   my_metrics_df   = load_product_data()
    comp_reviews_df, comp_metrics_df = load_competitor_data()
    validated_my, validated_comp     = validate_both()

    cm_result  = complaint_mirror(validated_my, validated_comp, my_reviews_df, comp_reviews_df)
    tg_result  = trust_gap_race(validated_my, validated_comp)
    ms_result  = momentum_shift(validated_comp, comp_metrics_df)

    return cm_result, tg_result, ms_result


def tg_icon(val: bool) -> str:
    return "✅ Yes" if val else "❌ No"


# ── Test print ────────────────────────────────────────────────────────────────
if __name__ == "__main__":

    cm, tg, ms = run_comparison()

    print("\n" + "=" * 58)
    print("  1. COMPLAINT MIRROR")
    print("=" * 58)
    print(f"  Shared categories : {cm['shared_categories']}")
    print(f"\n  {'Category':<12}  {'Mine':>5}  {'Comp':>5}  {'Winner':<12}")
    print("  " + "-" * 42)
    for cat in LABEL_NAMES:
        my_c   = cm["my_complaint_counts"][cat]
        comp_c = cm["comp_complaint_counts"][cat]
        win    = cm["winner_per_category"].get(cat, "—")
        flag   = "🏆" if win == "my_product" else ("💀" if win == "competitor" else ("🤝" if win == "tie" else " "))
        print(f"  {cat:<12}  {my_c:>5}  {comp_c:>5}  {flag} {win}")

    print("\n" + "=" * 58)
    print("  2. TRUST GAP RACE")
    print("=" * 58)
    winner_label = {"my_product": "🏆 My Product", "competitor": "💀 Competitor", "neutral": "➡️  Neutral"}
    print(f"  My repeat purchase rate   : {tg['my_repeat_rate']}")
    print(f"  Comp rating velocity mean : {tg['comp_rating_vel_mean']}")
    print(f"  Winner                    : {winner_label.get(tg['winner'], tg['winner'])}")

    print("\n" + "=" * 58)
    print("  3. MOMENTUM SHIFT")
    print("=" * 58)
    print(f"  Price drop streak ≥5 days : {tg_icon(ms['price_drop_streak'])} ({ms['price_drop_streak_days']} days)")
    print(f"  Review volume decline     : {tg_icon(ms['review_volume_decline'])}")
    print(f"    Early vol avg           : {ms['early_vol_avg']}")
    print(f"    Late  vol avg           : {ms['late_vol_avg']}")
    print(f"  Momentum Lost             : {'🔴 YES' if ms['momentum_lost'] else ('🟡 PARTIAL' if ms['partial'] else '🟢 NO')}")
    print("=" * 58)
