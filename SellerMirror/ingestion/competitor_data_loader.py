"""
Competitor Data Loader
Loads rows where seller_id == 'competitor' from:
  - data/reviews.csv
  - data/daily_metrics.csv
Returns reviews_df and metrics_df with parsed dates.
"""

import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def load_competitor_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns
    -------
    reviews_df : DataFrame
        Columns: review_id, seller_id, product_id, review_text, rating,
                 date, verified_purchase, helpful_votes, replied_by_seller
    metrics_df : DataFrame
        Columns: seller_id, date, price, original_price, is_on_sale,
                 daily_views, daily_purchases, cart_adds, cart_completions,
                 repeat_purchases, returns, stock_available, unanswered_questions
    """
    # ── Reviews ──────────────────────────────────────────────────────────────
    reviews_df = pd.read_csv(DATA_DIR / "reviews.csv", parse_dates=["date"])
    reviews_df = reviews_df[reviews_df["seller_id"] == "competitor"].copy()
    reviews_df.sort_values("date", inplace=True)
    reviews_df.reset_index(drop=True, inplace=True)

    # ── Daily metrics ─────────────────────────────────────────────────────────
    metrics_df = pd.read_csv(DATA_DIR / "daily_metrics.csv", parse_dates=["date"])
    metrics_df = metrics_df[metrics_df["seller_id"] == "competitor"].copy()
    metrics_df.sort_values("date", inplace=True)
    metrics_df.reset_index(drop=True, inplace=True)

    return reviews_df, metrics_df


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    reviews, metrics = load_competitor_data()

    print("=== COMPETITOR — reviews_df ===")
    print(f"Shape : {reviews.shape}")
    print(f"Dates : {reviews['date'].min().date()}  →  {reviews['date'].max().date()}")
    print(f"Rating distribution:\n{reviews['rating'].value_counts().sort_index()}\n")
    print(reviews.head(3).to_string(), "\n")

    print("=== COMPETITOR — metrics_df ===")
    print(f"Shape : {metrics.shape}")
    print(f"Dates : {metrics['date'].min().date()}  →  {metrics['date'].max().date()}")
    print(metrics[["date", "price", "is_on_sale", "daily_views",
                    "daily_purchases", "returns", "unanswered_questions"]].head(5).to_string())
