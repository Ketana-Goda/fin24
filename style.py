import streamlit as st

CSS = """
<style>
[data-testid="stMetric"] {
    background: #F5F3FF;
    border: 1px solid #DDD6FE;
    border-radius: 12px;
    padding: 14px 18px;
}
[data-testid="stMetricValue"] { color: #6D28D9; }
[data-testid="stSidebar"] { border-right: 1px solid #DDD6FE; }
[data-testid="stExpander"] {
    background: #FAF9FF;
    border: 1px solid #DDD6FE;
    border-radius: 10px;
}
h1, h2, h3 { color: #1F1B2E; }
h1 { font-weight: 800; }
.block-container { padding-top: 2rem; }
footer { visibility: hidden; }
</style>
"""


def apply_style():
    st.markdown(CSS, unsafe_allow_html=True)