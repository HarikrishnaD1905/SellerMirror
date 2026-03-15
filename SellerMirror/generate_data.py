# import pandas as pd
# import numpy as np
# from datetime import datetime, timedelta
# import random
# import os

# random.seed(42)
# np.random.seed(42)

# START_DATE = datetime(2024, 10, 1)
# DAYS = 90
# PRODUCT_ID = "PHONE_CASE_01"

# def date_range():
#     return [START_DATE + timedelta(days=i) for i in range(DAYS)]

# MY_GOOD_REVIEWS = [
#     "Great phone case, fits perfectly!",
#     "Good quality for the price.",
#     "Looks exactly like the photo.",
#     "Decent product, arrived on time.",
#     "Happy with this purchase.",
#     "Nice finish, feels sturdy.",
#     "Good value for money.",
#     "Packaging was neat.",
#     "Fits my phone perfectly.",
#     "Colour is accurate to listing.",
#     "Good quality stitching.",
#     "Fast delivery, product is fine.",
#     "Would buy again.",
#     "Much better than before! Updated listing is accurate.",
#     "Great quality now.",
#     "Seller responded quickly to my question.",
#     "Exactly as shown in photos.",
#     "Bought again, quality improved.",
#     "Very happy with new version.",
#     "Fast response from seller.",
#     "Sturdy and well-made.",
#     "Consistent quality.",
#     "Will definitely recommend.",
# ]

# MY_BAD_REVIEWS = [
#     "Looks different from photo, misleading listing.",
#     "Strap broke after 3 days.",
#     "Material feels cheap.",
#     "Not as described.",
#     "Poor stitching, disappointed.",
#     "Returned this item.",
#     "Images on listing don't match product.",
#     "Quality worse than expected.",
#     "Added to cart twice but hesitated — photos unclear.",
#     "No response to my question.",
#     "Seller never answered my query.",
#     "Bought once, won't return.",
#     "Minor stitching issue but okay.",
#     "Average quality but acceptable.",
#     "Strap feels a bit loose but overall good.",
# ]

# COMP_GOOD_REVIEWS = [
#     "Best phone case I've bought!",
#     "Excellent quality, very sturdy.",
#     "Love this case, perfect fit.",
#     "Amazing product, fast delivery.",
#     "Top quality stitching.",
#     "Highly recommend this seller.",
#     "Five stars, no complaints.",
#     "Perfect packaging.",
#     "Great product, great price.",
#     "Superb quality.",
#     "Really happy with this.",
#     "Solid build quality.",
#     "Looks premium.",
#     "Great value.",
#     "Would buy again.",
#     "Fantastic product overall.",
# ]

# COMP_BAD_REVIEWS = [
#     "Strap broke after one week.",
#     "Material feels very cheap now.",
#     "Quality has dropped significantly.",
#     "Not the same as before.",
#     "Poor stitching on new batch.",
#     "Disappointed with recent order.",
#     "Broke on first use.",
#     "Looks nothing like the photo.",
#     "Material complaint — feels plastic.",
#     "Delivery delayed by 2 weeks.",
#     "No response from seller on my complaint.",
#     "Returning this item.",
#     "Rating dropping for a reason.",
#     "Quality inconsistent.",
#     "Seller not responding to questions.",
#     "Would not buy again.",
#     "Still poor quality.",
#     "Strap broke again.",
#     "Avoid this seller.",
#     "Material complaint still unresolved.",
#     "Three bad orders in a row.",
#     "No improvement.",
#     "Seller ignoring complaints.",
#     "Very disappointed.",
#     "Returning for third time.",
#     "Quality never recovered.",
# ]

# def build_reviews(seller_id, good_pool, bad_pool):
#     rows = []
#     rid  = 1

#     if seller_id == "my_product":
#         phases = [
#             (0,  30, 6, good_pool, [4, 5]),
#             (30, 65, 8, bad_pool,  [1, 2, 3]),
#             (65, 90, 6, good_pool, [4, 5]),
#         ]
#     else:
#         phases = [
#             (0,  30, 6, good_pool, [4, 5]),
#             (30, 65, 8, bad_pool,  [1, 2, 3]),
#             (65, 90, 6, bad_pool,  [1, 2]),
#         ]

#     for (d_start, d_end, n, pool, rating_range) in phases:
#         days_available = list(range(d_start, d_end))
#         chosen         = sorted(random.choices(days_available, k=n * 3))[:n * 3]
#         shuffled_pool  = pool.copy()
#         random.shuffle(shuffled_pool)
#         for idx, day_offset in enumerate(chosen):
#             text   = shuffled_pool[idx % len(shuffled_pool)]
#             rating = random.choice(rating_range)
#             if seller_id == "competitor" and d_start == 30:
#                 rating = random.choice([1, 2, 3])
#             if seller_id == "competitor" and d_start == 65:
#                 rating = random.choice([1, 2])
#             rows.append({
#                 "review_id":         f"{seller_id[:3].upper()}{rid:04d}",
#                 "seller_id":         seller_id,
#                 "product_id":        PRODUCT_ID,
#                 "review_text":       text,
#                 "rating":            rating,
#                 "date":              (START_DATE + timedelta(days=day_offset)).date(),
#                 "verified_purchase": random.choice([True, True, True, False]),
#                 "helpful_votes":     random.randint(0, 20),
#                 "replied_by_seller": (
#                     False if seller_id == "competitor" and d_start >= 30
#                     else random.choice([True, False])
#                 ),
#             })
#             rid += 1
#     return rows

# def build_metrics(seller_id):
#     rows = []
#     for i, date in enumerate(date_range()):
#         day = i

#         if seller_id == "my_product":
#             base_price     = 299.0
#             original_price = 349.0
#             if day < 30:
#                 price            = base_price
#                 is_on_sale       = False
#                 views            = random.randint(480, 560)
#                 purchases        = random.randint(16, 22)
#                 cart_adds        = random.randint(60, 80)
#                 cart_completions = random.randint(16, 22)
#                 repeat_purchases = random.randint(3, 6)
#                 returns          = random.randint(0, 2)
#                 unanswered_q     = random.randint(0, 3)
#             elif day < 65:
#                 price            = base_price
#                 is_on_sale       = False
#                 views            = random.randint(400, 480)
#                 purchases        = random.randint(8, 14)
#                 cart_adds        = random.randint(70, 100)
#                 cart_completions = random.randint(8, 14)
#                 repeat_purchases = random.randint(1, 3)
#                 returns          = random.randint(2, 5)
#                 unanswered_q     = random.randint(4, 10)
#             else:
#                 price            = base_price
#                 is_on_sale       = False
#                 views            = random.randint(500, 600)
#                 purchases        = random.randint(20, 30)
#                 cart_adds        = random.randint(65, 85)
#                 cart_completions = random.randint(20, 30)
#                 repeat_purchases = random.randint(5, 9)
#                 returns          = random.randint(0, 1)
#                 unanswered_q     = random.randint(0, 2)

#         else:
#             base_price     = 289.0
#             original_price = 349.0
#             if day < 30:
#                 price            = base_price
#                 is_on_sale       = False
#                 views            = random.randint(520, 620)
#                 purchases        = random.randint(20, 28)
#                 cart_adds        = random.randint(70, 90)
#                 cart_completions = random.randint(20, 28)
#                 repeat_purchases = random.randint(4, 7)
#                 returns          = random.randint(0, 2)
#                 unanswered_q     = random.randint(0, 2)
#             elif day < 65:
#                 decline          = (day - 30) / 35
#                 price            = round(base_price - decline * 60, 2)
#                 is_on_sale       = day > 45
#                 views            = random.randint(
#                     int(520 - decline * 200), int(560 - decline * 200))
#                 purchases        = random.randint(
#                     int(24 - decline * 16), int(28 - decline * 16))
#                 cart_adds        = random.randint(60, 80)
#                 cart_completions = random.randint(
#                     int(20 - decline * 14), int(24 - decline * 14))
#                 repeat_purchases = random.randint(
#                     int(6 - decline * 5), max(1, int(7 - decline * 5)))
#                 returns          = random.randint(int(decline * 3), int(decline * 8))
#                 unanswered_q     = random.randint(int(decline * 5), int(decline * 12))
#             else:
#                 price            = round(base_price - 70 - random.uniform(0, 20), 2)
#                 is_on_sale       = True
#                 views            = random.randint(200, 320)
#                 purchases        = random.randint(3, 8)
#                 cart_adds        = random.randint(30, 55)
#                 cart_completions = random.randint(3, 8)
#                 repeat_purchases = random.randint(0, 1)
#                 returns          = random.randint(5, 12)
#                 unanswered_q     = random.randint(8, 18)

#         rows.append({
#             "seller_id":            seller_id,
#             "date":                 date.date(),
#             "price":                price,
#             "original_price":       original_price,
#             "is_on_sale":           is_on_sale,
#             "daily_views":          views,
#             "daily_purchases":      purchases,
#             "cart_adds":            cart_adds,
#             "cart_completions":     cart_completions,
#             "repeat_purchases":     repeat_purchases,
#             "returns":              returns,
#             "stock_available":      (
#                 True if seller_id == "my_product"
#                 else (day < 80 or random.random() > 0.4)
#             ),
#             "unanswered_questions": unanswered_q,
#         })
#     return rows

# os.makedirs("data", exist_ok=True)

# my_reviews   = build_reviews("my_product",  MY_GOOD_REVIEWS, MY_BAD_REVIEWS)
# comp_reviews = build_reviews("competitor",  COMP_GOOD_REVIEWS, COMP_BAD_REVIEWS)
# reviews_df   = pd.DataFrame(my_reviews + comp_reviews)
# reviews_df.sort_values("date", inplace=True)
# reviews_df.to_csv("data/reviews.csv", index=False)
# print(f"reviews1.csv        -> {len(reviews_df)} rows")

# my_metrics   = build_metrics("my_product")
# comp_metrics = build_metrics("competitor")
# metrics_df   = pd.DataFrame(my_metrics + comp_metrics)
# metrics_df.sort_values(["seller_id", "date"], inplace=True)
# metrics_df.to_csv("data/daily_metrics.csv", index=False)
# print(f"daily_metrics1.csv  -> {len(metrics_df)} rows")

# print("\nSample — my product reviews (first 3):")
# print(reviews_df[reviews_df.seller_id == "my_product"].head(3).to_string())
# print("\nSample — competitor reviews (last 3):")
# print(reviews_df[reviews_df.seller_id == "competitor"].tail(3).to_string())
# print("\nDone. Both CSVs saved to data/")


import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

random.seed(99)
np.random.seed(99)

START_DATE = datetime(2024, 10, 1)
DAYS = 90
PRODUCT_ID = "BT_SPEAKER_PRO"

def date_range():
    return [START_DATE + timedelta(days=i) for i in range(DAYS)]

MY_GOOD_REVIEWS = [
    "Excellent bass, very loud for its size.",
    "Battery lasts all day, very impressed.",
    "Waterproof as advertised, used at the beach.",
    "Pairs instantly with my phone, love it.",
    "Great sound quality for the price.",
    "Compact and portable, takes it everywhere.",
    "Very sturdy build, dropped it twice no damage.",
    "Customer support was helpful and fast.",
    "Exactly as described, no surprises.",
    "Sound is crisp and clear, no distortion.",
    "Bought as a gift, recipient loved it.",
    "Much better than my old speaker.",
    "Setup was super easy, connected in seconds.",
    "Worth every rupee, highly recommend.",
    "New batch sounds even better than before.",
    "Seller fixed the connectivity issue fast.",
    "Updated firmware solved all problems.",
    "Now works perfectly after replacement.",
    "Great after sales support from seller.",
    "Second purchase, quality is consistent.",
    "Sound improved noticeably in recent batch.",
    "Will buy again without hesitation.",
]

MY_BAD_REVIEWS = [
    "Bluetooth keeps disconnecting randomly.",
    "Battery drains in 3 hours not 12 as claimed.",
    "Stopped working after 2 weeks.",
    "Sound cuts out when phone is 2 meters away.",
    "Not waterproof at all, died in light rain.",
    "Bass is distorted at high volume.",
    "Charging port broke after one month.",
    "Not as loud as described in listing.",
    "Seller did not respond to my complaint.",
    "Photos show different color than received.",
    "Returned due to connectivity issues.",
    "Disappointed with build quality.",
]

COMP_GOOD_REVIEWS = [
    "Best bluetooth speaker under 2000.",
    "Incredibly loud and clear sound.",
    "Battery is a beast, lasts 2 days.",
    "Premium build quality, feels expensive.",
    "Waterproof tested in heavy rain, perfect.",
    "Connects instantly every time.",
    "Great bass, neighbours complained!",
    "Highly recommend to everyone.",
    "Used daily for 3 months, no issues.",
    "Best purchase this year.",
    "Sound quality beats speakers 3x the price.",
    "Sturdy, portable, and loud.",
    "Perfect for outdoor parties.",
]

COMP_BAD_REVIEWS = [
    "Quality dropped badly in new batch.",
    "Speaker crackles at medium volume now.",
    "Battery started swelling after 6 weeks.",
    "New units sound nothing like old ones.",
    "Returned three times, all faulty.",
    "Seller not responding to replacement requests.",
    "Build quality is now cheap plastic.",
    "Bought second unit, worse than first.",
    "Bluetooth range reduced to 1 meter.",
    "Overheats during charging.",
    "Sound is tinny and distorted.",
    "Avoid this seller, quality has collapsed.",
    "Charging cable doesnt fit properly.",
    "LED lights stopped working day 1.",
]

def build_reviews(seller_id, good_pool, bad_pool):
    rows = []
    rid  = 1
    if seller_id == "my_product":
        phases = [
            (0,  30, 7, good_pool, [4, 5]),
            (30, 60, 8, bad_pool,  [1, 2, 3]),
            (60, 90, 7, good_pool, [4, 5]),
        ]
    else:
        phases = [
            (0,  40, 8, good_pool, [4, 5]),
            (40, 70, 8, bad_pool,  [1, 2, 3]),
            (70, 90, 6, bad_pool,  [1, 2]),
        ]
    for (d_start, d_end, n, pool, rating_range) in phases:
        days_available = list(range(d_start, d_end))
        chosen         = sorted(random.choices(days_available, k=n * 2))[:n * 2]
        shuffled_pool  = pool.copy()
        random.shuffle(shuffled_pool)
        for idx, day_offset in enumerate(chosen):
            text   = shuffled_pool[idx % len(shuffled_pool)]
            rating = random.choice(rating_range)
            if seller_id == "competitor" and d_start == 70:
                rating = random.choice([1, 2])
            rows.append({
                "review_id":         f"{seller_id[:3].upper()}{rid:04d}",
                "seller_id":         seller_id,
                "product_id":        PRODUCT_ID,
                "review_text":       text,
                "rating":            rating,
                "date":              (START_DATE + timedelta(days=day_offset)).date(),
                "verified_purchase": random.choice([True, True, True, False]),
                "helpful_votes":     random.randint(0, 25),
                "replied_by_seller": (
                    False if seller_id == "competitor" and d_start >= 40
                    else random.choice([True, False])
                ),
            })
            rid += 1
    return rows

def build_metrics(seller_id):
    rows = []
    for i, date in enumerate(date_range()):
        day = i
        if seller_id == "my_product":
            base_price     = 1799.0
            original_price = 1999.0
            if day < 30:
                price            = base_price
                is_on_sale       = False
                views            = random.randint(550, 650)
                purchases        = random.randint(20, 28)
                cart_adds        = random.randint(70, 90)
                cart_completions = random.randint(20, 28)
                repeat_purchases = random.randint(4, 7)
                returns          = random.randint(0, 2)
                unanswered_q     = random.randint(0, 3)
            elif day < 60:
                price            = base_price
                is_on_sale       = False
                views            = random.randint(460, 530)
                purchases        = random.randint(9, 15)
                cart_adds        = random.randint(75, 105)
                cart_completions = random.randint(9, 15)
                repeat_purchases = random.randint(1, 3)
                returns          = random.randint(3, 7)
                unanswered_q     = random.randint(5, 12)
            else:
                price            = base_price
                is_on_sale       = False
                views            = random.randint(580, 680)
                purchases        = random.randint(24, 34)
                cart_adds        = random.randint(72, 92)
                cart_completions = random.randint(24, 34)
                repeat_purchases = random.randint(6, 10)
                returns          = random.randint(0, 1)
                unanswered_q     = random.randint(0, 2)
        else:
            base_price     = 1749.0
            original_price = 1999.0
            if day < 40:
                price            = base_price
                is_on_sale       = False
                views            = random.randint(600, 720)
                purchases        = random.randint(26, 36)
                cart_adds        = random.randint(80, 100)
                cart_completions = random.randint(26, 36)
                repeat_purchases = random.randint(5, 9)
                returns          = random.randint(0, 2)
                unanswered_q     = random.randint(0, 2)
            elif day < 70:
                decline          = (day - 40) / 30
                price            = round(base_price - decline * 250, 2)
                is_on_sale       = day > 52
                views            = random.randint(
                    int(580 - decline * 250), int(640 - decline * 250))
                purchases        = random.randint(
                    int(30 - decline * 20), max(6, int(34 - decline * 20)))
                cart_adds        = random.randint(65, 90)
                cart_completions = random.randint(
                    int(26 - decline * 18), max(5, int(30 - decline * 18)))
                repeat_purchases = random.randint(
                    int(7 - decline * 6), max(1, int(8 - decline * 6)))
                returns          = random.randint(int(decline * 4), int(decline * 10))
                unanswered_q     = random.randint(int(decline * 6), int(decline * 15))
            else:
                price            = round(base_price - 300 - random.uniform(0, 80), 2)
                is_on_sale       = True
                views            = random.randint(180, 300)
                purchases        = random.randint(2, 7)
                cart_adds        = random.randint(25, 50)
                cart_completions = random.randint(2, 7)
                repeat_purchases = random.randint(0, 1)
                returns          = random.randint(6, 14)
                unanswered_q     = random.randint(10, 20)
        rows.append({
            "seller_id":            seller_id,
            "date":                 date.date(),
            "price":                price,
            "original_price":       original_price,
            "is_on_sale":           is_on_sale,
            "daily_views":          views,
            "daily_purchases":      purchases,
            "cart_adds":            cart_adds,
            "cart_completions":     cart_completions,
            "repeat_purchases":     repeat_purchases,
            "returns":              returns,
            "stock_available":      (
                True if seller_id == "my_product"
                else (day < 82 or random.random() > 0.45)
            ),
            "unanswered_questions": unanswered_q,
        })
    return rows

os.makedirs("data", exist_ok=True)

my_reviews   = build_reviews("my_product",  MY_GOOD_REVIEWS, MY_BAD_REVIEWS)
comp_reviews = build_reviews("competitor",  COMP_GOOD_REVIEWS, COMP_BAD_REVIEWS)
reviews_df   = pd.DataFrame(my_reviews + comp_reviews)
reviews_df.sort_values("date", inplace=True)
reviews_df.to_csv("data/reviews.csv", index=False)
print(f"reviews.csv        -> {len(reviews_df)} rows")

my_metrics   = build_metrics("my_product")
comp_metrics = build_metrics("competitor")
metrics_df   = pd.DataFrame(my_metrics + comp_metrics)
metrics_df.sort_values(["seller_id", "date"], inplace=True)
metrics_df.to_csv("data/daily_metrics.csv", index=False)
print(f"daily_metrics.csv  -> {len(metrics_df)} rows")

print("\nSample — my product reviews (first 3):")
print(reviews_df[reviews_df.seller_id == "my_product"].head(3).to_string())
print("\nSample — competitor reviews (last 3):")
print(reviews_df[reviews_df.seller_id == "competitor"].tail(3).to_string())
print("\nDone. Both CSVs saved to data/")