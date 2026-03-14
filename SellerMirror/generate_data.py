import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

random.seed(42)
np.random.seed(42)

START_DATE = datetime(2024, 10, 1)
DAYS = 90

# ── helpers ──────────────────────────────────────────────────────────────────

def date_range():
    return [START_DATE + timedelta(days=i) for i in range(DAYS)]

# ── REVIEWS TABLE ─────────────────────────────────────────────────────────────

MY_REVIEWS = [
    # Days 1-30: mostly positive, minor quality complaints
    "Great phone case, fits perfectly!", "Good quality for the price.",
    "Looks exactly like the photo.", "Decent product, arrived on time.",
    "Happy with this purchase.", "Nice finish, feels sturdy.",
    "Good value for money.", "Packaging was neat.",
    "Fits my phone perfectly.", "Colour is accurate to listing.",
    "Strap feels a bit loose but overall good.", "Minor stitching issue but okay.",
    "Good quality stitching.", "Fast delivery, product is fine.",
    "Would buy again.", "Average quality but acceptable.",
    # Days 31-65: ghost signals rising, some complaints, then improving
    "Looks different from photo, misleading listing.", "Strap broke after 3 days.",
    "Material feels cheap.", "Not as described.",
    "Poor stitching, disappointed.", "Returned this item.",
    "Images on listing don't match product.", "Quality worse than expected.",
    "Added to cart twice but hesitated — photos unclear.", "No response to my question.",
    "Seller never answered my query.", "Bought once, won't return.",
    # Days 66-90: recovered after fix
    "Much better than before! Updated listing is accurate.", "Great quality now.",
    "Seller responded quickly to my question.", "Exactly as shown in photos.",
    "Bought again, quality improved.", "Very happy with new version.",
    "Fast response from seller.", "Sturdy and well-made.",
    "Consistent quality.", "Will definitely recommend.",
]

COMPETITOR_REVIEWS = [
    # Days 1-30: strong start
    "Best phone case I've bought!", "Excellent quality, very sturdy.",
    "Love this case, perfect fit.", "Amazing product, fast delivery.",
    "Top quality stitching.", "Highly recommend this seller.",
    "Five stars, no complaints.", "Perfect packaging.",
    "Great product, great price.", "Superb quality.",
    "Really happy with this.", "Solid build quality.",
    "Looks premium.", "Great value.", "Would buy again.",
    "Fantastic product overall.",
    # Days 31-65: quality complaints rising
    "Strap broke after one week.", "Material feels very cheap now.",
    "Quality has dropped significantly.", "Not the same as before.",
    "Poor stitching on new batch.", "Disappointed with recent order.",
    "Broke on first use.", "Looks nothing like the photo.",
    "Material complaint — feels plastic.", "Delivery delayed by 2 weeks.",
    "No response from seller on my complaint.", "Returning this item.",
    "Rating dropping for a reason.", "Quality inconsistent.",
    "Seller not responding to questions.", "Would not buy again.",
    # Days 66-90: continued decline
    "Still poor quality.", "Strap broke again.",
    "Avoid this seller.", "Material complaint still unresolved.",
    "Three bad orders in a row.", "No improvement.",
    "Seller ignoring complaints.", "Very disappointed.",
    "Returning for third time.", "Quality never recovered.",
]

def build_reviews(seller_id, review_pool, n_per_phase=(6, 8, 6)):
    rows = []
    review_id = 1
    phases = [
        (0,  30,  n_per_phase[0], [4, 5],    False),   # healthy
        (30, 65,  n_per_phase[1], [1,2,3],   True),    # declining / ghost
        (65, 90,  n_per_phase[2], [4, 5],    False),   # recovery (my) / worse (comp)
    ]
    pool = review_pool.copy()
    random.shuffle(pool)
    pool_idx = 0

    for (d_start, d_end, n, rating_pool, has_complaints) in phases:
        days_in_phase = list(range(d_start, d_end))
        chosen_days = sorted(random.choices(days_in_phase, k=n * 3))[:n * 3]
        for i, day_offset in enumerate(chosen_days):
            text = pool[pool_idx % len(pool)]
            pool_idx += 1
            rating = random.choice(rating_pool)
            # for competitor in decline phase push rating lower
            if seller_id == "competitor" and d_start == 30:
                rating = random.choice([1, 2, 3])
            if seller_id == "competitor" and d_start == 65:
                rating = random.choice([1, 2])
            rows.append({
                "review_id":         f"{seller_id[:3].upper()}{review_id:04d}",
                "seller_id":         seller_id,
                "product_id":        "PHONE_CASE_01",
                "review_text":       text,
                "rating":            rating,
                "date":              (START_DATE + timedelta(days=day_offset)).date(),
                "verified_purchase": random.choice([True, True, True, False]),
                "helpful_votes":     random.randint(0, 20),
                "replied_by_seller": False if has_complaints and seller_id == "competitor"
                                     else random.choice([True, False]),
            })
            review_id += 1
    return rows

# ── DAILY METRICS TABLE ───────────────────────────────────────────────────────

def build_metrics(seller_id):
    rows = []
    for i, date in enumerate(date_range()):
        day = i  # 0-indexed

        # ── MY PRODUCT ───────────────────────────────────────────────────────
        if seller_id == "my_product":
            base_price       = 299.0
            original_price   = 349.0

            if day < 30:        # healthy phase
                price            = base_price
                is_on_sale       = False
                views            = random.randint(480, 560)
                purchases        = random.randint(16, 22)
                cart_adds        = random.randint(60, 80)
                cart_completions = random.randint(16, 22)
                repeat_purchases = random.randint(3, 6)
                returns          = random.randint(0, 2)
                unanswered_q     = random.randint(0, 3)

            elif day < 65:      # ghost signals rising
                price            = base_price
                is_on_sale       = False
                views            = random.randint(400, 480)
                purchases        = random.randint(8, 14)       # conversion drops
                cart_adds        = random.randint(70, 100)     # people browse but leave
                cart_completions = random.randint(8, 14)
                repeat_purchases = random.randint(1, 3)
                returns          = random.randint(2, 5)
                unanswered_q     = random.randint(4, 10)

            else:               # recovery — listing fixed
                price            = base_price
                is_on_sale       = False
                views            = random.randint(500, 600)
                purchases        = random.randint(20, 30)      # conversion recovers
                cart_adds        = random.randint(65, 85)
                cart_completions = random.randint(20, 30)
                repeat_purchases = random.randint(5, 9)
                returns          = random.randint(0, 1)
                unanswered_q     = random.randint(0, 2)

        # ── COMPETITOR ───────────────────────────────────────────────────────
        else:
            base_price       = 289.0
            original_price   = 349.0

            if day < 30:        # strong start
                price            = base_price
                is_on_sale       = False
                views            = random.randint(520, 620)
                purchases        = random.randint(20, 28)
                cart_adds        = random.randint(70, 90)
                cart_completions = random.randint(20, 28)
                repeat_purchases = random.randint(4, 7)
                returns          = random.randint(0, 2)
                unanswered_q     = random.randint(0, 2)

            elif day < 65:      # quality complaints hit; panic discounting starts
                decline          = (day - 30) / 35            # 0→1 over this phase
                price            = round(base_price - decline * 60, 2)   # drops to ~229
                is_on_sale       = day > 45                   # sale flag from day 45
                views            = random.randint(int(520 - decline*200), int(560 - decline*200))
                purchases        = random.randint(int(24 - decline*16), int(28 - decline*16))
                cart_adds        = random.randint(60, 80)
                cart_completions = random.randint(int(20 - decline*14), int(24 - decline*14))
                repeat_purchases = random.randint(int(6 - decline*5), max(1, int(7 - decline*5)))
                returns          = random.randint(int(decline*3), int(decline*8))
                unanswered_q     = random.randint(int(decline*5), int(decline*12))

            else:               # continued decline, deep discounts
                price            = round(base_price - 70 - random.uniform(0, 20), 2)
                is_on_sale       = True
                views            = random.randint(200, 320)
                purchases        = random.randint(3, 8)
                cart_adds        = random.randint(30, 55)
                cart_completions = random.randint(3, 8)
                repeat_purchases = random.randint(0, 1)
                returns          = random.randint(5, 12)
                unanswered_q     = random.randint(8, 18)

        rows.append({
            "seller_id":         seller_id,
            "date":              date.date(),
            "price":             price,
            "original_price":    original_price,
            "is_on_sale":        is_on_sale,
            "daily_views":       views,
            "daily_purchases":   purchases,
            "cart_adds":         cart_adds,
            "cart_completions":  cart_completions,
            "repeat_purchases":  repeat_purchases,
            "returns":           returns,
            "stock_available":   True if seller_id == "my_product" else (day < 80 or random.random() > 0.4),
            "unanswered_questions": unanswered_q,
        })
    return rows

# ── GENERATE & SAVE ───────────────────────────────────────────────────────────

os.makedirs("data", exist_ok=True)

# Reviews
my_reviews   = build_reviews("my_product",  MY_REVIEWS,         n_per_phase=(6, 8, 6))
comp_reviews = build_reviews("competitor",  COMPETITOR_REVIEWS, n_per_phase=(6, 8, 6))
reviews_df   = pd.DataFrame(my_reviews + comp_reviews)
reviews_df.sort_values("date", inplace=True)
reviews_df.to_csv("data/reviews.csv", index=False)
print(f"reviews.csv → {len(reviews_df)} rows")

# Daily metrics
my_metrics   = build_metrics("my_product")
comp_metrics = build_metrics("competitor")
metrics_df   = pd.DataFrame(my_metrics + comp_metrics)
metrics_df.sort_values(["seller_id", "date"], inplace=True)
metrics_df.to_csv("data/daily_metrics.csv", index=False)
print(f"daily_metrics.csv → {len(metrics_df)} rows")

print("\nSample — reviews:")
print(reviews_df.head(3).to_string())
print("\nSample — daily metrics:")
print(metrics_df.head(3).to_string())
print("\nDone. Both CSVs saved to data/")