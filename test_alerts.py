import pandas as pd
from detect import load_and_clean, find_recurring
from insights import build_alerts

df = load_and_clean(pd.read_csv("data/sample.csv"))
rec = find_recurring(df)
alerts = build_alerts(df, rec)

print(f"{len(alerts)} alerts found\n")
for a in alerts:
    print(f"[{a['severity']}] {a['type']} | {a['title']}")
    print("   ", a["message"])
    print("   ", a["impact_text"])
    print()