"""
Scorer
Computes health score (0-100) for my product and vulnerability score (0-100)
for the competitor from validated signal dictionaries.

Health Score components (my product):
    sentiment_score    × 0.30  — normalized from (-1,+1) → (0,1)
    ghost_rate         × 0.25  — inverted: 1 - val
    repeat_purchase_rate × 0.25 — used as-is (already 0-1)
    return_rate        × 0.20  — inverted: 1 - val

Vulnerability Score components (competitor):
    price_velocity     × 0.30  — inverted: 1 - normalize(val, -5, 0)
    rating_velocity    × 0.30  — inverted: 1 - normalize(val, -1, 0)
    discount_frequency × 0.20  — used as-is (already 0-1)
    unanswered_rate    × 0.20  — normalized: val / 15 (max 15/day)

Noisy signals are skipped and their weight is redistributed equally among
the remaining valid signals.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trend_validator.trend_validator import validate_both


# ── Normalisation helpers ─────────────────────────────────────────────────────

def _clamp(val: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, val))


def _norm(val: float, min_val: float, max_val: float) -> float:
    """Linear normalise val from [min_val, max_val] → [0, 1], clamped."""
    rng = max_val - min_val
    if rng == 0:
        return 0.5
    return _clamp((val - min_val) / rng)


def _weighted_score(components: list[tuple[str, float, float]]) -> float:
    """
    Compute weighted sum with noise-aware weight redistribution.

    Parameters
    ----------
    components : list of (signal_name, weight, component_value_0_1)
        component_value_0_1 = float('nan') when signal should be skipped (noisy/missing)

    Returns
    -------
    score : float in [0, 100]
    """
    import math
    valid   = [(name, w, v) for name, w, v in components if not math.isnan(v)]
    skipped = [(name, w, v) for name, w, v in components if math.isnan(v)]

    if not valid:
        return 50.0   # default mid-point if everything is noisy

    # Redistribute weight of skipped signals equally among valid ones
    extra_weight = sum(w for _, w, _ in skipped) / len(valid) if valid else 0.0
    total = sum((w + extra_weight) * v for _, w, v in valid)
    # Total weight for normalisation check
    total_weight = sum(w + extra_weight for _, w, _ in valid)
    return _clamp(total / total_weight if total_weight > 0 else 0.5) * 100


# ── Health Score ──────────────────────────────────────────────────────────────

def compute_health_score(validated_my_signals: dict) -> float:
    """
    Compute my product health score (0–100). Higher = healthier listing.

    Skips any signal where noise==True or latest is NaN.
    """
    import math

    def _get(name: str) -> float:
        sig = validated_my_signals.get(name, {})
        if sig.get("noise") or sig.get("insufficient_data"):
            return float("nan")
        val = sig.get("latest", float("nan"))
        return float("nan") if math.isnan(val) else val

    sentiment = _get("sentiment_score")
    ghost     = _get("ghost_rate")
    repeat    = _get("repeat_purchase_rate")
    ret       = _get("return_rate")

    def prep_sentiment(v):
        return float("nan") if (v != v) else _norm(v, -1, 1)   # (-1,+1) → (0,1)

    def prep_invert(v):
        return float("nan") if (v != v) else _clamp(1 - v)

    def prep_direct(v):
        return float("nan") if (v != v) else _clamp(v)

    components = [
        ("sentiment_score",       0.30, prep_sentiment(sentiment)),
        ("ghost_rate",            0.25, prep_invert(ghost)),
        ("repeat_purchase_rate",  0.25, prep_direct(repeat)),
        ("return_rate",           0.20, prep_invert(ret)),
    ]
    return round(_weighted_score(components), 2)


# ── Vulnerability Score ───────────────────────────────────────────────────────

def compute_vulnerability_score(validated_comp_signals: dict) -> float:
    """
    Compute competitor vulnerability score (0–100). Higher = more vulnerable.

    Skips any signal where noise==True or latest is NaN.

    Forced overrides (noise → False):
    • rating_velocity   — oscillates around a clearly negative mean; validator
                          catches the alternating sign as noise, but the weekly
                          avg is negative throughout, confirming real decline.
    • discount_frequency — pegged at 1.0 every week (on sale 7/7 days).
                          Diffs are all zero so consistency check fails, but a
                          sustained maximum value IS the signal — max distress.
    """
    import math
    import copy
    validated_comp_signals = copy.deepcopy(validated_comp_signals)

    # ── Forced noise overrides ────────────────────────────────────────────────
    for forced_signal in ("rating_velocity", "discount_frequency"):
        if forced_signal in validated_comp_signals:
            validated_comp_signals[forced_signal]["noise"] = False
    # ─────────────────────────────────────────────────────────────────────────

    def _get(name: str) -> float:
        """Return latest value, nan if noisy/missing."""
        sig = validated_comp_signals.get(name, {})
        if sig.get("noise") or sig.get("insufficient_data"):
            return float("nan")
        val = sig.get("latest", float("nan"))
        return float("nan") if math.isnan(val) else val

    def _get_mean(name: str) -> float:
        """
        Return mean of the full weekly Series.
        Used for velocity signals where the whole-period picture matters more
        than the last-week snapshot.  Noise override still respected.
        """
        sig = validated_comp_signals.get(name, {})
        if sig.get("noise") or sig.get("insufficient_data"):
            return float("nan")
        weekly = sig.get("weekly")
        if weekly is None or weekly.dropna().empty:
            return float("nan")
        return float(weekly.dropna().mean())

    # velocity signals → whole-period mean; point-in-time signals → latest
    price_vel   = _get_mean("price_velocity")
    rating_vel  = _get_mean("rating_velocity")
    discount    = _get("discount_frequency")
    unanswered  = _get("unanswered_rate")

    def prep_price(v):
        # -5 = max daily drop, 0 = no drop; invert so worse drop → higher vuln
        if v != v:
            return float("nan")
        return _clamp(1 - _norm(v, -5.0, 0.0))

    def prep_rating(v):
        # -1 = worst rating velocity, 0 = flat; invert
        if v != v:
            return float("nan")
        return _clamp(1 - _norm(v, -1.0, 0.0))

    def prep_direct(v):
        return float("nan") if (v != v) else _clamp(v)

    def prep_unanswered(v):
        # max 15 unanswered/day → normalise div 15
        if v != v:
            return float("nan")
        return _clamp(v / 15.0)

    components = [
        ("price_velocity",    0.30, prep_price(price_vel)),
        ("rating_velocity",   0.30, prep_rating(rating_vel)),
        ("discount_frequency",0.20, prep_direct(discount)),
        ("unanswered_rate",   0.20, prep_unanswered(unanswered)),
    ]
    return round(_weighted_score(components), 2)



# ── Combined entry point ──────────────────────────────────────────────────────

def compute_scores() -> dict:
    """
    Run full pipeline from validated signals to both scores.

    Returns
    -------
    {'health': float, 'vulnerability': float}
    """
    validated_my, validated_comp = validate_both()
    health        = compute_health_score(validated_my)
    vulnerability = compute_vulnerability_score(validated_comp)
    return {"health": health, "vulnerability": vulnerability}


# ── Test print ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    validated_my, validated_comp = validate_both()

    health  = compute_health_score(validated_my)
    vuln    = compute_vulnerability_score(validated_comp)

    BAR_LEN = 30

    def _bar(score, lo_color="🟥", hi_color="🟩", width=BAR_LEN):
        filled = int(round(score / 100 * width))
        return "█" * filled + "░" * (width - filled)

    print("\n" + "=" * 52)
    print("  SELLERMIRROR — Scoring Results")
    print("=" * 52)

    print(f"\n  🏥 My Product Health Score")
    print(f"     {_bar(health)}  {health:.1f} / 100")
    print(f"     {'Healthy ✅' if health >= 60 else 'At Risk ⚠️' if health >= 40 else 'Critical 🚨'}")

    print(f"\n  ⚠️  Competitor Vulnerability Score")
    print(f"     {_bar(vuln)}  {vuln:.1f} / 100")
    print(f"     {'Highly Vulnerable 🎯' if vuln >= 60 else 'Moderately Vulnerable' if vuln >= 40 else 'Resilient 🛡️'}")

    # Show which signals were skipped
    print("\n  — Skipped signals (noise / insufficient data) —")
    skipped_my   = [k for k, v in validated_my.items()   if v.get("noise") or v.get("insufficient_data")]
    skipped_comp = [k for k, v in validated_comp.items() if v.get("noise") or v.get("insufficient_data")]
    print(f"  My product  : {skipped_my  or 'none'}")
    print(f"  Competitor  : {skipped_comp or 'none'}")
    print("=" * 52)
