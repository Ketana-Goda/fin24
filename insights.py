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





# =====================================================================
# STEP 7: PLAIN-ENGLISH INSIGHTS
# =====================================================================

def build_insights(df, recurring, upcoming_30, alerts) -> list:
    """Return a list of short sentences that summarise the situation."""
    if recurring.empty:
        return ["No recurring expenses were detected in this data."]

    active = recurring[recurring["status"] == "Active"]
    insights = []

    # 1) How much of all spending is recurring?
    total_spend = df["amount"].sum()
    rec_keys = recurring["vendor"].str.lower()
    rec_spend = df[df["vendor_key"].isin(rec_keys)]["amount"].sum()
    insights.append(
        f"Recurring expenses make up **{rec_spend / total_spend:.0%}** of total spending "
        f"(₹{rec_spend:,.0f} of ₹{total_spend:,.0f})."
    )

    # 2) How many commitments and what do they cost?
    monthly = active["monthly_equivalent"].sum()
    insights.append(
        f"**{len(active)} active recurring commitments** cost about "
        f"**₹{monthly:,.0f} per month** (₹{monthly * 12:,.0f} per year)."
    )

    # 3) Top 3 biggest
    top = active.head(3)  # already sorted by monthly cost
    top_text = ", ".join(f"{r.vendor} (₹{r.monthly_equivalent:,.0f}/month)"
                         for r in top.itertuples())
    insights.append(f"Largest recurring expenses: {top_text}.")

    # 4) Biggest category
    by_cat = active.groupby("category")["monthly_equivalent"].sum().sort_values(ascending=False)
    insights.append(
        f"**{by_cat.index[0]}** is the biggest recurring category "
        f"(₹{by_cat.iloc[0]:,.0f} per month, {by_cat.iloc[0] / monthly:.0%} of recurring)."
    )

    # 4b) Cost of quarterly/yearly items hidden in the monthly view
    # (skipped: kept simple for the hackathon)

    # 5) Upcoming payments
    insights.append(
        f"Expected recurring payments in the next 30 days: "
        f"**₹{upcoming_30['amount'].sum():,.0f}** across {len(upcoming_30)} payments."
    )

    # 6) Price increases
    for a in alerts:
        if a["type"] == "Price increase":
            insights.append(f"📈 {a['title']}. {a['impact_text']}.")

    # 7) Overlaps
    overlaps = [a for a in alerts if a["type"] == "Potential duplicate"]
    if overlaps:
        overlap_cost = 0
        for a in overlaps:
            overlap_cost += active[active["vendor"].isin(a["vendors"])]["monthly_equivalent"].sum()
        insights.append(
            f"⚠️ **{len(overlaps)} groups** of subscriptions may overlap "
            f"(₹{overlap_cost:,.0f} per month combined). Potential overlap, requires review."
        )

    # 8) Possibly stopped
    stopped = recurring[recurring["status"] == "Possibly stopped"]
    if len(stopped) > 0:
        names = ", ".join(stopped["vendor"])
        insights.append(f"🔵 Payments seem to have stopped for: {names}.")

    return insights
# =====================================================================
# ACZEN INVOICE INSIGHTS
# =====================================================================

def invoice_summary(df):
    """Return basic summary statistics for Aczen invoice data."""

    return {
        "total_invoices": len(df),
        "total_amount": df["total_amount"].sum(),
        "paid_amount": df["paid_amount"].sum(),
        "balance_due": df["balance_due"].sum(),
        "paid_invoices": (df["status"] == "paid").sum(),
        "pending_invoices": (df["status"] == "pending").sum(),
        "overdue_invoices": (df["status"] == "overdue").sum(),
        "partial_invoices": (df["status"] == "partial").sum(),
    }
def find_invoice_alerts(df):
    """Find invoices that need attention."""

    alerts = []

    for _, row in df.iterrows():

        if row["status"] == "overdue":
            alerts.append({
                "type": "Overdue",
                "invoice_number": row["invoice_number"],
                "client": row["client_name"],
                "amount_due": row["balance_due"],
                "message": f"{row['invoice_number']} from {row['client_name']} is overdue."
            })

        elif row["status"] == "pending":
            alerts.append({
                "type": "Pending",
                "invoice_number": row["invoice_number"],
                "client": row["client_name"],
                "amount_due": row["balance_due"],
                "message": f"{row['invoice_number']} from {row['client_name']} is pending."
            })

    # Sort highest outstanding amount first
    alerts.sort(key=lambda x: x["amount_due"], reverse=True)

    return alerts
def client_outstanding(df):
    """Calculate outstanding amount for each client."""

    result = (
        df.groupby("client_name")["balance_due"]
        .sum()
        .reset_index()
    )

    result = result.sort_values(
        "balance_due",
        ascending=False
    )

    return result
def get_dashboard_summary(df):
    """Return key numbers for the dashboard."""

    return {
        "total_invoices": len(df),
        "total_amount": df["total_amount"].sum(),
        "paid_amount": df["paid_amount"].sum(),
        "outstanding": df["balance_due"].sum(),
        "overdue_count": (df["status"] == "overdue").sum(),
        "pending_count": (df["status"] == "pending").sum(),
    }