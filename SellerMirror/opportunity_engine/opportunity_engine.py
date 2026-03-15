"""
Opportunity Engine — Closed-Loop Opportunity Detection
Checks 5 conditions across my product and competitor signals.
An opportunity window opens when 3+ conditions are met.

Conditions
----------
1. My sentiment improving          — my sentiment_score trend == 'improving'
2. Competitor sentiment worsening  — comp sentiment_score trend == 'worsening'
3. Competitor price drop streak    — price_drop_streak_days >= 5 (from momentum_shift)
4. Competitor price velocity drop  — comp price_velocity weekly mean < -0.5
5. My ghost rate stable/improving  — my ghost_rate trend in ('improving', 'stable')

Confidence = conditions_met / 5
is_opportunity = conditions_met >= 3
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trend_validator.trend_validator import validate_both
from scoring.scorer import compute_scores
from analytics.analytics import run_comparison


def closed_loop_opportunity() -> dict:
    """
    Evaluate all 5 opportunity conditions and return a full opportunity report.

    Returns
    -------
    {
        is_opportunity    : bool    — True if conditions_met >= 3
        conditions_met    : int     — count of True conditions (0-5)
        conditions        : dict    — {condition_name: bool} for all 5
        confidence        : float   — conditions_met / 5, rounded to 2dp
        recommended_action: str     — composite action string from fired conditions
    }
    """
    # ── Load all data ─────────────────────────────────────────────────────────
    validated_my, validated_comp = validate_both()
    scores = compute_scores()
    cm_result, tg_result, ms_result = run_comparison()

    # ── Evaluate 5 conditions ─────────────────────────────────────────────────

    # Condition 1 — My sentiment improving
    c1 = validated_my.get("sentiment_score", {}).get("trend") == "improving"

    # Condition 2 — Competitor sentiment worsening
    c2 = validated_comp.get("sentiment_score", {}).get("trend") == "worsening"

    # Condition 3 — Competitor price drop streak >= 5 consecutive days
    c3 = ms_result.get("price_drop_streak_days", 0) >= 5

    # Condition 4 — Competitor price velocity weekly mean < -0.5
    price_weekly = validated_comp.get("price_velocity", {}).get("weekly")
    if price_weekly is not None and not price_weekly.dropna().empty:
        c4 = float(price_weekly.dropna().mean()) < -0.5
    else:
        c4 = False

    # Condition 5 — My ghost rate stable or improving
    c5 = validated_my.get("ghost_rate", {}).get("trend") in ("improving", "stable")

    conditions = {
        "my_sentiment_improving":        c1,
        "comp_sentiment_worsening":      c2,
        "comp_price_drop_streak_5plus":  c3,
        "comp_price_velocity_dropping":  c4,
        "my_ghost_rate_stable_or_better":c5,
    }

    conditions_met = sum(conditions.values())
    confidence     = round(conditions_met / 5, 2)
    is_opportunity = conditions_met >= 3

    # ── Generate recommended action ───────────────────────────────────────────
    action_parts = []

    if c1 and c2:
        action_parts.append(
            "Launch a quality-focused campaign — your sentiment is rising while "
            "competitor reviews are souring."
        )
    if c4:
        action_parts.append(
            "Competitor is panic-discounting, hold your price — their price drop "
            "signals desperation, not strategy."
        )
    if c5:
        action_parts.append(
            "Your listing improvements are working, push visibility now — ghost "
            "rate is stable/improving, conversion should follow."
        )

    if not action_parts:
        recommended_action = (
            "No strong opportunity yet — monitor signals and wait for further "
            "competitor deterioration."
        )
    else:
        recommended_action = " | ".join(action_parts)

    return {
        "is_opportunity":     is_opportunity,
        "conditions_met":     conditions_met,
        "conditions":         conditions,
        "confidence":         confidence,
        "recommended_action": recommended_action,
        # Pass-through context for downstream use
        "_scores":            scores,
        "_trust_gap":         tg_result,
        "_momentum":          ms_result,
    }


# ── Test print ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    result = closed_loop_opportunity()

    COND_LABELS = {
        "my_sentiment_improving":        "My sentiment improving",
        "comp_sentiment_worsening":      "Comp sentiment worsening",
        "comp_price_drop_streak_5plus":  "Comp price drop streak ≥5d",
        "comp_price_velocity_dropping":  "Comp price velocity < -0.5",
        "my_ghost_rate_stable_or_better":"My ghost rate stable/improving",
    }

    print("\n" + "=" * 60)
    print("  OPPORTUNITY ENGINE — Closed-Loop Assessment")
    print("=" * 60)

    print(f"\n  {'Condition':<36}  Status")
    print("  " + "-" * 50)
    for key, label in COND_LABELS.items():
        val = result["conditions"][key]
        icon = "✅" if val else "❌"
        print(f"  {label:<36}  {icon} {'True' if val else 'False'}")

    print(f"\n  Conditions Met  : {result['conditions_met']} / 5")
    print(f"  Confidence      : {result['confidence'] * 100:.0f}%")

    opp_str = "🟢 OPEN" if result["is_opportunity"] else "🔴 NOT OPEN"
    print(f"  Opportunity     : {opp_str}")

    print(f"\n  📋 Recommended Action")
    print(f"  {'─' * 56}")
    # Word-wrap at 56 chars
    words = result["recommended_action"].split(" | ")
    for i, part in enumerate(words, 1):
        print(f"  {i}. {part}")

    print("\n" + "=" * 60)
