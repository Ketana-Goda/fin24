import streamlit as st

import db


def require_login():
    """Show a login screen until the user signs in. Returns the user dict."""
    if st.session_state.get("user"):
        user = st.session_state["user"]
        with st.sidebar:
            st.caption(f"Signed in as **{user['username']}** ({user['role']})")
            if st.button("Log out"):
                st.session_state.pop("user", None)
                st.rerun()
        return user

    st.title("🔐 PLUTO24 Login")
    st.caption("Sign in to continue.")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")

    if submitted:
        role = db.check_login(username.strip(), password)
        if role:
            st.session_state["user"] = {"username": username.strip(), "role": role}
            st.rerun()
        else:
            st.error("Wrong username or password.")

    st.stop()  # nothing below this runs until logged in