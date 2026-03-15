"""
Trend Validator
Validates signals from both signal engines.

Rules
-----
1. Consistent for last 5 weeks (all diff same sign) → keep as-is
2. Only 1-2 weeks of directional movement in last 5 → set trend='stable', noise=True
3. Fewer than 5 weeks of data in weekly Series → keep as-is, insufficient_data=True
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from signals.your_product.product_signal_engine import compute_product_signals
from signals.competitor.competitor_signal_engine import compute_competitor_signals


# ── Core validation logic ─────────────────────────────────────────────────────

def _count_consistent_direction(weekly_series) -> tuple[int, int]:
    """
    Over the last 5 data points of weekly_series, count how many
    consecutive diffs share the same sign.

    Returns
    -------
    consistent_count : int   — number of diffs pointing same direction (max 4)
    total_diffs      : int   — how many diffs exist (min(len-1, 4))
    """
    clean = weekly_series.dropna()
    window = clean.iloc[-5:] if len(clean) >= 5 else clean
    if len(window) < 2:
        return 0, 0
    diffs = window.diff().dropna()
    # Count how many diffs share the sign of the first diff
    first_sign = (diffs.iloc[0] > 0)
    consistent = sum(1 for d in diffs if (d > 0) == first_sign and d != 0)
    return consistent, len(diffs)


def validate_trends(signals_dict: dict) -> dict:
    """
    Validate each signal in signals_dict.

    Parameters
    ----------
    signals_dict : dict
        Output from compute_product_signals() or compute_competitor_signals().

    Returns
    -------
    validated : dict
        Same structure, each signal may have added keys:
          - 'noise': True           if only 1-2 weeks of directional movement
          - 'insufficient_data': True  if fewer than 5 weeks of data
        If noise, trend is overridden to 'stable'.
    """
    import copy
    validated = copy.deepcopy(signals_dict)

    for name, sig in validated.items():
        weekly = sig.get("weekly")
        if weekly is None or len(weekly.dropna()) == 0:
            sig["insufficient_data"] = True
            continue

        n_weeks = len(weekly.dropna())

        # Rule 3: fewer than 5 weeks of data → keep, flag
        if n_weeks < 5:
            sig["insufficient_data"] = True
            continue

        consistent_count, total_diffs = _count_consistent_direction(weekly)

        # Rule 2: 0 or 1 consistent diffs out of 4 → noise (< 4 of 5 points agree)
        if consistent_count <= 1:
            sig["trend"]  = "stable"
            sig["noise"]  = True
        # Rule 1: 2+ consistent diffs (≥ 4 of 5 points agree) → validated
        else:
            sig["noise"]  = False

    return validated


def validate_both() -> tuple[dict, dict]:
    """
    Compute and validate signals for both sellers.

    Returns
    -------
    (validated_my_signals, validated_comp_signals)
    """
    my_signals   = compute_product_signals()
    comp_signals = compute_competitor_signals()

    validated_my   = validate_trends(my_signals)
    validated_comp = validate_trends(comp_signals)

    return validated_my, validated_comp


# ── Test print ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    validated_my, validated_comp = validate_both()

    TREND_EMOJI = {"improving": "📈", "worsening": "📉", "stable": "➡️"}

    def _print_validation(label: str, validated: dict):
        print(f"\n{'=' * 60}")
        print(f"  {label} — Trend Validation")
        print(f"{'=' * 60}")
        fmt = "{:<24}  {:>8}  {:<12}  {}"
        print(fmt.format("Signal", "Latest", "Trend", "Status"))
        print("-" * 60)
        for name, sig in validated.items():
            emoji  = TREND_EMOJI.get(sig["trend"], "")
            trend  = f"{emoji} {sig['trend']}"
            if sig.get("insufficient_data"):
                status = "⚠️  insufficient data"
            elif sig.get("noise"):
                status = "🔇 noise → overridden to stable"
            else:
                status = "✅ validated"
            print(fmt.format(name, f"{sig['latest']:.4f}", trend, status))

    _print_validation("MY PRODUCT", validated_my)
    _print_validation("COMPETITOR", validated_comp)
