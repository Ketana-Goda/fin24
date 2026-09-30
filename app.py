import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="FIN-24 Expense Intelligence", layout="wide")
st.title("💰 Recurring Expense Intelligence")

# ---------- Sidebar: upload ----------
uploaded = st.sidebar.file_uploader("Upload transactions CSV", type=["csv"])

if uploaded is None:
    st.info("👈 Upload a CSV to begin (columns: date, vendor, category, amount)")
    st.stop()  # nothing below runs until a file is uploaded

df = pd.read_csv(uploaded)
df["date"] = pd.to_datetime(df["date"])

# ---------- Tabs ----------
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Dashboard", "🔄 Recurring", "⚠️ Alerts", "🤖 Finance Agent"]
)

with tab1:
    st.subheader("Overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Spending", f"₹{df['amount'].sum():,.0f}")
    c2.metric("Recurring Spending", "₹0")       # placeholder for now
    c3.metric("Upcoming (30 days)", "₹0")       # placeholder for now
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
    st.write("Recurring expenses table goes here")

with tab3:
    st.write("Alerts go here")

with tab4:
    st.write("Chat agent goes here")