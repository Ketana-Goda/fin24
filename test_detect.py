import pandas as pd
from detect import load_and_clean, find_recurring

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", None)

df = load_and_clean(pd.read_csv("data/sample.csv"))
rec = find_recurring(df)

print(rec[["vendor", "frequency", "payments", "expected_amount",
           "next_date", "status", "confidence"]])
print("\nRecurring found:", len(rec))