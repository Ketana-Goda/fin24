import pandas as pd
from detect import load_and_clean

messy = pd.DataFrame({
    " Date ": ["01-01-2026", "2026-02-01", "not a date", "05-03-2026", "10-03-2026"],
    "Vendor": ["AWS ", "aws", "Zoom", "  Adobe  Cloud", "Refund Co"],
    "Category": ["Cloud", "Cloud", None, "Software", "Misc"],
    "Amount": ["₹8,500", "8500", "1500", "3,200", "-500"],
})

print("BEFORE:")
print(messy)

clean = load_and_clean(messy)

print("\nAFTER:")
print(clean)
print("\nRows before:", len(messy), "| Rows after:", len(clean))