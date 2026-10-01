import pandas as pd

df = pd.read_csv("data/invoices.csv")

print("Invoice Status:")
print(df["status"].value_counts())

print("\nTotal invoice amount:")
print(df["total_amount"].sum())

print("\nTotal paid amount:")
print(df["paid_amount"].sum())

print("\nTotal balance due:")
print(df["balance_due"].sum())