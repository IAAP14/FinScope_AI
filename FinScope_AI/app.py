"""FinScope AI - entry point.  Run:  python -m streamlit run app.py"""
import streamlit as st

st.set_page_config(page_title="FinScope AI", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

from auth import session, ui as auth_ui
from components import ui
from components import navigation as nav
from database import repository as repo
from database.db import init_db
from modules import (financial_health, my_finances, loan_affordability, debt_risk, what_if, repayment,
                     ai_assistant, settings, privacy)
from utils.finance import compute

PAGES = {nav.HOME: financial_health, "My Finances": my_finances, "Loan Affordability": loan_affordability,
         "Debt Risk Analyzer": debt_risk, "What-If Simulator": what_if, "Debt Repayment Analyzer": repayment,
         "AI Financial Explanation": ai_assistant, "Profile & Settings": settings, "Privacy": privacy}

@st.cache_resource
def _setup():
    """One-time start-up: create the database and load (or first-time train) the debt-risk model."""
    init_db()
    try:
        from ml.predict import ensure_model
        ensure_model()
    except Exception:
        pass
    return True

def _logout():
    session.logout(); st.rerun()

def main():
    _setup(); ui.load_css()
    user = session.current_user()
    if not user: return auth_ui.render()
    if st.session_state.get("page") not in PAGES: st.session_state["page"] = nav.HOME
    nav.sidebar(user, _logout)
    if st.session_state.get("notice_ok"): st.success(st.session_state.pop("notice_ok"))
    try:
        profile = repo.get_profile(user["id"])
        ctx = dict(user=user, profile=profile, m=compute(profile), records=repo.list_records(user["id"]))
        PAGES[st.session_state["page"]].render(ctx)
    except Exception:
        st.error("Something went wrong loading this page. Please try again or go back to Financial Health.")
        st.button("Back to Financial Health", key="err_home", on_click=nav.go, args=(nav.HOME,))

main()
