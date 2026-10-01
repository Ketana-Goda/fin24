import re

import pandas as pd

REQUIRED = ["date", "vendor", "category", "amount"]


def load_standard(df: pd.DataFrame) -> pd.DataFrame:
    """Clean a standard transactions table: date, vendor, category, amount
    (optional: department)."""
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]

    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}. Found: {list(df.columns)}")

    extra = ["department"] if "department" in df.columns else []
    df = df[REQUIRED + extra]

    parsed = pd.to_datetime(df["date"], errors="coerce", format="ISO8601")
    failed = parsed.isna()
    if failed.any():
        parsed[failed] = pd.to_datetime(df.loc[failed, "date"], errors="coerce", dayfirst=True)
    df["date"] = parsed

    df["amount"] = (
        df["amount"].astype(str)
        .str.replace(r"[₹,\s]", "", regex=True)
        .pipe(pd.to_numeric, errors="coerce")
    )

    df["vendor"] = df["vendor"].astype(str).apply(lambda v: re.sub(r"\s+", " ", v).strip())
    df["vendor_key"] = df["vendor"].str.lower()
    df["category"] = df["category"].fillna("Uncategorized").astype(str).str.strip()

    if "department" in df.columns:
        df["department"] = df["department"].fillna("Unassigned").astype(str).str.strip()
    else:
        df["department"] = "Unassigned"

    df = df.dropna(subset=["date", "amount"])
    df = df[~df["vendor_key"].isin(["", "nan", "none"])]
    df = df[df["amount"] > 0]
    return df.sort_values("date").reset_index(drop=True)