"""Sidebar navigation + a 'Financial Health' button on every other page, so users are never stuck."""
import streamlit as st
from components import ui
from components.compat import STRETCH

HOME = "Financial Health"
NAV = [("FINANCIAL OVERVIEW", [(HOME, "monitoring")]),
       ("MY FINANCES", [("My Finances", "account_balance_wallet"), ("Loan Affordability", "calculate"),
                        ("Debt Risk Analyzer", "shield"), ("What-If Simulator", "tune")]),
       ("DEBT MANAGEMENT", [("Debt Repayment Analyzer", "flag")]),
       ("AI INSIGHTS", [("AI Financial Explanation", "smart_toy")])]
SETTINGS = [("Profile & Settings", "settings"), ("Privacy", "privacy_tip")]

def go(name):
    st.session_state["page"] = name

def _button(name, icon, key_prefix="nav"):
    st.button(name, key=f"{key_prefix}_{name}", icon=f":material/{icon}:", **STRETCH,
              type="primary" if st.session_state.get("page") == name else "secondary", on_click=go, args=(name,))

def sidebar(user, logout_cb):
    with st.sidebar:
        st.markdown(f'<div class="fs-brand"><span class="fs-logo">{ui.icon("chart", 20)}</span>'
                    '<div><b>FinScope AI</b><small>Understand your debt</small></div></div>', unsafe_allow_html=True)
        for section, items in NAV:
            st.markdown(f'<div class="fs-nav-h">{section}</div>', unsafe_allow_html=True)
            for name, ic in items: _button(name, ic)
        st.markdown('<div class="fs-nav-h">SETTINGS</div>', unsafe_allow_html=True)
        for name, ic in SETTINGS: _button(name, ic)
        st.markdown(f'<div class="sb-user"><span class="av">{user["name"][:1].upper()}</span>'
                    f'<div><b>{user["name"]}</b><small>@{user["username"]}</small></div></div>', unsafe_allow_html=True)
        if st.button("Log out", key="logout", icon=":material/logout:", **STRETCH): logout_cb()

def back_to_home():
    """Shown above every page except the dashboard (also helps when the sidebar is collapsed on a phone)."""
    if st.session_state.get("page") != HOME:
        st.button("Back to Financial Health", key="back_home", icon=":material/arrow_back:", on_click=go, args=(HOME,))

def quick_link(label, page, key, icon, primary=False):
    st.button(label, key=key, icon=f":material/{icon}:", **STRETCH, type="primary" if primary else "secondary", on_click=go, args=(page,))
