"""
Alert Gate
Takes the opportunity engine result and classifies it into a final actionable alert.

Alert Levels
------------
'red'    — confidence >= 0.8 AND is_opportunity True  → Strike Now
'yellow' — confidence >= 0.6 AND is_opportunity True  → Watch Closely
'green'  — is_opportunity False                        → Market Stable
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from opportunity_engine.opportunity_engine import closed_loop_opportunity


def generate_alert(opportunity_result: dict) -> dict:
    """
    Classify an opportunity result into a final alert dict.

    Parameters
    ----------
    opportunity_result : dict
        Output from closed_loop_opportunity().

    Returns
    -------
    {
        alert_level         : str   — 'red' | 'yellow' | 'green'
        alert_title         : str
        alert_message       : str   — recommended_action passed through as-is
        conditions_summary  : str   — e.g. '4 of 5 signals converging'
        confidence_pct      : int   — e.g. 80
    }
    """
    is_opp     = opportunity_result["is_opportunity"]
    confidence = opportunity_result["confidence"]
    conditions_met = opportunity_result["conditions_met"]

    # ── Alert level ───────────────────────────────────────────────────────────
    if is_opp and confidence >= 0.8:
        alert_level = "red"
        alert_title = "Strike Now — High Confidence Opportunity Detected"
    elif is_opp and confidence >= 0.6:
        alert_level = "yellow"
        alert_title = "Watch Closely — Opportunity Window Opening"
    else:
        alert_level = "green"
        alert_title = "Market Stable — Continue Monitoring"

    return {
        "alert_level":        alert_level,
        "alert_title":        alert_title,
        "alert_message":      opportunity_result["recommended_action"],
        "conditions_summary": f"{conditions_met} of 5 signals converging",
        "confidence_pct":     int(confidence * 100),
    }


def run_alert_pipeline() -> tuple[dict, dict]:
    """
    Run the full pipeline: opportunity engine → alert gate.

    Returns
    -------
    (opportunity_result, alert)
    """
    opportunity_result = closed_loop_opportunity()
    alert = generate_alert(opportunity_result)
    return opportunity_result, alert


# ── Test print ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    opp, alert = run_alert_pipeline()

    LEVEL_STYLE = {
        "red":    ("🔴", "─" * 58),
        "yellow": ("🟡", "─" * 58),
        "green":  ("🟢", "─" * 58),
    }
    icon, divider = LEVEL_STYLE[alert["alert_level"]]

    print("\n" + "=" * 60)
    print(f"  SELLERMIRROR — ALERT GATE OUTPUT")
    print("=" * 60)
    print(f"\n  {icon}  Alert Level   : {alert['alert_level'].upper()}")
    print(f"  📌 Title        : {alert['alert_title']}")
    print(f"  📊 Signals      : {alert['conditions_summary']}")
    print(f"  🎯 Confidence   : {alert['confidence_pct']}%")
    print(f"\n  📋 Recommended Action")
    print(f"  {divider}")
    for i, part in enumerate(alert["alert_message"].split(" | "), 1):
        print(f"  {i}. {part}")
    print("\n" + "=" * 60)
