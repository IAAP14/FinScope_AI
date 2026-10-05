"""FEATURE 6: Financial Health Dashboard (home page after login)."""
from datetime import datetime
import streamlit as st
from components import ui, charts
from components.compat import plot, STRETCH
from components.navigation import quick_link
from utils.finance import RISK_TEXT, warnings, drivers
from utils.format import fmt, pct

def _greeting():
    h = datetime.now().hour
    return "Good morning" if h < 12 else "Good afternoon" if h < 17 else "Good evening"

def _ask_ai(question):
    st.session_state["pending_q"] = question
    st.session_state["page"] = "AI Financial Explanation"

def render(ctx):
    m, name = ctx["m"], ctx["user"]["name"].split()[0]
    st.markdown(f'<div class="hello"><h1>{_greeting()}, {name}</h1><p>Here\'s a simple view of your financial health.</p></div>', unsafe_allow_html=True)
    if not m:
        return ui.empty("fh", ctx)

    # 1. four key cards
    k = st.columns(4)
    with k[0]: ui.status_kpi("Financial Health", m["health"].upper(), "Overall picture today", m["health_status"], "pulse")
    with k[1]: ui.status_kpi("Debt Risk", m["level"].title(), "Based on your debt and income", m["status"], "shield")
    with k[2]: ui.kpi("Monthly EMI", fmt(m["emi"]), f"{pct(m['emi_r'])} of your income", "card")
    with k[3]: ui.kpi("Remaining Income", fmt(m["remaining"]), "After all spending and EMIs", "wallet")
    st.write("")

    # 2. overview chart + key numbers
    a, b = st.columns([3, 2])
    with a, st.container(border=True):
        ui.section("Your Financial Overview", "Where your monthly income goes", "chart")
        plot(charts.flow(m, 300))
    with b, st.container(border=True):
        ui.section("Key numbers", "At a glance", "coins")
        repaid = f"{m['repaid'] / m['original']:.0%}" if m["has_repaid"] and m["original"] > 0 else "Add original amounts"
        ui.mini_grid([("Monthly income", fmt(m["inc"])), ("Monthly expenses", fmt(m["ess"] + m["non"] + m["commit"])),
                      ("Existing EMI", fmt(m["emi"])), ("Outstanding debt", fmt(m["debt"])),
                      ("Debt vs yearly income", f"{m['dti']:.1f}x"), ("Disposable income", fmt(m["avail"])),
                      ("Repaid so far", repaid), ("Active loans", m["n"])])
    st.write("")

    # 3. what's affecting + warnings
    a, b = st.columns(2)
    with a, st.container(border=True):
        ui.section("What's affecting your financial health?", RISK_TEXT[m["level"]], "bulb")
        for status, title, text in drivers(m): ui.insight(status, title, text, "pulse")
    with b, st.container(border=True):
        ui.section("Important Warnings", "Only shown when something needs attention", "alert")
        ws = warnings(m)
        if not ws: ui.insight("ok", "No warnings right now", "Based on the information entered, nothing needs urgent attention.", "check")
        for w in ws[:4]: ui.insight(w["status"], w["title"], w["text"], "alert")
    st.write("")

    # 4. quick actions
    with st.container(border=True):
        ui.section("Quick Actions", "Jump straight to what you need", "target")
        q = st.columns(4)
        with q[0]: quick_link("Check Loan Affordability", "Loan Affordability", "qa_la", "calculate", True)
        with q[1]: quick_link("Analyze Debt Risk", "Debt Risk Analyzer", "qa_dr", "shield")
        with q[2]: quick_link("Run What-If", "What-If Simulator", "qa_wi", "tune")
        with q[3]: quick_link("View Repayment", "Debt Repayment Analyzer", "qa_rp", "flag")
    st.write("")

    # 5. ask FinScope AI
    st.markdown('<div class="ask"><b>Ask FinScope AI</b><p>Get a plain-language explanation of your numbers, for example '
                '"Why is my debt risk moderate?"</p></div>', unsafe_allow_html=True)
    with st.form("dash_ask", clear_on_submit=True):
        c = st.columns([5, 1])
        text = c[0].text_input("Your question", placeholder="Why is my debt risk " + m["level"].lower() + "?", label_visibility="collapsed")
        if c[1].form_submit_button("Ask", **STRETCH):
            _ask_ai(text.strip() or f"Why is my debt risk {m['level'].lower()}?"); st.rerun()
    ui.disclaimer()
