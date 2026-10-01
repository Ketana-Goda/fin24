import os

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

from agent import ask_question
from detect import forecast_invoice_cashflow, predict_next_month
from insights import (
    client_outstanding,
    find_invoice_alerts,
    get_dashboard_summary,
)
from style import apply_style

# ==================================================
# LOAD ENVIRONMENT
# ==================================================

load_dotenv()

# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="PLUTO24",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_style()

# ==================================================
# PLUTO24 LIGHT / PURPLE UI
# ==================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* MAIN APP */
.stApp {
    background:
        radial-gradient(circle at 10% 10%, rgba(139, 92, 246, 0.08), transparent 30%),
        radial-gradient(circle at 90% 20%, rgba(217, 70, 239, 0.06), transparent 25%),
        #FFFFFF;
    color: #1F1B2E;
    font-family: 'Inter', sans-serif;
}

.block-container {
    max-width: 1500px;
    padding-top: 2.5rem;
    padding-left: 2rem;
    padding-right: 2rem;
    padding-bottom: 3rem;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #F5F3FF 0%, #FFFFFF 100%);
    border-right: 1px solid #DDD6FE;
}

section[data-testid="stSidebar"] * {
    color: #3B2A66;
}

.stRadio label {
    padding: 10px 12px;
    border-radius: 10px;
    transition: all 0.25s ease;
}

.stRadio label:hover {
    background: rgba(124, 58, 237, 0.08);
}

/* TITLES */
.pluto-title {
    font-size: 42px;
    font-weight: 700;
    letter-spacing: -1px;
    background: linear-gradient(90deg, #6D28D9, #A855F7, #D946EF);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 2px;
}

.pluto-subtitle {
    color: #6B6585;
    font-size: 15px;
    margin-bottom: 32px;
}

/* METRIC CARDS */
.metric-card {
    box-sizing: border-box;
    width: 100%;
    background: #FFFFFF;
    border: 1px solid #DDD6FE;
    border-radius: 18px;
    padding: 22px;
    min-height: 125px;
    box-shadow: 0 2px 12px rgba(124, 58, 237, 0.08);
    transition: transform 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
}

.metric-card:hover {
    transform: translateY(-4px);
    border-color: #7C3AED;
    box-shadow: 0 8px 24px rgba(124, 58, 237, 0.18);
}

.metric-label {
    color: #6B6585;
    font-size: 14px;
    margin-bottom: 12px;
}

.metric-value {
    color: #1F1B2E;
    font-size: 26px;
    font-weight: 700;
}

/* SECTION HEADINGS */
.section-title {
    font-size: 21px;
    font-weight: 600;
    color: #2E1065;
    margin-top: 35px;
    margin-bottom: 18px;
}

/* BUTTONS */
.stButton > button {
    background: #F5F3FF;
    color: #5B21B6;
    border: 1px solid #C4B5FD;
    border-radius: 10px;
    transition: all 0.25s ease;
}

.stButton > button:hover {
    background: #EDE9FE;
    border-color: #7C3AED;
}

/* TEXT INPUT */
.stTextInput input {
    background: #FFFFFF;
    color: #1F1B2E;
    border: 1px solid #C4B5FD;
    border-radius: 12px;
}

.stTextInput input:focus {
    border-color: #7C3AED;
    box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.12);
}

/* DATAFRAME */
div[data-testid="stDataFrame"] {
    border: 1px solid #DDD6FE;
    border-radius: 14px;
    overflow: hidden;
}

hr {
    border-color: #E9E5FF !important;
}

/* HIDE STREAMLIT DEFAULT UI */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

</style>
""", unsafe_allow_html=True)


# ==================================================
# ACZEN API (cached, with offline fallback)
# ==================================================

FALLBACK_CSV = "data/aczen_raw.csv"


@st.cache_data(ttl=600, show_spinner="Loading invoices...")
def load_invoices():
    """Fetch invoices once and reuse them for 10 minutes.
    Returns (DataFrame, source). Falls back to a saved copy if the API fails."""
    api_key = os.getenv("ACZEN_API_KEY") or os.getenv("NOVA_API_KEY")
    base_url = os.getenv("ACZEN_BASE_URL") or os.getenv("NOVA_BASE_URL")

    if api_key and base_url:
        try:
            response = requests.get(
                f"{base_url}/invoices?limit=300",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=15,
            )
            if response.status_code == 200:
                return pd.DataFrame(response.json()["data"]), "live API"
        except Exception:
            pass

    if os.path.exists(FALLBACK_CSV):
        return pd.read_csv(FALLBACK_CSV), "saved copy (offline)"

    return None, "none"


df, data_source = load_invoices()

if df is None:
    st.error("Unable to load invoice data from Aczen, and no saved copy was found.")
    st.stop()

# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:

    st.markdown(
        '<div style="text-align:center; padding:10px 0 25px 0;">'
        '<div style="font-size:34px; font-weight:700; color:#6D28D9;">'
        '✦ PLUTO24'
        '</div>'
        '<div style="font-size:11px; color:#8B83A6; '
        'letter-spacing:2px; margin-top:6px;">'
        'FINANCE INTELLIGENCE'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("### Navigation")

    page = st.radio(
        "Navigation",
        [
            "◉ Dashboard",
            "◈ Invoices",
            "◇ Analytics",
            "⚠ Alerts",
            "✦ AI Assistant",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.caption("Powered by Aczen Nova API")
    st.caption(f"Data source: {data_source}")


# ==================================================
# DASHBOARD
# ==================================================

if page == "◉ Dashboard":

    st.markdown('<div class="pluto-title">PLUTO24</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="pluto-subtitle">Finance Intelligence & Invoice Monitoring</div>',
        unsafe_allow_html=True,
    )

    summary = get_dashboard_summary(df)

    col1, col2, col3, col4 = st.columns(4, gap="medium")

    with col1:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">Total Invoices</div>'
            f'<div class="metric-value">{summary["total_invoices"]}</div></div>',
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">Total Invoiced</div>'
            f'<div class="metric-value">₹{summary["total_amount"]:,.0f}</div></div>',
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">Amount Paid</div>'
            f'<div class="metric-value">₹{summary["paid_amount"]:,.0f}</div></div>',
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">Outstanding</div>'
            f'<div class="metric-value">₹{summary["outstanding"]:,.0f}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-title">Overview</div>', unsafe_allow_html=True)

    st.write(
        "PLUTO24 provides centralized invoice monitoring, "
        "payment tracking, alerts and financial insights. "
        "Use the Registry and Assistant pages in the sidebar menu "
        "for recurring-expense and subscription management."
    )


# ==================================================
# INVOICES
# ==================================================

if page == "◈ Invoices":

    st.markdown('<div class="pluto-title">Invoices</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="pluto-subtitle">View and monitor invoice records</div>',
        unsafe_allow_html=True,
    )

    st.dataframe(
        df[
            [
                "invoice_number",
                "client_name",
                "total_amount",
                "paid_amount",
                "balance_due",
                "status",
                "invoice_date",
                "due_date",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )


# ==================================================
# ANALYTICS
# ==================================================

if page == "◇ Analytics":

    st.markdown('<div class="pluto-title">Analytics</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="pluto-subtitle">Financial trends and performance</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title">Top Clients by Outstanding Amount</div>',
        unsafe_allow_html=True,
    )

    outstanding = client_outstanding(df)
    st.bar_chart(outstanding.head(10), x="client_name", y="balance_due")

    st.markdown('<div class="section-title">Invoice Cash Flow</div>', unsafe_allow_html=True)

    monthly = forecast_invoice_cashflow(df)
    st.line_chart(monthly, x="invoice_date", y="total_amount")

    prediction = predict_next_month(monthly)
    st.metric("Predicted Next Month Invoice Amount", f"₹{prediction:,.0f}")


# ==================================================
# ALERTS
# ==================================================

if page == "⚠ Alerts":

    st.markdown('<div class="pluto-title">Alerts</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="pluto-subtitle">Invoices requiring attention</div>',
        unsafe_allow_html=True,
    )

    alerts = find_invoice_alerts(df)

    st.write(f"{len(alerts)} invoices need attention.")

    for alert in alerts[:15]:

        if alert["type"] == "Overdue":
            st.error(
                f"🔴 {alert['invoice_number']} — "
                f"{alert['client']} — "
                f"₹{alert['amount_due']:,.2f}"
            )
        else:
            st.warning(
                f"🟣 {alert['invoice_number']} — "
                f"{alert['client']} — "
                f"₹{alert['amount_due']:,.2f}"
            )


# ==================================================
# AI ASSISTANT
# ==================================================

if page == "✦ AI Assistant":

    st.markdown(
        '<div class="pluto-title">AI Finance Assistant</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="pluto-subtitle">Ask questions about your invoice data</div>',
        unsafe_allow_html=True,
    )

    question = st.text_input("Ask PLUTO24", placeholder="e.g. How much is outstanding?")

    if question:
        answer = ask_question(question, df)
        st.info(answer)