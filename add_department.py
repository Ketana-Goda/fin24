import pandas as pd

df = pd.read_csv("data/sample.csv")

dept = {
    "AWS": "Engineering", "Slack": "Engineering",
    "Adobe Creative Cloud": "Marketing", "Canva Pro": "Marketing", "Figma": "Marketing",
    "Microsoft 365": "Operations", "Office 365": "Operations",
    "Zoom": "Operations", "Dropbox": "Operations",
    "Office Rent": "Admin", "Airtel Internet": "Admin", "Fresh Bites Catering": "Admin",
    "HDFC Insurance": "Finance",
}
df["department"] = df["vendor"].map(dept).fillna("General")
df.to_csv("data/sample_dept.csv", index=False)
print("Saved data/sample_dept.csv with", len(df), "rows")