import os

import pandas as pd
import streamlit as st

from auth import require_login
from detect import find_recurring, forecast_upcoming
from insights import build_alerts
from loaders import load_standard
from style import apply_style


st.set_page_config(page_title="Finance Assistant", layout="wide")
apply_style()
require_login()

st.title("🤖 Finance Assistant")
st.caption("Answers are calculated from the transaction data, not guessed. "
           "Each answer shows the numbers behind it.")

# ---------- Data ----------
uploaded = st.sidebar.file_uploader("Upload expense transactions CSV", type=["csv"])
if uploaded is not None:
    raw = pd.read_csv(uploaded)
else:
    path = "data/sample_dept.csv" if os.path.exists("data/sample_dept.csv") else "data/sample.csv"
    raw = pd.read_csv(path)
    st.sidebar.info("Using synthetic demo expense ledger (not real company data)")

try:
    df = load_standard(raw)
except ValueError as e:
    st.error(f"Could not read this file: {e}")
    st.stop()

as_of = df["date"].max()
recurring = find_recurring(df)
if recurring.empty:
    st.warning("No recurring expenses were detected in this data.")
    st.stop()

alerts = build_alerts(df, recurring)
dept_by_key = df.groupby("vendor_key")["department"].agg(lambda s: s.mode().iloc[0])
recurring["department"] = recurring["vendor"].str.lower().map(dept_by_key).fillna("Unassigned")
active = recurring[recurring["status"] == "Active"]


# ---------- Answer functions (each returns text, table) ----------
def q_biggest():
    top = active.head(5)
    share = top["monthly_equivalent"].sum() / active["monthly_equivalent"].sum()
    text = ("Your largest recurring expenses are "
            + ", ".join(f"**{r.vendor}** (₹{r.monthly_equivalent:,.0f}/month)"
                        for r in top.itertuples())
            + f". Together they are about ₹{top['monthly_equivalent'].sum():,.0f} per month, "
              f"{share:.0%} of all recurring commitments.")
    cols = ["vendor", "department", "frequency", "monthly_equivalent", "annual_cost"]
    return text, top[cols]


def q_renewals():
    up = forecast_upcoming(recurring, as_of, 30)
    text = (f"**{len(up)} recurring payments** totalling **₹{up['amount'].sum():,.0f}** "
            f"are expected in the next 30 days (from {as_of:%d %b %Y}).")
    up = up.copy()
    up["date"] = up["date"].dt.strftime("%d %b %Y")
    return text, up


def q_review():
    if not alerts:
        return "Nothing needs review right now.", None
    text = (f"**{len(alerts)} items** may need review: "
            + "; ".join(a["title"] for a in alerts)
            + ". These are flags based on payment patterns only. "
              "The final decision belongs to the finance team.")
    table = pd.DataFrame(alerts)[["severity", "type", "title", "impact_text"]]
    return text, table


def q_reduce():
    rows = []
    for a in alerts:
        if a["type"] == "Potential duplicate":
            g = active[active["vendor"].isin(a["vendors"])]
            saving = (g["monthly_equivalent"].sum() - g["monthly_equivalent"].max()) * 12
            rows.append({"area": a["title"],
                         "vendors": ", ".join(a["vendors"]),
                         "possible annual saving (₹)": round(saving)})
    if not rows:
        return "I did not find overlapping subscriptions to consolidate.", None
    total = sum(r["possible annual saving (₹)"] for r in rows)
    text = (f"The clearest review area is **overlapping subscriptions**. If each group "
            f"were consolidated to its single most expensive tool, the saving would be "
            f"up to **₹{total:,.0f} per year**. This is an estimate for review, not a "
            f"recommendation to cancel. Without usage data, I cannot tell which tools "
            f"are actually used.")
    return text, pd.DataFrame(rows)


def q_dept():
    by = (active.groupby("department")["monthly_equivalent"].sum()
          .sort_values(ascending=False).reset_index())
    by.columns = ["department", "monthly recurring (₹)"]
    by["monthly recurring (₹)"] = by["monthly recurring (₹)"].round()
    top = by.iloc[0]
    text = (f"**{top['department']}** has the largest recurring commitment "
            f"(₹{top['monthly recurring (₹)']:,.0f} per month). Full split below.")
    return text, by


def q_price():
    rises = [a for a in alerts if a["type"] == "Price increase"]
    if not rises:
        return "I did not detect meaningful price increases.", None
    text = ("Rising costs detected: " + "; ".join(a["title"] for a in rises)
            + ". Worth checking whether the plan or usage changed.")
    table = pd.DataFrame(rises)[["severity", "title", "impact_text"]]
    return text, table


PRESETS = {
    "What are our biggest recurring expenses?": q_biggest,
    "What renews in the next 30 days?": q_renewals,
    "Which subscriptions should we review?": q_review,
    "Where could we reduce spending?": q_reduce,
    "How much do we spend per department?": q_dept,
    "Which expenses are rising in price?": q_price,
}

KEYWORDS = [  # checked in this order
    (["price", "increase", "rising", "hike"], "Which expenses are rising in price?"),
    (["department", "team", "allocation"], "How much do we spend per department?"),
    (["save", "saving", "reduce", "cut", "cancel"], "Where could we reduce spending?"),
    (["review", "flag", "alert", "duplicate", "overlap", "unnecessary"],
     "Which subscriptions should we review?"),
    (["renew", "upcoming", "due", "next month", "next 30", "forecast", "expect", "pay next"],
     "What renews in the next 30 days?"),
    (["biggest", "largest", "top", "most", "highest", "recurring"],
     "What are our biggest recurring expenses?"),
]

# ---------- Chat UI ----------
if "history" not in st.session_state:
    st.session_state.history = []


def ask(label):
    text, table = PRESETS[label]()
    st.session_state.history.append((label, text, table))


st.write("**Try a question:**")
cols = st.columns(3)
for i, label in enumerate(PRESETS):
    if cols[i % 3].button(label, use_container_width=True):
        ask(label)

typed = st.chat_input("Ask about recurring expenses, renewals, savings...")
if typed:
    lowered = typed.lower()
    match = next((label for words, label in KEYWORDS if any(w in lowered for w in words)), None)
    if match:
        text, table = PRESETS[match]()
        st.session_state.history.append((typed, text, table))
    else:
        st.session_state.history.append((
            typed,
            "I can answer questions about recurring expenses, upcoming renewals, "
            "items to review, possible savings, department costs and price increases. "
            "Try one of the buttons above.",
            None))

for question, text, table in st.session_state.history:
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        st.markdown(text)
        if table is not None:
            st.dataframe(table, use_container_width=True, hide_index=True)