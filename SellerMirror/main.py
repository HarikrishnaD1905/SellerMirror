"""
SellerMirror — Main Pipeline
Run the full pipeline end-to-end and print a clean summary report.

Usage:
    python main.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from ingestion.product_data_loader   import load_product_data
from ingestion.competitor_data_loader import load_competitor_data
from trend_validator.trend_validator  import validate_both
from scoring.scorer                   import compute_scores
from analytics.analytics              import run_comparison
from alerts.alert_gate                import run_alert_pipeline
from agents.strategy_agent            import generate_market_report


def run():
    print("\n" + "█" * 62)
    print("  🪞  SELLERMIRROR — Full Pipeline")
    print("█" * 62)

    # ── Step 1: Ingestion ─────────────────────────────────────────────────────
    print("\n  [1/5] Loading data...", end=" ", flush=True)
    my_reviews,   my_metrics   = load_product_data()
    comp_reviews, comp_metrics = load_competitor_data()
    print(f"✓  ({len(my_reviews)} my reviews · {len(comp_reviews)} comp reviews · "
          f"{len(my_metrics)} my metric rows · {len(comp_metrics)} comp metric rows)")

    # ── Step 2: Trend Validation ──────────────────────────────────────────────
    print("  [2/5] Validating trends...", end=" ", flush=True)
    validated_my, validated_comp = validate_both()
    noise_my   = [k for k, v in validated_my.items()   if v.get("noise")]
    noise_comp = [k for k, v in validated_comp.items() if v.get("noise")]
    print(f"✓  (noisy signals — mine: {len(noise_my)} · comp: {len(noise_comp)})")

    # ── Step 3: Scoring ───────────────────────────────────────────────────────
    print("  [3/5] Scoring...", end=" ", flush=True)
    scores = compute_scores()
    print(f"✓")

    # ── Step 4: Analytics ─────────────────────────────────────────────────────
    print("  [4/5] Running comparisons...", end=" ", flush=True)
    cm, tg, ms = run_comparison()
    print(f"✓")

    # ── Step 5: Alert Gate ────────────────────────────────────────────────────
    print("  [5/5] Running alert gate...", end=" ", flush=True)
    opp, alert = run_alert_pipeline()
    print(f"✓\n")

    # ── Summary Report ────────────────────────────────────────────────────────
    W = 62
    print("=" * W)
    print("  SUMMARY REPORT")
    print("=" * W)

    # Scores
    h  = scores["health"]
    v  = scores["vulnerability"]
    h_bar = "█" * int(h / 100 * 20) + "░" * (20 - int(h / 100 * 20))
    v_bar = "█" * int(v / 100 * 20) + "░" * (20 - int(v / 100 * 20))
    h_label = "Healthy ✅"    if h >= 60 else ("At Risk ⚠️"  if h >= 40 else "Critical 🚨")
    v_label = "Highly Vuln 🎯" if v >= 60 else ("Moderate ⚠️" if v >= 40 else "Resilient 🛡️")

    print(f"\n  📊 SCORES")
    print(f"  {'─' * (W - 4)}")
    print(f"  My Health Score       {h_bar}  {h:>5.1f}/100  {h_label}")
    print(f"  Comp Vulnerability    {v_bar}  {v:>5.1f}/100  {v_label}")

    # Comparison
    print(f"\n  🔍 COMPARISON")
    print(f"  {'─' * (W - 4)}")

    # Complaint mirror — which categories we're winning
    my_wins   = [cat for cat, w in cm["winner_per_category"].items() if w == "my_product"]
    comp_wins = [cat for cat, w in cm["winner_per_category"].items() if w == "competitor"]
    print(f"  Complaint Mirror      My wins: {my_wins or '—'}  |  Comp wins: {comp_wins or '—'}")

    # Trust gap
    tg_winner = {"my_product": "🏆 My Product", "competitor": "💀 Competitor", "neutral": "➡️  Neutral"}
    print(f"  Trust Gap Race        Winner: {tg_winner.get(tg['winner'], tg['winner'])}")
    print(f"                        My repeat rate: {tg['my_repeat_rate']}  |  "
          f"Comp rating vel (mean): {tg['comp_rating_vel_mean']}")

    # Momentum
    m_status = "🔴 LOST" if ms["momentum_lost"] else ("🟡 PARTIAL" if ms["partial"] else "🟢 HOLDING")
    print(f"  Competitor Momentum   {m_status}  "
          f"(price streak: {ms['price_drop_streak_days']}d · "
          f"vol decline: {ms['review_volume_decline']})")

    # Alert
    LEVEL_ICON = {"red": "🔴", "yellow": "🟡", "green": "🟢"}
    icon = LEVEL_ICON.get(alert["alert_level"], "⚪")

    print(f"\n  🚨 ALERT")
    print(f"  {'─' * (W - 4)}")
    print(f"  Level                 {icon}  {alert['alert_level'].upper()}")
    print(f"  Title                 {alert['alert_title']}")
    print(f"  Signals               {alert['conditions_summary']}")
    print(f"  Confidence            {alert['confidence_pct']}%")
    print(f"\n  Recommended Actions:")
    for i, action in enumerate(alert["alert_message"].split(" | "), 1):
        # Wrap at W-6 chars
        import textwrap
        wrapped = textwrap.fill(action, width=W - 8, subsequent_indent="     ")
        print(f"  {i}. {wrapped}")

    print("\n" + "=" * W)
    print("  🤖  AI STRATEGIC ANALYSIS")
    print("=" * W)
    
    pipeline_output = {
        'scores': scores,
        'comparison': {
            'complaint_mirror': cm,
            'trust_gap': tg,
            'momentum': ms
        },
        'alert': alert
    }
    
    ai_report = generate_market_report(pipeline_output)
    print(ai_report)

    print("\n" + "=" * W)
    print("  Pipeline complete.")
    print("=" * W + "\n")


if __name__ == "__main__":
    run()
