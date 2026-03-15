"""
SellerMirror — Streamlit Dashboard
All insights unified · One screen · Seller takes final action
"""

import sys
from pathlib import Path

# Add project root so all package imports resolve
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st  # type: ignore
import pandas as pd  # type: ignore
import numpy as np  # type: ignore
import plotly.graph_objects as go  # type: ignore
from datetime import datetime

from alerts.alert_gate import run_alert_pipeline  # type: ignore
from analytics.analytics import run_comparison  # type: ignore
from scoring.scorer import compute_scores  # type: ignore
from ingestion.product_data_loader import load_product_data  # type: ignore
from ingestion.competitor_data_loader import load_competitor_data  # type: ignore
from agents.strategy_agent import ask_agent, generate_market_report  # type: ignore

# ── Page config (must be the first Streamlit command) ────────────────────────
st.set_page_config(layout="wide", page_title="SellerMirror", page_icon="🪞")


# ── Cached pipeline ──────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def run_full_pipeline():
    """
    Run every back-end pipeline once and return all results.
    Cached for 5 min so the dashboard stays snappy on re-renders.
    """
    try:
        scores = compute_scores()                          # {'health', 'vulnerability'}
        cm, tg, ms = run_comparison()                      # complaint_mirror, trust_gap, momentum
        opp, alert = run_alert_pipeline()                  # opportunity, alert
        my_reviews, my_metrics = load_product_data()
        comp_reviews, comp_metrics = load_competitor_data()

        return {
            "scores": scores,
            "cm": cm,
            "tg": tg,
            "ms": ms,
            "opp": opp,
            "alert": alert,
            "my_reviews": my_reviews,
            "my_metrics": my_metrics,
            "comp_reviews": comp_reviews,
            "comp_metrics": comp_metrics,
        }
    except Exception as exc:
        return {"error": str(exc)}


# ── Styling ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

  html, body, [class*="css"] {
      font-family: 'Inter', sans-serif;
  }

  /* ── Alert banner ───────────────────────────────────────────── */
  .alert-banner {
      border-radius: 12px;
      padding: 20px 28px;
      margin-bottom: 20px;
      color: #fff;
  }
  .alert-banner h3 { margin: 0 0 8px 0; font-size: 1.25rem; }
  .alert-banner .conditions { opacity: 0.9; font-size: 0.92rem; margin-bottom: 6px; }
  .alert-banner .confidence { font-weight: 700; font-size: 1.1rem; margin-bottom: 10px; }
  .alert-banner ol { margin: 0; padding-left: 20px; }
  .alert-banner li { margin-bottom: 4px; font-size: 0.93rem; }

  /* ── Comparison cards ───────────────────────────────────────── */
  .comp-card {
      background: linear-gradient(135deg, #1a1d2e 0%, #20243a 100%);
      border: 1px solid #30364a;
      border-radius: 12px;
      padding: 20px;
      height: 100%;
  }
  .comp-card h4 {
      margin: 0 0 12px 0;
      font-size: 1.05rem;
      color: #e0e0e0;
  }
  .tag {
      display: inline-block;
      padding: 3px 10px;
      border-radius: 6px;
      font-size: 0.82rem;
      font-weight: 600;
      margin: 2px 4px 2px 0;
  }
  .tag-green  { background: #143d24; color: #00cc66; border: 1px solid #00cc66; }
  .tag-red    { background: #3d1a1a; color: #ff4444; border: 1px solid #ff4444; }
  .tag-yellow { background: #3d2f1a; color: #ffaa00; border: 1px solid #ffaa00; }
  .tag-teal   { background: #0d3b3b; color: #2dd4bf; border: 1px solid #2dd4bf; }
  .tag-coral  { background: #3d1a1a; color: #f87171; border: 1px solid #f87171; }
  .tag-blue   { background: #1a2a3d; color: #60a5fa; border: 1px solid #60a5fa; }

  .kv-row { display: flex; justify-content: space-between; padding: 4px 0; font-size: 0.9rem; }
  .kv-label { color: #9ca3af; }
  .kv-value { color: #e5e7eb; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# ── Run pipeline ──────────────────────────────────────────────────────────────
data = run_full_pipeline()

if "error" in data:
    st.error(f"🚨 Pipeline failed: {data['error']}")
    st.stop()

# Unpack
scores      = data["scores"]
cm          = data["cm"]
tg          = data["tg"]
ms          = data["ms"]
opp         = data["opp"]
alert       = data["alert"]
my_reviews  = data["my_reviews"]
my_metrics  = data["my_metrics"]
comp_reviews = data["comp_reviews"]
comp_metrics = data["comp_metrics"]

# Pre-build dictionary for the AI agent
pipeline_output = {
    'scores': scores,
    'comparison': {'complaint_mirror': cm, 'trust_gap': tg, 'momentum': ms},
    'alert': alert
}

# ══════════════════════════════════════════════════════════════════════════════
# HERO HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div style="padding: 10px 0 30px 0;">
    <h1 style="margin-bottom: 0px; font-weight: 700; font-size: 2.8rem;">
        <span style="color: #60a5fa;">🪞 Seller</span>Mirror
    </h1>
    <p style="color: #9ca3af; font-size: 1.1rem; margin-top: 5px;">
        Competitive Intelligence Platform · {datetime.now().strftime('%B %d, %Y')}
    </p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Alert Banner (full width)
# ══════════════════════════════════════════════════════════════════════════════

LEVEL_COLORS = {"red": "#ff4444", "yellow": "#ffaa00", "green": "#00cc66"}
bg_color = LEVEL_COLORS.get(alert["alert_level"], "#00cc66")

# Parse recommended actions (separated by " | ")
actions_list = alert["alert_message"].split(" | ")
actions_html = "".join(f"<li>{a.strip()}</li>" for a in actions_list)

st.markdown(f"""
<div class="alert-banner" style="background:{bg_color}22; border: 2px solid {bg_color};">
    <h3 style="color:{bg_color};">
        {"🔴" if alert["alert_level"] == "red" else "🟡" if alert["alert_level"] == "yellow" else "🟢"}
        &nbsp;{alert["alert_title"]}
    </h3>
    <div class="conditions">{alert["conditions_summary"]}</div>
    <div class="confidence">Confidence: {alert["confidence_pct"]}%</div>
    <ol>{actions_html}</ol>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Scores (two columns with Plotly gauge charts)
# ══════════════════════════════════════════════════════════════════════════════

col_h, col_v = st.columns(2)

# ── Health gauge ─────────────────────────────────────────────────────────────
with col_h:
    h = int(scores["health"]) if "health" in scores else 0
    if h > 60:
        gauge_color = "#00cc66"
    elif h > 40:
        gauge_color = "#ffaa00"
    else:
        gauge_color = "#ff4444"

    fig_h = go.Figure(go.Indicator(
        mode="gauge+number",
        value=h,
        title={"text": "My Health Score", "font": {"size": 18, "color": "#e5e7eb"}},
        number={"suffix": "/100", "font": {"size": 32, "color": "#e5e7eb"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#555", "dtick": 20},
            "bar": {"color": gauge_color, "thickness": 0.75},
            "bgcolor": "#1e2130",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 40],  "color": "rgba(255,68,68,0.12)"},
                {"range": [40, 60], "color": "rgba(255,170,0,0.12)"},
                {"range": [60, 100], "color": "rgba(0,204,102,0.12)"},
            ],
            "threshold": {
                "line": {"color": "#fff", "width": 2},
                "thickness": 0.8,
                "value": h,
            },
        },
    ))
    fig_h.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#e5e7eb"}, height=280,
        margin=dict(l=30, r=30, t=60, b=20),
    )
    st.plotly_chart(fig_h, use_container_width=True)

# ── Vulnerability gauge ──────────────────────────────────────────────────────
with col_v:
    v = int(scores["vulnerability"]) if "vulnerability" in scores else 0
    # Inverted coloring: HIGH vulnerability = RED (bad for competitor = good for us)
    if v > 60:
        vgauge_color = "#ff4444"
    elif v > 40:
        vgauge_color = "#ffaa00"
    else:
        vgauge_color = "#00cc66"

    fig_v = go.Figure(go.Indicator(
        mode="gauge+number",
        value=v,
        title={"text": "Competitor Vulnerability Score", "font": {"size": 18, "color": "#e5e7eb"}},
        number={"suffix": "/100", "font": {"size": 32, "color": "#e5e7eb"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#555", "dtick": 20},
            "bar": {"color": vgauge_color, "thickness": 0.75},
            "bgcolor": "#1e2130",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 40],  "color": "rgba(0,204,102,0.12)"},
                {"range": [40, 60], "color": "rgba(255,170,0,0.12)"},
                {"range": [60, 100], "color": "rgba(255,68,68,0.12)"},
            ],
            "threshold": {
                "line": {"color": "#fff", "width": 2},
                "thickness": 0.8,
                "value": v,
            },
        },
    ))
    fig_v.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#e5e7eb"}, height=280,
        margin=dict(l=30, r=30, t=60, b=20),
    )
    st.plotly_chart(fig_v, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2.5 — Core Metrics (Full Width Row)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
col_m1, col_m2, col_m3, col_m4 = st.columns(4)

# Calculate latest metrics
latest_my = my_metrics.iloc[-1]
latest_comp = comp_metrics.iloc[-1]

prev_my = my_metrics.iloc[-2] if len(my_metrics) > 1 else latest_my
prev_comp = comp_metrics.iloc[-2] if len(comp_metrics) > 1 else latest_comp

my_conv = (latest_my['daily_purchases'] / latest_my['daily_views']) * 100 if latest_my['daily_views'] else 0
prev_my_conv = (prev_my['daily_purchases'] / prev_my['daily_views']) * 100 if prev_my['daily_views'] else 0
my_conv_delta = my_conv - prev_my_conv

comp_conv = (latest_comp['daily_purchases'] / latest_comp['daily_views']) * 100 if latest_comp['daily_views'] else 0
prev_comp_conv = (prev_comp['daily_purchases'] / prev_comp['daily_views']) * 100 if prev_comp['daily_views'] else 0
comp_conv_delta = comp_conv - prev_comp_conv

with col_m1:
    st.metric(
        label="My Conversion Rate", 
        value=f"{my_conv:.1f}%", 
        delta=f"{my_conv_delta:.1f}% vs yesterday"
    )

with col_m2:
    st.metric(
        label="Competitor Conversion Rate", 
        value=f"{comp_conv:.1f}%", 
        delta=f"{comp_conv_delta:.1f}% vs yesterday",
        delta_color="inverse"
    )

with col_m3:
    returns_delta = int(latest_my['returns'] - prev_my['returns'])
    st.metric(
        label="My Daily Returns", 
        value=int(latest_my['returns']), 
        delta=f"{returns_delta} vs yesterday",
        delta_color="inverse"
    )

with col_m4:
    comp_returns_delta = int(latest_comp['returns'] - prev_comp['returns'])
    st.metric(
        label="Competitor Daily Returns", 
        value=int(latest_comp['returns']), 
        delta=f"{comp_returns_delta} vs yesterday",
        delta_color="inverse"
    )


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Three comparison cards  (three columns)
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.subheader("⚔️ Competitive Breakdown")
col_cm, col_tg, col_ms = st.columns(3)

# ── Card 1: Complaint Matchup ────────────────────────────────────────────────
with col_cm:
    shared = cm.get("shared_categories", [])
    if not shared:
        my_counts = cm.get("my_complaint_counts", {})
        comp_counts = cm.get("comp_complaint_counts", {})
        
        my_list = "".join(f"<div class='kv-row'><span class='kv-label'>{k}</span><span class='kv-value'>{v}</span></div>" for k, v in my_counts.items())
        comp_list = "".join(f"<div class='kv-row'><span class='kv-label'>{k}</span><span class='kv-value'>{v}</span></div>" for k, v in comp_counts.items())
        
        st.markdown(f"""
        <div class="comp-card">
            <h4>📋 Complaint Matchup</h4>
            <div style="font-size: 0.85rem; color: #9ca3af; margin-bottom: 12px; line-height: 1.4;">
                No shared complaint categories — you and competitor are failing in different areas.
            </div>
            <div style="margin-bottom: 12px;">
                <div style="color: #e5e7eb; font-weight: 600; margin-bottom: 4px; font-size: 0.9rem;">Your complaints</div>
                {my_list if my_list else "<span style='color:#9ca3af; font-size:0.85rem;'>None</span>"}
            </div>
            <div>
                <div style="color: #e5e7eb; font-weight: 600; margin-bottom: 4px; font-size: 0.9rem;">Their complaints</div>
                {comp_list if comp_list else "<span style='color:#9ca3af; font-size:0.85rem;'>None</span>"}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        my_wins   = [c for c, w in cm["winner_per_category"].items() if w == "my_product"]
        comp_wins = [c for c, w in cm["winner_per_category"].items() if w == "competitor"]
    
        my_tags   = "".join(f'<span class="tag tag-green">{c}</span>' for c in my_wins) if my_wins else '<span class="tag tag-blue">—</span>'
        comp_tags = "".join(f'<span class="tag tag-red">{c}</span>' for c in comp_wins) if comp_wins else '<span class="tag tag-blue">—</span>'
    
        st.markdown(f"""
        <div class="comp-card">
            <h4>📋 Complaint Matchup</h4>
            <div class="kv-row">
                <span class="kv-label">My Wins</span>
            </div>
            <div style="margin-bottom:8px;">{my_tags}</div>
            <div class="kv-row">
                <span class="kv-label">Competitor Wins</span>
            </div>
            <div>{comp_tags}</div>
        </div>
        """, unsafe_allow_html=True)

# ── Card 2: Trust Gap Race ──────────────────────────────────────────────────
with col_tg:
    winner_map = {
        "my_product": ("🏆 My Product", "tag-green"),
        "competitor": ("💀 Competitor", "tag-red"),
        "neutral":    ("➡️ Neutral",    "tag-yellow"),
    }
    winner_label, winner_tag_cls = winner_map.get(tg["winner"], ("—", "tag-blue"))

    rr = tg["my_repeat_rate"]
    rv = tg["comp_rating_vel_mean"]
    rr_str = f"{rr:.0%}" if rr is not None else "N/A"
    if rv is None:
        rv_str = "N/A"
    elif rv > 0:
        rv_str = f"Rising (+{rv:.1f}★/wk)"
    elif rv < 0:
        rv_str = f"Dropping ({rv:.1f}★/wk)"
    else:
        rv_str = "Stable"

    st.markdown(f"""
    <div class="comp-card">
        <h4>🤝 Customer Trust</h4>
        <div class="kv-row">
            <span class="kv-label">Winner</span>
            <span class="tag {winner_tag_cls}">{winner_label}</span>
        </div>
        <div class="kv-row">
            <span class="kv-label">Repeat Customers</span>
            <span class="kv-value">{rr_str}</span>
        </div>
        <div class="kv-row">
            <span class="kv-label">Rating Trend</span>
            <span class="kv-value">{rv_str}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Card 3: Momentum Shift ──────────────────────────────────────────────────
with col_ms:
    if ms["momentum_lost"]:
        m_label, m_cls = "🔴 LOST", "tag-red"
    elif ms["partial"]:
        m_label, m_cls = "🟡 PARTIAL", "tag-yellow"
    else:
        m_label, m_cls = "🟢 HOLDING", "tag-green"

    st.markdown(f"""
    <div class="comp-card">
        <h4>📉 Momentum</h4>
        <div class="kv-row">
            <span class="kv-label">Status</span>
            <span class="tag {m_cls}">{m_label}</span>
        </div>
        <div class="kv-row">
            <span class="kv-label">Price Drop Days</span>
            <span class="kv-value">{ms["price_drop_streak_days"]} days</span>
        </div>
        <div class="kv-row">
            <span class="kv-label">Fewer Reviews?</span>
            <span class="kv-value">{"Yes" if ms["review_volume_decline"] else "No"}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3.5 — Traffic vs Sales (Full Width)
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.subheader("🚦 Ghost Rate — Traffic vs Conversion")

fig_funnel = go.Figure()

# Add My Product Views
fig_funnel.add_trace(go.Scatter(
    x=my_metrics["date"], y=my_metrics["daily_views"],
    mode="lines", name="My Page Views",
    line={"color": "rgba(45, 212, 191, 0.4)", "width": 2},
    fill="tozeroy", fillcolor="rgba(45, 212, 191, 0.1)",
))

# Add My Product Purchases
fig_funnel.add_trace(go.Scatter(
    x=my_metrics["date"], y=my_metrics["daily_purchases"],
    mode="lines", name="My Purchases",
    line={"color": "#2dd4bf", "width": 3},
    fill="tozeroy", fillcolor="rgba(45, 212, 191, 0.3)",
))

# Add Competitor Views
fig_funnel.add_trace(go.Scatter(
    x=comp_metrics["date"], y=comp_metrics["daily_views"],
    mode="lines", name="Comp Page Views",
    line={"color": "rgba(248, 113, 113, 0.4)", "width": 2, "dash": "dash"},
))

# Add Competitor Purchases
fig_funnel.add_trace(go.Scatter(
    x=comp_metrics["date"], y=comp_metrics["daily_purchases"],
    mode="lines", name="Comp Purchases",
    line={"color": "#f87171", "width": 2, "dash": "dash"},
))

fig_funnel.update_layout(
    template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    height=350, margin={"l": 0, "r": 0, "t": 10, "b": 0},
    xaxis={"showgrid": False},
    yaxis={"title": "Daily Count", "showgrid": True, "gridcolor": "rgba(255,255,255,0.06)"},
    legend={"orientation": "h", "yanchor": "bottom", "y": 1.02},
    hovermode="x unified"
)
st.plotly_chart(fig_funnel, use_container_width=True)

st.markdown("""
<div style="font-size: 0.9rem; color: #9ca3af; margin-top: -15px; margin-bottom: 30px;">
    <strong>Why this matters:</strong> A big gap between Page Views and Purchases is your "Ghost Rate". If views are high but purchases drop, your listing is failing to convert traffic into sales. This chart reveals immediately when customers are abandoning your page.
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — 90-day price chart  (full width)
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.subheader("💰 Competitor Price — 90-Day Trend")

comp_prices = comp_metrics[["date", "price"]].copy().sort_values("date")
n_days = len(comp_prices)

fig_price = go.Figure()
fig_price.add_trace(go.Scatter(
    x=comp_prices["date"],
    y=comp_prices["price"],
    mode="lines",
    name="Competitor Price",
    line={"color": "#f87171", "width": 3, "shape": "spline"},
    fill="tozeroy",
    fillcolor="rgba(248,113,113,0.05)",
))

# Alert-fired line at day 66 (or proportional if fewer days)
alert_day_idx = min(65, n_days - 1)  # 0-indexed day 66
alert_date = str(comp_prices.iloc[alert_day_idx]["date"]).split()[0]  # ISO string

# Opportunity Phase Highlighting
fig_price.add_vrect(
    x0=alert_date, x1=comp_prices["date"].max(),
    fillcolor="rgba(0, 204, 102, 0.1)", opacity=0.5,
    layer="below", line_width=0,
)

fig_price.add_shape(
    type="line", x0=alert_date, x1=alert_date, y0=0, y1=1,
    yref="paper", line={"color": "#00cc66", "width": 2},
)

mid_idx  = min(alert_day_idx + (n_days - alert_day_idx) // 2, n_days - 1)
mid_date  = str(comp_prices.iloc[mid_idx]["date"]).split()[0]  # ISO string
mid_price = float(comp_prices["price"].iloc[alert_day_idx:].mean())

fig_price.add_annotation(
    x=mid_date, y=mid_price,
    text="Opportunity Window<br><span style='font-size:10px;'>(Hold Your Price)</span>",
    showarrow=True, arrowhead=2, arrowcolor="#00cc66", ax=0, ay=-40,
    font={"size": 13, "color": "#00cc66", "family": "Inter"},
    bordercolor="#00cc66", borderwidth=1, borderpad=6, bgcolor="rgba(0,0,0,0.8)",
)

fig_price.update_layout(
    template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    height=320, margin={"l": 0, "r": 0, "t": 10, "b": 0},
    xaxis={"showgrid": False},
    yaxis={"title": "Price (₹)", "showgrid": True, "gridcolor": "rgba(255,255,255,0.04)"},
    legend={"orientation": "h", "yanchor": "bottom", "y": 1.02},
    hovermode="x unified"
)
st.plotly_chart(fig_price, use_container_width=True)

st.markdown("""
<div style="font-size: 0.9rem; color: #9ca3af; margin-top: -15px; margin-bottom: 30px;">
    <strong>Why this matters:</strong> This chart tracks the competitor's 90-day pricing strategy. Consecutive price drops often signal panic discounting or excess inventory, creating a high-margin opportunity window for you to hold your price and capture their lost trust.
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — 90-day review sentiment trend  (full width)
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.subheader("💬 Review Sentiment & Complaints")

col_sent, col_ret = st.columns([1.2, 1])

with col_sent:
    # Simple keyword-based sentiment proxy: count positive vs negative keywords per week
    POS_WORDS = {"great", "happy", "good", "excellent", "love", "perfect", "sturdy",
                 "fast", "best", "amazing", "solid", "recommend", "improved", "premium",
                 "neat", "fantastic", "accurate", "nice", "clear", "loud", "bass"}
    NEG_WORDS = {"broke", "poor", "cheap", "disappointed", "delayed", "misleading",
                 "returned", "bad", "worst", "avoid", "complaint", "inconsistent",
                 "dropped", "declined", "loose", "unclear", "different", "issue", "faulty", "stops"}


    def _weekly_sentiment(reviews_df: pd.DataFrame) -> pd.DataFrame:
        """Compute a weekly sentiment score in [-1, +1] from review text."""
        df = reviews_df[["date", "review_text"]].copy()
        df["date"] = pd.to_datetime(df["date"])
        df["week"] = df["date"].dt.to_period("W").dt.start_time

        def _score(text: str) -> float:
            words = set(str(text).lower().split())
            pos = len(words & POS_WORDS)
            neg = len(words & NEG_WORDS)
            total = pos + neg
            return (pos - neg) / total if total else 0.0

        df["sentiment"] = df["review_text"].apply(_score)
        weekly = df.groupby("week")["sentiment"].mean().reset_index()
        weekly.columns = ["week", "sentiment"]
        return weekly


    my_sent  = _weekly_sentiment(my_reviews)
    comp_sent = _weekly_sentiment(comp_reviews)

    fig_sent = go.Figure()
    
    # Positive/Negative background zones
    fig_sent.add_hrect(y0=0, y1=1, fillcolor="rgba(0, 204, 102, 0.05)", line_width=0, layer="below")
    fig_sent.add_hrect(y0=-1, y1=0, fillcolor="rgba(255, 68, 68, 0.05)", line_width=0, layer="below")
    fig_sent.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.2)")

    fig_sent.add_trace(go.Scatter(
        x=my_sent["week"], y=my_sent["sentiment"],
        mode="lines", name="My Product",
        line={"color": "#2dd4bf", "width": 3, "shape": "spline"},
    ))
    fig_sent.add_trace(go.Scatter(
        x=comp_sent["week"], y=comp_sent["sentiment"],
        mode="lines", name="Competitor",
        line={"color": "#f87171", "width": 3, "shape": "spline"},
    ))

    fig_sent.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=320, margin={"l": 0, "r": 0, "t": 30, "b": 0},
        xaxis={"showgrid": False},
        yaxis={"title": "Polarity (Negative → Positive)", "showgrid": False, "range": [-1, 1],
               "tickvals": [-0.8, 0, 0.8], "ticktext": ["😡 Negative", "Neutral", "😊 Positive"]},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.05},
        hovermode="x unified"
    )
    st.markdown('<div style="font-weight:600; font-size: 0.95rem; color:#e0e0e0; margin-bottom: 5px;">Weekly Sentiment Polarity</div>', unsafe_allow_html=True)
    st.plotly_chart(fig_sent, use_container_width=True)

with col_ret:
    st.markdown('<div style="font-weight:600; font-size: 0.95rem; color:#e0e0e0; margin-bottom: 5px;">Daily Returns Comparison</div>', unsafe_allow_html=True)
    
    fig_ret = go.Figure()
    
    fig_ret.add_trace(go.Bar(
        x=my_metrics["date"], y=my_metrics["returns"],
        name="My Returns", marker_color="rgba(45, 212, 191, 0.8)"
    ))
    
    fig_ret.add_trace(go.Bar(
        x=comp_metrics["date"], y=comp_metrics["returns"],
        name="Comp Returns", marker_color="rgba(248, 113, 113, 0.8)"
    ))
    
    fig_ret.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=320, margin={"l": 0, "r": 0, "t": 30, "b": 0},
        barmode="group",
        xaxis={"showgrid": False},
        yaxis={"title": "Units Returned", "showgrid": True, "gridcolor": "rgba(255,255,255,0.04)"},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.05},
        hovermode="x unified"
    )
    st.plotly_chart(fig_ret, use_container_width=True)

st.markdown("""
<div style="font-size: 0.9rem; color: #9ca3af; margin-top: -15px; margin-bottom: 30px;">
    <strong>Why this matters:</strong> Polarity shows exactly when negative review keywords outweigh positive ones. The bar chart pairs this with actual Daily Returns. If the competitor's sentiment crashes into the red zone and returns spike, they are dealing with a severe quality or fulfillment crisis.
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — Sidebar
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 🪞 SellerMirror")
    st.markdown("---")

    # Dynamically extract Product ID from reviews
    display_product_id = my_reviews["product_id"].iloc[0] if "product_id" in my_reviews.columns and not my_reviews.empty else "UNKNOWN_PRODUCT"
    st.markdown(f"**Product** &nbsp; `{display_product_id}`")

    # Date range from metrics
    date_min = my_metrics["date"].min().strftime("%Y-%m-%d")
    date_max = my_metrics["date"].max().strftime("%Y-%m-%d")
    st.markdown(f"**Date Range** &nbsp; {date_min} → {date_max}")

    st.markdown("---")
    
    st.markdown("### 🏗️ Pipeline Flow")
    st.markdown(f"""
    <div style="font-size: 0.85rem; padding: 10px; background: rgba(0,0,0,0.2); border-radius: 8px; border: 1px solid #30364a;">
        <div style="color: #60a5fa; font-weight: 600;">1. Data Ingestion</div>
        <div style="color: #9ca3af; margin-left: 12px;">↳ Reviews & Core Metrics</div>
        <div style="color: #2dd4bf; font-weight: 600; margin-top: 8px;">2. Trend Validation</div>
        <div style="color: #9ca3af; margin-left: 12px;">↳ Filter noise & spikes</div>
        <div style="color: #f87171; font-weight: 600; margin-top: 8px;">3. Scoring Engine</div>
        <div style="color: #9ca3af; margin-left: 12px;">↳ Health & Vulnerability</div>
        <div style="color: #a78bfa; font-weight: 600; margin-top: 8px;">4. AI Analytics</div>
        <div style="color: #9ca3af; margin-left: 12px;">↳ Complaint Classification</div>
        <div style="color: #fbbf24; font-weight: 600; margin-top: 8px;">5. Alert Gate</div>
        <div style="color: #9ca3af; margin-left: 12px;">↳ Multi-signal evaluation</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")

    if st.button("🔄 Rerun Analysis", use_container_width=True):
        st.rerun()

    st.markdown("---")
    st.caption("SellerMirror · Built with Streamlit + Plotly")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — AI Strategy Agent
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.header("🤖 Ask Your Strategy Agent")

# Auto-generated report
with st.spinner("Generating AI market analysis..."):
    # Generate report only on first load using session state to save tokens (or re-run on button)
    if "ai_report" not in st.session_state:
        try:
            st.session_state.ai_report = generate_market_report(pipeline_output)
        except Exception as e:
            st.error('Agent unavailable — check API key')
            st.write(e)
            st.session_state.ai_report = "Analysis failed to load."
    
st.markdown(f"""
<div class="comp-card" style="margin-bottom: 25px; border-left: 4px solid #60a5fa; padding: 25px;">
    {st.session_state.ai_report}
</div>
""", unsafe_allow_html=True)

# Example question buttons
st.markdown("**Quick questions:**")
col1, col2, col3 = st.columns(3)
quick_q = None
with col1:
    if st.button("Should I run a discount now?"):
        quick_q = "Should I run a discount now?"
with col2:
    if st.button("Why is my competitor declining?"):
        quick_q = "Why is my competitor declining?"
with col3:
    if st.button("What should I fix first?"):
        quick_q = "What should I fix first?"

if quick_q:
    with st.spinner("Agent thinking..."):
        answer = ask_agent(quick_q, pipeline_output)
    with st.chat_message("user"):
        st.markdown(quick_q)
    with st.chat_message("assistant"):
        st.markdown(answer)

# Free chat
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_q := st.chat_input("Ask anything about your market position..."):
    st.session_state.chat_history.append({"role": "user", "content": user_q})
    
    # Render user message right away
    with st.chat_message("user"):
        st.markdown(user_q)
    
    with st.spinner("Agent thinking..."):
        agent_reply = ask_agent(user_q, pipeline_output)
        
    st.session_state.chat_history.append({"role": "assistant", "content": agent_reply})
    st.rerun()
