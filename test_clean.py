import pandas as pd
from detect import load_and_clean

df = pd.read_csv("data/invoices.csv")

cleaned = load_and_clean(df)

print("Cleaned rows:", len(cleaned))
print("\nColumns:")
print(cleaned.columns.tolist())

print("\nFirst 5 rows:")
print(cleaned[["date", "vendor", "category", "amount"]].head())