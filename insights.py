import pandas as pd

# ---------------------------------------------------------------
# Tools that do a similar job. Paying for 2+ from one group = overlap.
# (Keywords are matched against the vendor name in lowercase.)
# ---------------------------------------------------------------
TOOL_GROUPS = {
    "Design tools": ["adobe", "canva", "figma", "sketch", "affinity"],
    "Office suites": ["microsoft 365", "office 365", "microsoft office",
                      "ms office", "m365", "google workspace"],
    "Video meetings": ["zoom", "google meet", "webex", "gotomeeting", "microsoft teams"],
    "Team chat": ["slack", "discord", "mattermost"],
    "Cloud storage": ["dropbox", "google drive", "onedrive"],
    "Project management": ["asana", "trello", "jira", "monday.com", "notion", "clickup"],
}

PRICE_INCREASE_THRESHOLD = 0.10   # flag increases of 10% or more
SEVERITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}


def _group_for(vendor):
    """Return the tool group a vendor belongs to, or None."""
    name = str(vendor).lower()
    for group, keywords in TOOL_GROUPS.items():
        if any(k in name for k in keywords):
            return group
    return None


def find_duplicates(recurring: pd.DataFrame) -> list:
    """Flag groups of active subscriptions that may overlap."""
    active = recurring[recurring["status"] == "Active"].copy()
    active["group"] = active["vendor"].apply(_group_for)

    alerts = []
    for group, g in active.dropna(subset=["group"]).groupby("group"):
        if len(g) < 2:
            continue
        cost = g["monthly_equivalent"].sum()
        names = ", ".join(g["vendor"])
        alerts.append({
            "type": "Potential duplicate",
            "severity": "Medium",
            "title": f"{group}: {len(g)} overlapping subscriptions",
            "message": (f"You pay for {names}, which all fall in the same group "
                        f"({group}). Combined cost: ₹{cost:,.0f} per month "
                        f"(₹{cost * 12:,.0f} per year). Potential overlap, "
                        f"requires review."),
            "impact_text": f"Combined cost: ₹{cost:,.0f} / month",
            "vendors": list(g["vendor"]),
        })
    return alerts


def find_price_increases(df: pd.DataFrame, recurring: pd.DataFrame) -> list:
    """Flag recurring vendors whose payments have risen noticeably."""
    alerts = []
    for _, r in recurring.iterrows():
        pays = df[df["vendor_key"] == r["vendor"].lower()].sort_values("date")

        # compare the earliest payments with the latest ones
        n = max(1, min(len(pays) // 4, 6))
        early = pays["amount"].head(n).mean()
        recent = pays["amount"].tail(n).mean()
        change = (recent - early) / early

        if change >= PRICE_INCREASE_THRESHOLD:
            payments_per_month = r["annual_cost"] / r["expected_amount"] / 12
            extra_monthly = (recent - early) * payments_per_month
            alerts.append({
                "type": "Price increase",
                "severity": "High" if change >= 0.20 else "Medium",
                "title": f"{r['vendor']} is up {change:.0%}",
                "message": (f"{r['vendor']} payments rose from about ₹{early:,.0f} to "
                            f"₹{recent:,.0f} per payment (average of the first {n} "
                            f"vs the last {n} payments). Worth checking if the plan "
                            f"or usage changed."),
                "impact_text": f"Extra cost vs before: about ₹{extra_monthly:,.0f} / month",
                "vendors": [r["vendor"]],
            })
    return alerts


def find_stopped(recurring: pd.DataFrame) -> list:
    """Flag recurring items whose payments seem to have ended."""
    alerts = []
    for _, r in recurring[recurring["status"] == "Possibly stopped"].iterrows():
        alerts.append({
            "type": "Possibly stopped",
            "severity": "Low",
            "title": f"{r['vendor']}: payments seem to have stopped",
            "message": (f"{r['vendor']} was last paid on {r['last_date']:%d %b %Y} "
                        f"(₹{r['last_amount']:,.0f}, {r['frequency'].lower()}), and "
                        f"nothing has been paid since. It may have been cancelled. "
                        f"Confirm it is not still active or billed elsewhere."),
            "impact_text": f"Previous cost: ₹{r['monthly_equivalent']:,.0f} / month",
            "vendors": [r["vendor"]],
        })
    return alerts


def build_alerts(df: pd.DataFrame, recurring: pd.DataFrame) -> list:
    """Combine all alerts, most serious first."""
    alerts = (find_duplicates(recurring)
              + find_price_increases(df, recurring)
              + find_stopped(recurring))
    return sorted(alerts, key=lambda a: SEVERITY_ORDER[a["severity"]])