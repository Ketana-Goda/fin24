import streamlit as st

CSS = """
<style>
[data-testid="stMetric"] {
    background: #1A1433;
    border: 1px solid #2E2552;
    border-radius: 12px;
    padding: 14px 18px;
}
[data-testid="stMetricValue"] { color: #A78BFA; }
[data-testid="stSidebar"] { border-right: 1px solid #2E2552; }
[data-testid="stExpander"] {
    background: #1A1433;
    border: 1px solid #2E2552;
    border-radius: 10px;
}
h1, h2, h3 { color: #EDE9FE; }
h1 { font-weight: 800; }
.block-container { padding-top: 2rem; }
footer { visibility: hidden; }
</style>
"""


def apply_style():
    st.markdown(CSS, unsafe_allow_html=True)