import os

import pandas as pd
import plotly.express as px
import streamlit as st

from detect import find_recurring
from insights import build_alerts
from loaders import load_standard

st.set_page_config(page_title="Subscription Registry", layout="wide")
st.title("📋 Subscription Registry & Renewals")

DECISIONS = ["Undecided", "Renew", "Review", "Cancel"]
DEC_FILE = "data/decisions.csv"

# ---------- Data source ----------
uploaded = st.sidebar.file_uploader("Upload expense transactions CSV", type=["csv"])
if uploaded is not None:
    raw = pd.read_csv(uploaded)
    st.sidebar.success(f"Using uploaded file: {uploaded.name}")
else:
    path = "data/sample_dept.csv" if os.path.exists("data/sample_dept.csv") else "data/sample.csv"
    raw = pd.read_csv(path)
    st.sidebar.info("Using synthetic demo expense ledger (not real company data)")

try:
    df = load_standard(raw)
except ValueError as e:
    st.error(f"Could not read this file: {e}")
    st.stop()

# ---------- Analysis ----------
as_of = df["date"].max()
recurring = find_recurring(df)
alerts = build_alerts(df, recurring)

if recurring.empty:
    st.warning("No recurring expenses were detected in this data.")
    st.stop()

# which vendors have which flags
flags = {}
for a in alerts:
    for v in a["vendors"]:
        flags.setdefault(v, []).append(a["type"])

dept_by_key = df.groupby("vendor_key")["department"].agg(lambda s: s.mode().iloc[0])

reg = recurring.copy()
reg["department"] = reg["vendor"].str.lower().map(dept_by_key).fillna("Unassigned")
reg["flags"] = reg["vendor"].map(lambda v: ", ".join(flags.get(v, [])))
reg["next_renewal"] = reg["next_date"].dt.strftime("%d %b %Y")
reg["days_to_renewal"] = (reg["next_date"] - as_of).dt.days
reg.loc[reg["status"] != "Active", ["next_renewal", "days_to_renewal"]] = None


def suggest(r):
    if r["status"] != "Active" or r["flags"]:
        return "Review"
    return "Renew"


reg["suggested"] = reg.apply(suggest, axis=1)

# saved decisions
saved = {}
if os.path.exists(DEC_FILE):
    saved = pd.read_csv(DEC_FILE).set_index("vendor")["decision"].to_dict()
reg["decision"] = reg["vendor"].map(saved).fillna("Undecided")

# ---------- Filters ----------
all_depts = sorted(reg["department"].unique())
depts = st.sidebar.multiselect("Departments", all_depts, default=all_depts)
window = st.sidebar.radio("Renewal window", [30, 60, 90], horizontal=True,
                          format_func=lambda d: f"{d} days")
view = reg[reg["department"].isin(depts)]
active = view[view["status"] == "Active"]

# ---------- KPIs ----------
due = active[active["days_to_renewal"] <= window]
k1, k2, k3, k4 = st.columns(4)
k1.metric("Active subscriptions", len(active))
k2.metric("Monthly commitment", f"₹{active['monthly_equivalent'].sum():,.0f}")
k3.metric("Annual commitment", f"₹{active['annual_cost'].sum():,.0f}")
k4.metric(f"Renewing in {window} days", len(due),
          f"₹{due['expected_amount'].sum():,.0f}")
st.caption(f"Data as of {as_of:%d %b %Y}. Flags use payment patterns only. "
           "No usage data is available, so utilization is not assessed.")

# ---------- Registry + decisions ----------
st.subheader("Subscription registry")
cols = ["vendor", "department", "category", "frequency", "monthly_equivalent",
        "annual_cost", "next_renewal", "days_to_renewal", "status", "flags",
        "suggested", "decision"]
edited = st.data_editor(
    view[cols],
    use_container_width=True,
    hide_index=True,
    disabled=[c for c in cols if c != "decision"],
    column_config={
        "monthly_equivalent": st.column_config.NumberColumn("Monthly ₹", format="₹%.0f"),
        "annual_cost": st.column_config.NumberColumn("Annual ₹", format="₹%.0f"),
        "days_to_renewal": st.column_config.NumberColumn("Days to renewal"),
        "decision": st.column_config.SelectboxColumn("Your decision", options=DECISIONS,
                                                     required=True),
    },
    key="registry_editor",
)

cancel_total = edited[edited["decision"] == "Cancel"]["annual_cost"].sum()
c1, c2 = st.columns([1, 3])
c1.metric("Annual saving if cancelled", f"₹{cancel_total:,.0f}")
if c2.button("💾 Save decisions"):
    saved.update(dict(zip(edited["vendor"], edited["decision"])))
    pd.DataFrame({"vendor": list(saved), "decision": list(saved.values())}) \
        .to_csv(DEC_FILE, index=False)
    st.success("Decisions saved.")

# ---------- Upcoming renewals ----------
st.subheader(f"🔔 Renewals in the next {window} days")
if due.empty:
    st.write("Nothing renews in this window.")
else:
    st.dataframe(
        due.sort_values("days_to_renewal")[
            ["vendor", "department", "next_renewal", "days_to_renewal",
             "expected_amount", "frequency"]],
        use_container_width=True, hide_index=True,
    )

# ---------- Department allocation ----------
st.subheader("🏢 Recurring cost by department")
by_dept = active.groupby("department")["monthly_equivalent"].sum().reset_index()
st.plotly_chart(
    px.bar(by_dept, x="department", y="monthly_equivalent",
           labels={"monthly_equivalent": "Monthly ₹"},
           title="Monthly recurring commitment by department"),
    use_container_width=True,
)