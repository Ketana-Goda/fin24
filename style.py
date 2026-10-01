import streamlit as st

CSS = """
<style>
[data-testid="stMetric"] {
    background: #F4F6FB;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 14px 18px;
}
[data-testid="stMetricValue"] { color: #4F46E5; }
[data-testid="stSidebar"] { border-right: 1px solid #E5E7EB; }
h1 { font-weight: 800; }
.block-container { padding-top: 2rem; }
footer { visibility: hidden; }
</style>
"""


def apply_style():
    st.markdown(CSS, unsafe_allow_html=True)