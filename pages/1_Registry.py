import os

import pandas as pd
import plotly.express as px
import streamlit as st

import db
from auth import require_login
from detect import find_recurring
from insights import build_alerts
from loaders import load_standard
from style import apply_style

st.set_page_config(page_title="Subscription Financial Management", layout="wide")
apply_style()
user = require_login()
can_edit = user["role"] == "finance_manager"

st.title("📋 Subscription Financial Management")

DECISIONS = ["Undecided", "Renew", "Review", "Cancel"]
LOW_USAGE = 50  # utilization below this % is flagged

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

# ---------- Optional usage data ----------
usage_file = st.sidebar.file_uploader(
    "Optional: usage CSV (vendor, licenses_bought, licenses_used)",
    type=["csv"], key="usage_upload")
usage_raw = None
if usage_file is not None:
    usage_raw = pd.read_csv(usage_file)
    st.sidebar.success(f"Using usage file: {usage_file.name}")
elif os.path.exists("data/sample_usage.csv"):
    if st.sidebar.checkbox("Use synthetic demo usage data", value=True):
        usage_raw = pd.read_csv("data/sample_usage.csv")
        st.sidebar.caption("Demo usage numbers are made up for the demo.")

usage = {}
if usage_raw is not None:
    try:
        u = usage_raw.copy()
        u.columns = [str(c).strip().lower() for c in u.columns]
        u["vkey"] = u["vendor"].astype(str).str.strip().str.lower()
        u["bought"] = pd.to_numeric(u["licenses_bought"], errors="coerce")
        u["used"] = pd.to_numeric(u["licenses_used"], errors="coerce")
        u = u.dropna(subset=["bought", "used"])
        u = u[u["bought"] > 0]
        usage = {r.vkey: (r.used, r.bought) for r in u.itertuples()}
    except KeyError:
        st.sidebar.error("Usage file needs the columns: vendor, licenses_bought, licenses_used")

# ---------- Analysis ----------
as_of = df["date"].max()
recurring = find_recurring(df)
alerts = build_alerts(df, recurring)

if recurring.empty:
    st.warning("No recurring expenses were detected in this data.")
    st.stop()

flags = {}
for a in alerts:
    for v in a["vendors"]:
        flags.setdefault(v, []).append(a["type"])

dept_by_key = df.groupby("vendor_key")["department"].agg(lambda s: s.mode().iloc[0])

reg = recurring.copy()
reg["department"] = reg["vendor"].str.lower().map(dept_by_key).fillna("Unassigned")


# utilization (only where usage data exists)
def util_for(v):
    t = usage.get(v.lower())
    return round(100 * t[0] / t[1]) if t else None


reg["utilization_pct"] = pd.to_numeric(reg["vendor"].map(util_for), errors="coerce")
reg["unused_monthly"] = reg.apply(
    lambda r: r["monthly_equivalent"] * (1 - r["utilization_pct"] / 100)
    if pd.notna(r["utilization_pct"]) else 0.0, axis=1)


def flag_text(r):
    f = list(flags.get(r["vendor"], []))
    if pd.notna(r["utilization_pct"]) and r["utilization_pct"] < LOW_USAGE:
        f.append("Low usage")
    return ", ".join(f)


reg["flags"] = reg.apply(flag_text, axis=1)
reg["next_renewal"] = reg["next_date"].dt.strftime("%d %b %Y")
reg["days_to_renewal"] = (reg["next_date"] - as_of).dt.days
reg.loc[reg["status"] != "Active", ["next_renewal", "days_to_renewal"]] = None


def suggest(r):
    if r["status"] != "Active" or r["flags"]:
        return "Review"
    return "Renew"


reg["suggested"] = reg.apply(suggest, axis=1)

# decisions come from the database
meta = db.load_decisions()
reg["decision"] = reg["vendor"].map(lambda v: meta.get(v, {}).get("decision", "Undecided"))
reg["decided_by"] = reg["vendor"].map(lambda v: meta.get(v, {}).get("decided_by") or "")

# contract details come from the database
contracts = db.load_contracts()
reg["owner"] = reg["vendor"].map(lambda v: contracts.get(v, {}).get("owner") or "")


def _contract_end(v):
    s = contracts.get(v, {}).get("contract_end")
    return pd.to_datetime(s).date() if s else None


reg["contract_end"] = reg["vendor"].map(_contract_end)
reg["notice_days"] = pd.to_numeric(
    reg["vendor"].map(lambda v: contracts.get(v, {}).get("notice_days")), errors="coerce")


def _notice_deadline(r):
    if pd.isna(r["contract_end"]) or pd.isna(r["notice_days"]):
        return None
    return pd.Timestamp(r["contract_end"]) - pd.Timedelta(days=int(r["notice_days"]))


reg["notice_ts"] = pd.to_datetime(reg.apply(_notice_deadline, axis=1), errors="coerce")
reg["notice_deadline"] = reg["notice_ts"].dt.strftime("%d %b %Y")
reg["days_to_notice"] = (reg["notice_ts"] - as_of).dt.days

# ---------- Filters ----------
all_depts = sorted(reg["department"].unique())
depts = st.sidebar.multiselect("Departments", all_depts, default=all_depts)
window = st.sidebar.radio("Renewal window", [30, 60, 90], horizontal=True,
                          format_func=lambda d: f"{d} days")
view = reg[reg["department"].isin(depts)]
active = view[view["status"] == "Active"]

# ---------- KPIs ----------
due = active[active["days_to_renewal"] <= window]
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Active subscriptions", len(active))
k2.metric("Monthly commitment", f"₹{active['monthly_equivalent'].sum():,.0f}")
k3.metric("Annual commitment", f"₹{active['annual_cost'].sum():,.0f}")
k4.metric(f"Renewing in {window} days", len(due), f"₹{due['expected_amount'].sum():,.0f}")
k5.metric("Est. unused spend / year",
          f"₹{active['unused_monthly'].sum() * 12:,.0f}" if usage else "No usage data")
st.caption(f"Data as of {as_of:%d %b %Y}. Flags use payment patterns"
           + (" and the usage file." if usage else
              ". No usage data loaded, so utilization is not assessed."))

# ---------- Registry + decisions + contract details ----------
st.subheader("Subscription registry")
cols = ["vendor", "department", "frequency", "monthly_equivalent", "annual_cost",
        "next_renewal", "days_to_renewal", "utilization_pct", "flags", "suggested",
        "decision", "decided_by", "owner", "contract_end", "notice_days",
        "notice_deadline"]
editable = ["decision", "owner", "contract_end", "notice_days"]
edited = st.data_editor(
    view[cols],
    use_container_width=True,
    hide_index=True,
    disabled=[c for c in cols if c not in editable] if can_edit else True,
    column_config={
        "monthly_equivalent": st.column_config.NumberColumn("Monthly ₹", format="₹%.0f"),
        "annual_cost": st.column_config.NumberColumn("Annual ₹", format="₹%.0f"),
        "days_to_renewal": st.column_config.NumberColumn("Days to renewal"),
        "utilization_pct": st.column_config.NumberColumn("Utilization", format="%.0f%%"),
        "decision": st.column_config.SelectboxColumn("Your decision", options=DECISIONS,
                                                     required=True),
        "decided_by": st.column_config.TextColumn("Decided by"),
        "owner": st.column_config.TextColumn("Owner"),
        "contract_end": st.column_config.DateColumn("Contract end"),
        "notice_days": st.column_config.NumberColumn("Notice days", min_value=0, step=1),
        "notice_deadline": st.column_config.TextColumn("Notice deadline"),
    },
    key="registry_editor",
)

cancel_total = edited[edited["decision"] == "Cancel"]["annual_cost"].sum()
c1, c2 = st.columns([1, 3])
c1.metric("Annual saving if cancelled", f"₹{cancel_total:,.0f}")

if can_edit:
    if c2.button("💾 Save changes"):
        db.save_decisions(dict(zip(edited["vendor"], edited["decision"])), user["username"])
        changes = {}
        for r in edited.itertuples():
            ce = None if pd.isna(r.contract_end) else pd.to_datetime(r.contract_end).strftime("%Y-%m-%d")
            nd = None if pd.isna(r.notice_days) else int(r.notice_days)
            owner = "" if pd.isna(r.owner) else str(r.owner).strip()
            changes[r.vendor] = {"owner": owner, "contract_end": ce, "notice_days": nd}
        db.save_contracts(changes, user["username"])
        st.success("Decisions and contract details saved to the database.")
        st.rerun()
else:
    c2.info("View-only account: changes can only be made by a finance manager.")

st.caption("Contract fields (owner, end date, notice days) are entered by the "
           "finance team. Predicted renewals come from payment history.")

# ---------- Notice deadlines ----------
st.subheader(f"⏰ Notice deadlines in the next {window} days")
notice_due = active[active["days_to_notice"].notna() & (active["days_to_notice"] <= window)]
if notice_due.empty:
    st.write("No notice deadlines in this window. Add contract end dates and notice "
             "periods in the table above.")
else:
    st.dataframe(
        notice_due.sort_values("days_to_notice")[
            ["vendor", "owner", "contract_end", "notice_deadline", "days_to_notice"]],
        use_container_width=True, hide_index=True)

# ---------- Low usage ----------
st.subheader("📉 Low-usage subscriptions")
low = active[active["utilization_pct"].notna() & (active["utilization_pct"] < LOW_USAGE)]
if not usage:
    st.write("Load a usage file in the sidebar to see utilization.")
elif low.empty:
    st.write("No subscriptions below the low-usage threshold.")
else:
    low_view = low.sort_values("unused_monthly", ascending=False)[
        ["vendor", "department", "utilization_pct", "monthly_equivalent", "unused_monthly"]
    ].copy()
    low_view["unused_annual"] = (low_view["unused_monthly"] * 12).round()
    st.dataframe(
        low_view[["vendor", "department", "utilization_pct", "monthly_equivalent",
                  "unused_annual"]],
        use_container_width=True, hide_index=True,
        column_config={
            "utilization_pct": st.column_config.NumberColumn("Utilization", format="%.0f%%"),
            "monthly_equivalent": st.column_config.NumberColumn("Monthly ₹", format="₹%.0f"),
            "unused_annual": st.column_config.NumberColumn("Est. unused ₹/year", format="₹%.0f"),
        })
    st.caption("Estimate = cost × unused share of licences. It assumes cost scales with "
               "licence count, and is meant for review, not as a cancellation recommendation.")

# ---------- Upcoming renewals ----------
st.subheader(f"🔔 Renewals in the next {window} days")
if due.empty:
    st.write("Nothing renews in this window.")
else:
    st.dataframe(
        due.sort_values("days_to_renewal")[
            ["vendor", "department", "next_renewal", "days_to_renewal",
             "expected_amount", "frequency"]],
        use_container_width=True, hide_index=True)

# ---------- Department allocation ----------
st.subheader("🏢 Recurring cost by department")
by_dept = active.groupby("department")["monthly_equivalent"].sum().reset_index()
st.plotly_chart(
    px.bar(by_dept, x="department", y="monthly_equivalent",
           labels={"monthly_equivalent": "Monthly ₹"},
           title="Monthly recurring commitment by department",
           color_discrete_sequence=["#7C3AED"]),
    use_container_width=True)