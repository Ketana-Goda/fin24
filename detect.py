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

    # 3) Dates: convert text to real dates. Bad ones become NaT (empty)
    df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)

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