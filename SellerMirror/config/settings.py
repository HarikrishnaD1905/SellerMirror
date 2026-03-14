"""
SellerMirror Configuration
"""

# ── Alert Gate ────────────────────────────────────────────────────────────────
ALERT_THRESHOLD = 3           # Number of conditions required to fire
SPIKE_THRESHOLD = 2.0         # Z-score cutoff to filter single spikes
MIN_TREND_DAYS = 5            # Minimum days to validate a trend

# ── Scoring ───────────────────────────────────────────────────────────────────
VULNERABILITY_THRESHOLD = 50  # Minimum score to flag competitor as vulnerable

# ── Signal Weights (Health Score) ─────────────────────────────────────────────
HEALTH_WEIGHTS = {
    "ghost_rate": 0.25,
    "cart_abandon_rate": 0.25,
    "qa_gap": 0.15,
    "three_star_rate": 0.15,
    "return_rate": 0.20,
}

# ── Data Paths ────────────────────────────────────────────────────────────────
RAW_DATA_DIR = "data/raw"
PROCESSED_DATA_DIR = "data/processed"
MOCK_DATA_DIR = "data/mock"
