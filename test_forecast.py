import pandas as pd
from detect import forecast_invoice_cashflow, predict_next_month
df = pd.read_csv("data/invoices.csv")

result = forecast_invoice_cashflow(df)

print("Monthly Invoice Amount")
print("----------------------")

print(result)
prediction = predict_next_month(result)

print("\nPredicted Next Month Invoice Amount")
print("-----------------------------------")
print(f"Rs {prediction:,.2f}")