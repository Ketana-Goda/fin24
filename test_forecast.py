import pandas as pd
from detect import load_and_clean, find_recurring, forecast_upcoming

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", None)

df = load_and_clean(pd.read_csv("data/sample.csv"))
rec = find_recurring(df)
as_of = df["date"].max()

for days in (7, 30, 90):
    up = forecast_upcoming(rec, as_of, days)
    print(f"Next {days:>2} days: {len(up):>3} payments, total Rs {up['amount'].sum():,.0f}")

print()
print(forecast_upcoming(rec, as_of, 30).head(15))