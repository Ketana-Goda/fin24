import re

import pandas as pd

REQUIRED_COLUMNS = ["date", "vendor", "category", "amount"]


def load_and_clean(df: pd.DataFrame) -> pd.DataFrame:
    """Take a raw transactions table and return a clean one.

    Expected columns: date, vendor, category, amount
    Adds one extra column: vendor_key (lowercase name, used for grouping).
    """
    df = df.copy()  # never change the user's original data

    # 1) Make column names lowercase with no spaces: " Vendor " -> "vendor"
    df.columns = [str(c).strip().lower() for c in df.columns]

    # 2) Check the required columns exist
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}. Found: {list(df.columns)}")

    df = df[REQUIRED_COLUMNS]

    # 3) Dates: try the standard format (2026-01-31) first,
    #    then fall back to day-first formats (31-01-2026) for the rest
    parsed = pd.to_datetime(df["date"], errors="coerce", format="ISO8601")
    failed = parsed.isna()
    if failed.any():
        parsed[failed] = pd.to_datetime(df.loc[failed, "date"], errors="coerce", dayfirst=True)
    df["date"] = parsed
    # 4) Amounts: remove ₹ , and spaces, then convert to numbers
    df["amount"] = (
        df["amount"]
        .astype(str)
        .str.replace(r"[₹,\s]", "", regex=False)
        .pipe(pd.to_numeric, errors="coerce")
    )

    # 5) Vendor names: trim spaces and collapse double spaces
    df["vendor"] = (
        df["vendor"]
        .astype(str)
        .apply(lambda v: re.sub(r"\s+", " ", v).strip())
    )
    df["vendor_key"] = df["vendor"].str.lower()

    # 6) Category: fill blanks
    df["category"] = df["category"].fillna("Uncategorized").astype(str).str.strip()
    df.loc[df["category"] == "", "category"] = "Uncategorized"

    # 7) Drop unusable rows: no date, no amount, no vendor
    df = df.dropna(subset=["date", "amount"])
    df = df[~df["vendor_key"].isin(["", "nan", "none"])]

    # 8) Keep only real expenses (positive amounts). Refunds/credits are removed.
    df = df[df["amount"] > 0]

    # 9) Sort by date and tidy the row numbers
    df = df.sort_values("date").reset_index(drop=True)
    return df



# =====================================================================
# STEP 4: RECURRING DETECTION
# =====================================================================

# name: (min gap days, max gap days, payments per year)
FREQUENCIES = {
    "Weekly":    (5, 9, 52),
    "Monthly":   (26, 35, 12),
    "Quarterly": (80, 100, 4),
    "Yearly":    (350, 380, 1),
}

MIN_PAYMENTS = 3            # need at least 3 payments to call it a pattern
MAX_AMOUNT_CV = 0.25        # amounts may vary up to ~25% (std / mean)
MIN_GAP_CONSISTENCY = 0.7   # 70% of gaps must be close to the typical gap

RESULT_COLUMNS = [
    "vendor", "category", "frequency", "payments", "avg_amount",
    "last_amount", "expected_amount", "first_date", "last_date",
    "next_date", "status", "monthly_equivalent", "annual_cost", "confidence",
]


def _guess_frequency(median_gap):
    """Turn a typical gap in days into 'Weekly', 'Monthly', etc."""
    for name, (low, high, per_year) in FREQUENCIES.items():
        if low <= median_gap <= high:
            return name, per_year
    return None, None


def _next_payment_date(last_date, frequency):
    """Predict the next payment date from the last one."""
    if frequency == "Weekly":
        return last_date + pd.Timedelta(days=7)
    if frequency == "Monthly":
        return last_date + pd.DateOffset(months=1)
    if frequency == "Quarterly":
        return last_date + pd.DateOffset(months=3)
    return last_date + pd.DateOffset(years=1)


def find_recurring(df: pd.DataFrame) -> pd.DataFrame:
    """Find vendors that are paid on a regular schedule.

    Input: the cleaned DataFrame from load_and_clean().
    Output: one row per recurring vendor (see RESULT_COLUMNS).
    """
    as_of = df["date"].max()  # "today" for our purposes = latest date in the data
    results = []

    for _, g in df.groupby("vendor_key"):
        g = g.sort_values("date")

        # Question 1: enough payments?
        dates = g["date"].drop_duplicates().sort_values()
        if len(dates) < MIN_PAYMENTS:
            continue

        # Question 2: is the typical gap weekly / monthly / quarterly / yearly?
        gaps = dates.diff().dropna().dt.days
        median_gap = gaps.median()
        frequency, per_year = _guess_frequency(median_gap)
        if frequency is None:
            continue

        # Question 3: are the gaps consistent?
        tolerance = max(2, 0.2 * median_gap)
        gap_score = ((gaps - median_gap).abs() <= tolerance).mean()

        # Question 4: are the amounts similar?
        amounts = g["amount"]
        cv = amounts.std() / amounts.mean()

        if gap_score < MIN_GAP_CONSISTENCY or cv > MAX_AMOUNT_CV:
            continue

        # It's recurring! Collect the details.
        last_date = dates.iloc[-1]
        expected = amounts.tail(3).mean()  # last 3 payments follow price changes
        days_since_last = (as_of - last_date).days
        is_active = days_since_last <= median_gap * 1.5

        confidence = 100 * (0.5 * gap_score + 0.5 * (1 - min(cv / MAX_AMOUNT_CV, 1)))

        results.append({
            "vendor": g["vendor"].mode().iloc[0],
            "category": g["category"].mode().iloc[0],
            "frequency": frequency,
            "payments": len(g),
            "avg_amount": round(amounts.mean(), 2),
            "last_amount": round(amounts.iloc[-1], 2),
            "expected_amount": round(expected, 2),
            "first_date": dates.iloc[0],
            "last_date": last_date,
            "next_date": _next_payment_date(last_date, frequency),
            "status": "Active" if is_active else "Possibly stopped",
            "monthly_equivalent": round(expected * per_year / 12, 2),
            "annual_cost": round(expected * per_year, 2),
            "confidence": int(round(confidence)),
        })

    out = pd.DataFrame(results, columns=RESULT_COLUMNS)
    return out.sort_values("monthly_equivalent", ascending=False).reset_index(drop=True)


# =====================================================================
# STEP 5: FORECAST UPCOMING PAYMENTS
# =====================================================================

def forecast_upcoming(recurring: pd.DataFrame, start_date, days: int = 30) -> pd.DataFrame:
    """List every payment we expect in the next `days` days.

    Only 'Active' recurring items are used (stopped ones are ignored).
    Weekly items can appear several times in the window.
    """
    start_date = pd.Timestamp(start_date)
    end_date = start_date + pd.Timedelta(days=days)
    rows = []

    for _, r in recurring[recurring["status"] == "Active"].iterrows():
        pay_date = r["next_date"]

        # if the predicted date is already in the past, move it forward
        while pay_date < start_date:
            pay_date = _next_payment_date(pay_date, r["frequency"])

        # collect every payment inside the window
        while pay_date <= end_date:
            rows.append({
                "date": pay_date,
                "vendor": r["vendor"],
                "category": r["category"],
                "frequency": r["frequency"],
                "amount": r["expected_amount"],
            })
            pay_date = _next_payment_date(pay_date, r["frequency"])

    cols = ["date", "vendor", "category", "frequency", "amount"]
    out = pd.DataFrame(rows, columns=cols)
    return out.sort_values("date").reset_index(drop=True)