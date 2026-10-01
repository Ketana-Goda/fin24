import pandas as pd

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", None)

df = pd.read_csv("data/aczen_raw.csv")

print("ROWS:", len(df))
print("\nCOLUMNS AND TYPES:")
print(df.dtypes)
print("\nFIRST 8 ROWS:")
print(df.head(8))
print("\nUNIQUE VALUES PER COLUMN:")
print(df.nunique().sort_values())