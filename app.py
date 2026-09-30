from detect import load_and_clean, find_recurring
import streamlit as st
import pandas as pd
import plotly.express as px

from detect import load_and_clean, find_recurring, forecast_upcoming

st.set_page_config(page_title="FIN-24 Expense Intelligence", layout="wide")
st.title("💰 Recurring Expense Intelligence")

# ---------- Sidebar: upload ----------
uploaded = st.sidebar.file_uploader("Upload transactions CSV", type=["csv"])

if uploaded is None:
    st.info("👈 Upload a CSV to begin (columns: date, vendor, category, amount)")
    st.stop()  # nothing below runs until a file is uploaded

raw = pd.read_csv(uploaded)
try:
    df = load_and_clean(raw)
except ValueError as e:
    st.error(f"Could not read this file: {e}")
    st.stop()

st.sidebar.success(f"Loaded {len(df)} transactions ({len(raw) - len(df)} rows removed)")

# ---------- Analysis ----------
as_of = df["date"].max()
recurring = find_recurring(df)
active = recurring[recurring["status"] == "Active"]
upcoming_30 = forecast_upcoming(recurring, as_of, 30)

# ---------- Tabs ----------
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Dashboard", "🔄 Recurring", "⚠️ Alerts", "🤖 Finance Agent"]
)

with tab1:
    st.subheader("Overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Spending", f"₹{df['amount'].sum():,.0f}")
    c2.metric("Recurring / month", f"₹{active['monthly_equivalent'].sum():,.0f}")
    c3.metric("Upcoming (30 days)", f"₹{upcoming_30['amount'].sum():,.0f}")
    c4.metric("Items to Review", "0")           # placeholder for now

    # Monthly spending chart
    monthly = (
        df.groupby(df["date"].dt.to_period("M").astype(str))["amount"]
        .sum()
        .reset_index()
    )
    monthly.columns = ["month", "amount"]
    fig = px.bar(monthly, x="month", y="amount", title="Monthly Spending")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Raw transactions")
    st.dataframe(df, use_container_width=True)

with tab2:
    st.subheader(f"{len(recurring)} recurring expenses detected")
    show = recurring.copy()
    for col in ["first_date", "last_date", "next_date"]:
        show[col] = show[col].dt.strftime("%d %b %Y")
    st.dataframe(
        show[["vendor", "category", "frequency", "expected_amount",
              "next_date", "status", "confidence"]],
        use_container_width=True,
    )

    st.subheader("📅 Upcoming payments")
    days = st.radio("Show next", [7, 30, 90], index=1, horizontal=True,
                    format_func=lambda d: f"{d} days")
    upcoming = forecast_upcoming(recurring, as_of, days)
    st.metric(f"Expected in next {days} days", f"₹{upcoming['amount'].sum():,.0f}",
              f"{len(upcoming)} payments")

    by_vendor = upcoming.groupby("vendor")["amount"].sum().reset_index()
    by_vendor = by_vendor.sort_values("amount", ascending=False)
    st.plotly_chart(px.bar(by_vendor, x="vendor", y="amount",
                           title=f"Expected spend by vendor (next {days} days)"),
                    use_container_width=True)

    up_show = upcoming.copy()
    up_show["date"] = up_show["date"].dt.strftime("%d %b %Y")
    st.dataframe(up_show, use_container_width=True)

with tab3:
    st.write("Alerts go here")

with tab4:
    st.write("Chat agent goes here")