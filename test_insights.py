import pandas as pd
from insights import get_dashboard_summary

df = pd.read_csv("data/invoices.csv")

summary = get_dashboard_summary(df)

print("Dashboard Summary")
print("------------------")

for key, value in summary.items():
    print(f"{key}: {value}")