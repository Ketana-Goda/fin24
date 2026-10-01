import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ACZEN_API_KEY")
base_url = os.getenv("ACZEN_BASE_URL")

url = base_url + "/invoices?limit=300"

headers = {
    "Authorization": f"Bearer {api_key}"
}

response = requests.get(url, headers=headers, timeout=30)
data = response.json()

df = pd.DataFrame(data["data"])

df.to_csv("data/invoices.csv", index=False)

print("CSV saved successfully!")

print("Number of invoices:", len(df))
print("\nColumns:")
print(df.columns.tolist())

print("\nInvoice Data:")
print(df[["invoice_number", "client_name", "total_amount", "paid_amount", "balance_due"]])
df.to_csv('data/aczen_raw.csv', index=False)
print('Saved', len(df), 'rows')
