import streamlit as st
from auth import service, session
from components import ui
from components.compat import STRETCH
from utils.validation import ValidationError

def render():
    _, mid, _ = st.columns([1, 1.25, 1])
    with mid:
        st.markdown(f'<div class="auth-brand"><span class="fs-logo">{ui.icon("chart", 22)}</span><b>FinScope AI</b>'
                    '<p>Understand Your Debt. Make Smarter Financial Decisions.</p></div>', unsafe_allow_html=True)
        if st.session_state.get("notice"): st.info(st.session_state.pop("notice"))
        tab_in, tab_up = st.tabs(["Sign in", "Create account"])
        with tab_in, st.container(border=True):
            with st.form("login"):
                u = st.text_input("Username"); p = st.text_input("Password", type="password")
                if st.form_submit_button("Sign in", **STRETCH):
                    try:
                        session.login_user(service.authenticate(u, p)); st.rerun()
                    except ValidationError as e: st.error(str(e))
        with tab_up, st.container(border=True):
            with st.form("register"):
                n = st.text_input("Name (optional)"); u = st.text_input("Choose a username")
                p = st.text_input("Password", type="password", help="At least 8 characters with a letter and a number")
                c = st.text_input("Confirm password", type="password")
                st.caption("Never enter banking passwords, card PINs or OTPs anywhere in this app.")
                if st.form_submit_button("Create account", **STRETCH):
                    try:
                        service.register(u, p, c, n); st.success("Account created. You can sign in now.")
                    except ValidationError as e: st.error(str(e))
