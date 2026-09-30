import pandas as pd
from detect import load_and_clean, find_recurring, forecast_upcoming
from insights import build_alerts, build_insights

df = load_and_clean(pd.read_csv("data/sample.csv"))
rec = find_recurring(df)
up = forecast_upcoming(rec, df["date"].max(), 30)
alerts = build_alerts(df, rec)

for line in build_insights(df, rec, up, alerts):
    print("•", line)
    print()