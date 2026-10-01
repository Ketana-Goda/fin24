import pandas as pd

# SYNTHETIC demo data (made up for the demo, not real usage)
usage = pd.DataFrame({
    "vendor": ["Microsoft 365", "Office 365", "Adobe Creative Cloud", "Canva Pro",
               "Figma", "Zoom", "Slack"],
    "licenses_bought": [60, 40, 10, 8, 6, 25, 50],
    "licenses_used":   [52, 12, 3, 2, 5, 22, 46],
})
usage.to_csv("data/sample_usage.csv", index=False)
print(usage)