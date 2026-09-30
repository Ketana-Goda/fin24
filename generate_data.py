import random
from datetime import date, timedelta

import pandas as pd

random.seed(42)  # same "random" data every run, so results are repeatable

START = date(2025, 10, 1)
END = date(2026, 9, 30)

rows = []


def add(d, vendor, category, amount):
    rows.append({
        "date": d,
        "vendor": vendor,
        "category": category,
        "amount": round(amount, 2),
    })


def month_start(i):
    """i = 0 means Oct 2025, i = 11 means Sep 2026. Returns (year, month)."""
    year = 2025 + (9 + i) // 12
    month = (9 + i) % 12 + 1
    return year, month


# ---------------------------------------------------------------
# 1) MONTHLY recurring expenses
# (vendor, category, base amount, day of month, monthly growth, months active)
# ---------------------------------------------------------------
monthly = [
    ("AWS",                 "Cloud",     8500,  1, 0.02, 12),  # price keeps creeping up
    ("Office Rent",         "Rent",     45000,  1, 0,    12),
    ("Microsoft 365",       "Software",  4200,  3, 0,    12),
    ("Office 365",          "Software",  3900,  4, 0,    12),  # overlaps with Microsoft 365
    ("Adobe Creative Cloud","Software",  3200,  5, 0,    12),
    ("Canva Pro",           "Software",  1500,  8, 0,    12),  # design overlap
    ("Figma",               "Software",  2000, 15, 0,    12),  # design overlap
    ("Zoom",                "Software",  1500, 10, 0,    12),
    ("Slack",               "Software",  2400, 12, 0,    12),
    ("Airtel Internet",     "Utilities", 2999,  7, 0,    12),
    ("Dropbox",             "Software",  1100,  9, 0,     6),  # stopped after 6 months
]

for i in range(12):
    year, month = month_start(i)
    for vendor, category, base, day, growth, active_months in monthly:
        if i >= active_months:
            continue
        amount = base * (1 + growth) ** i
        if growth > 0:
            amount *= random.uniform(0.98, 1.02)  # small bill variation
        add(date(year, month, day), vendor, category, amount)

# ---------------------------------------------------------------
# 2) QUARTERLY recurring: insurance every 3 months
# ---------------------------------------------------------------
for i in range(0, 12, 3):
    year, month = month_start(i)
    add(date(year, month, 20), "HDFC Insurance", "Insurance", 18000)

# ---------------------------------------------------------------
# 3) WEEKLY recurring: catering every Monday
# ---------------------------------------------------------------
d = START
while d <= END:
    if d.weekday() == 0:  # 0 = Monday
        add(d, "Fresh Bites Catering", "Food", random.uniform(1100, 1300))
    d += timedelta(days=1)

# ---------------------------------------------------------------
# 4) ONE-OFF / random purchases (noise that should NOT be flagged)
# ---------------------------------------------------------------
one_offs = [
    ("Amazon Business", "Supplies",   500,  15000),
    ("Flipkart",        "Supplies",   300,   8000),
    ("Uber",            "Travel",     150,   1200),  # frequent but irregular
    ("Swiggy",          "Food",       200,   1500),  # frequent but irregular
    ("Dell India",      "Hardware", 30000,  90000),
    ("Office Chairs",   "Furniture", 8000,  25000),
    ("Local Printers",  "Supplies",   400,   4000),
    ("Consulting Fee",  "Services", 10000,  60000),
    ("IndiGo",          "Travel",    3000,  12000),
]

total_days = (END - START).days
for _ in range(350):
    vendor, category, low, high = random.choice(one_offs)
    d = START + timedelta(days=random.randint(0, total_days))
    add(d, vendor, category, random.uniform(low, high))

# ---------------------------------------------------------------
# Save to CSV
# ---------------------------------------------------------------
df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
df.to_csv("data/sample.csv", index=False)

print(f"Created data/sample.csv with {len(df)} rows")
print(df.head(10))