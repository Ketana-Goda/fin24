import streamlit as st
import pandas as pd
import requests
import os

from style import apply_style
from agent import ask_question
from dotenv import load_dotenv
from detect import forecast_invoice_cashflow, predict_next_month
from insights import (
    get_dashboard_summary,
    client_outstanding,
    find_invoice_alerts
)


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
    initial_sidebar_state="expanded"
)
apply_style()

# ==================================================
# PLUTO24 DARK / NEON UI
# ==================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');


/* -------------------------------------------------
   MAIN APP
------------------------------------------------- */

.stApp {
    background:
        radial-gradient(
            circle at 10% 10%,
            rgba(139, 92, 246, 0.15),
            transparent 30%
        ),
        radial-gradient(
            circle at 90% 20%,
            rgba(217, 70, 239, 0.10),
            transparent 25%
        ),
        #08060d;

    color: #f5f3ff;
    font-family: 'Inter', sans-serif;
}


/* -------------------------------------------------
   MAIN CONTENT
------------------------------------------------- */

.block-container {
    max-width: 1500px;
    padding-top: 2.5rem;
    padding-left: 2rem;
    padding-right: 2rem;
    padding-bottom: 3rem;
}


/* -------------------------------------------------
   SIDEBAR
------------------------------------------------- */

section[data-testid="stSidebar"] {
    background:
        linear-gradient(
            180deg,
            #100a1c 0%,
            #09070f 100%
        );

    border-right:
        1px solid rgba(139, 92, 246, 0.25);
}


section[data-testid="stSidebar"] * {
    color: #ddd6fe;
}


/* Sidebar navigation */

.stRadio label {
    padding: 10px 12px;
    border-radius: 10px;
    transition: all 0.25s ease;
}


.stRadio label:hover {
    background:
        rgba(139, 92, 246, 0.15);

    box-shadow:
        0 0 18px rgba(139, 92, 246, 0.18);
}


/* -------------------------------------------------
   PLUTO24 TITLE
------------------------------------------------- */

.pluto-title {
    font-size: 42px;
    font-weight: 700;
    letter-spacing: -1px;

    background:
        linear-gradient(
            90deg,
            #c4b5fd,
            #a855f7,
            #e879f9
        );

    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;

    margin-bottom: 2px;
}


.pluto-subtitle {
    color: #a8a1b8;
    font-size: 15px;
    margin-bottom: 32px;
}


/* -------------------------------------------------
   METRIC CARDS
------------------------------------------------- */

.metric-card {

    box-sizing: border-box;

    width: 100%;

    background:
        linear-gradient(
            145deg,
            rgba(30, 20, 45, 0.95),
            rgba(14, 9, 22, 0.95)
        );

    border:
        1px solid rgba(139, 92, 246, 0.30);

    border-radius: 18px;

    padding: 22px;

    min-height: 125px;

    transition:
        transform 0.3s ease,
        border-color 0.3s ease,
        box-shadow 0.3s ease;
}


.metric-card:hover {

    transform:
        translateY(-5px);

    border-color:
        #a855f7;

    box-shadow:
        0 0 20px rgba(139, 92, 246, 0.35),
        0 0 40px rgba(168, 85, 247, 0.15);
}


.metric-label {

    color: #a8a1b8;

    font-size: 14px;

    margin-bottom: 12px;
}


.metric-value {

    color: #f5f3ff;

    font-size: 26px;

    font-weight: 700;
}


/* -------------------------------------------------
   SECTION HEADINGS
------------------------------------------------- */

.section-title {

    font-size: 21px;

    font-weight: 600;

    color: #ede9fe;

    margin-top: 35px;

    margin-bottom: 18px;
}


/* -------------------------------------------------
   BUTTONS
------------------------------------------------- */

.stButton > button {

    background:
        rgba(139, 92, 246, 0.12);

    color: #ddd6fe;

    border:
        1px solid rgba(139, 92, 246, 0.35);

    border-radius: 10px;

    transition: all 0.25s ease;
}


.stButton > button:hover {

    background:
        rgba(139, 92, 246, 0.25);

    border-color:
        #a855f7;

    box-shadow:
        0 0 18px rgba(168, 85, 247, 0.25);
}


/* -------------------------------------------------
   TEXT INPUT
------------------------------------------------- */

.stTextInput input {

    background:
        rgba(15, 10, 24, 0.90);

    color: #f5f3ff;

    border:
        1px solid rgba(139, 92, 246, 0.30);

    border-radius: 12px;
}


.stTextInput input:focus {

    border-color:
        #a855f7;

    box-shadow:
        0 0 15px rgba(168, 85, 247, 0.18);
}


/* -------------------------------------------------
   DATAFRAME
------------------------------------------------- */

div[data-testid="stDataFrame"] {

    border:
        1px solid rgba(139, 92, 246, 0.20);

    border-radius: 14px;

    overflow: hidden;
}


/* -------------------------------------------------
   DIVIDERS
------------------------------------------------- */

hr {

    border-color:
        rgba(139, 92, 246, 0.15) !important;
}


/* -------------------------------------------------
   HIDE STREAMLIT DEFAULT UI
------------------------------------------------- */

#MainMenu {
    visibility: hidden;
}


footer {
    visibility: hidden;
}

</style>
""", unsafe_allow_html=True)


# ==================================================
# ACZEN API
# ==================================================

API_KEY = os.getenv("ACZEN_API_KEY")
BASE_URL = os.getenv("ACZEN_BASE_URL")


url = BASE_URL + "/invoices?limit=300"


headers = {
    "Authorization": f"Bearer {API_KEY}"
}


response = requests.get(
    url,
    headers=headers
)


if response.status_code != 200:

    st.error(
        "Unable to load invoice data from Aczen."
    )

    st.stop()


data = response.json()


df = pd.DataFrame(
    data["data"]
)
# Get dashboard summary
summary = get_dashboard_summary(df)

# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:

    st.markdown(
        '<div style="text-align:center; padding:10px 0 25px 0;">'
        '<div style="font-size:34px; font-weight:700; color:#c4b5fd; '
        'text-shadow:0 0 10px rgba(168,85,247,0.5), '
        '0 0 25px rgba(168,85,247,0.3);">'
        '✦ PLUTO24'
        '</div>'
        '<div style="font-size:11px; color:#8f879f; '
        'letter-spacing:2px; margin-top:6px;">'
        'FINANCE INTELLIGENCE'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown("### Navigation")

    page = st.radio(
        "",
        [
            "◉ Dashboard",
            "◈ Invoices",
            "◇ Analytics",
            "⚠ Alerts",
            "✦ AI Assistant"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")

    st.caption("Powered by Aczen Nova API")
# ==================================================
# DASHBOARD
# ==================================================

if page == "◉ Dashboard":

    st.markdown(
        '<div class="pluto-title">PLUTO24</div>',
        unsafe_allow_html=True
    )


    st.markdown(
        '<div class="pluto-subtitle">'
        'Finance Intelligence & Invoice Monitoring'
        '</div>',
        unsafe_allow_html=True
    )


    # Dashboard summary

    summary = get_dashboard_summary(df)

# --------------------------------------------------
# KPI CARDS
# --------------------------------------------------

col1, col2, col3, col4 = st.columns(4, gap="medium")

with col1:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">Total Invoices</div><div class="metric-value">{summary["total_invoices"]}</div></div>',
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">Total Invoiced</div><div class="metric-value">₹{summary["total_amount"]:,.0f}</div></div>',
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">Amount Paid</div><div class="metric-value">₹{summary["paid_amount"]:,.0f}</div></div>',
        unsafe_allow_html=True
    )

with col4:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">Outstanding</div><div class="metric-value">₹{summary["outstanding"]:,.0f}</div></div>',
        unsafe_allow_html=True
    )


st.markdown(
    '<div class="section-title">Overview</div>',
    unsafe_allow_html=True
)

st.write(
    "PLUTO24 provides centralized invoice monitoring, "
    "payment tracking, alerts and financial insights."
)


# ==================================================
# INVOICES
# ==================================================

if page == "◈ Invoices":

    st.markdown(
        '<div class="pluto-title">Invoices</div>',
        unsafe_allow_html=True
    )


    st.markdown(
        '<div class="pluto-subtitle">'
        'View and monitor invoice records'
        '</div>',
        unsafe_allow_html=True
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
                "due_date"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )


# ==================================================
# ANALYTICS
# ==================================================

if page == "◇ Analytics":

    st.markdown(
        '<div class="pluto-title">Analytics</div>',
        unsafe_allow_html=True
    )


    st.markdown(
        '<div class="pluto-subtitle">'
        'Financial trends and performance'
        '</div>',
        unsafe_allow_html=True
    )


    # --------------------------------------------------
    # TOP CLIENTS
    # --------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        'Top Clients by Outstanding Amount'
        '</div>',
        unsafe_allow_html=True
    )


    outstanding = client_outstanding(df)


    st.bar_chart(
        outstanding.head(10),
        x="client_name",
        y="balance_due"
    )


    # --------------------------------------------------
    # CASH FLOW
    # --------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        'Invoice Cash Flow'
        '</div>',
        unsafe_allow_html=True
    )


    monthly = forecast_invoice_cashflow(df)


    st.line_chart(
        monthly,
        x="invoice_date",
        y="total_amount"
    )


    # --------------------------------------------------
    # PREDICTION
    # --------------------------------------------------

    prediction = predict_next_month(
        monthly
    )


    st.metric(
        "Predicted Next Month Invoice Amount",
        f"₹{prediction:,.0f}"
    )


# ==================================================
# ALERTS
# ==================================================

if page == "⚠ Alerts":

    st.markdown(
        '<div class="pluto-title">Alerts</div>',
        unsafe_allow_html=True
    )


    st.markdown(
        '<div class="pluto-subtitle">'
        'Invoices requiring attention'
        '</div>',
        unsafe_allow_html=True
    )


    alerts = find_invoice_alerts(df)


    st.write(
        f"{len(alerts)} invoices need attention."
    )


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
        '<div class="pluto-title">'
        'AI Finance Assistant'
        '</div>',
        unsafe_allow_html=True
    )


    st.markdown(
        '<div class="pluto-subtitle">'
        'Ask questions about your invoice data'
        '</div>',
        unsafe_allow_html=True
    )


    question = st.text_input(
        "Ask PLUTO24",
        placeholder="e.g. How much is outstanding?"
    )


    if question:

        answer = ask_question(
            question,
            df
        )


        st.info(
            answer
        )