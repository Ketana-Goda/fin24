import pandas as pd
from detect import find_recurring

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", None)

raw = pd.read_csv("data/aczen_raw.csv")

df = pd.DataFrame({
    "date": pd.to_datetime(raw["invoice_date"], errors="coerce"),
    "vendor": raw["client_name"].astype(str).str.strip(),
    "category": raw["business_unit_id"].astype(str),
    "amount": raw["total_amount"],
})
df["vendor_key"] = df["vendor"].str.lower()
df = df.dropna(subset=["date", "amount"]).sort_values("date").reset_index(drop=True)

print("Date range:", df["date"].min().date(), "to", df["date"].max().date())
print("\nInvoices per client:")
print(df.groupby("vendor_key").size().sort_values(ascending=False).head(10))

rec = find_recurring(df)
print("\nRecurring found:", len(rec))
if len(rec) > 0:
    print(rec[["vendor", "frequency", "payments", "expected_amount", "status"]])