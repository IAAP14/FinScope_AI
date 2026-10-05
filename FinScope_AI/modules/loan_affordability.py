"""FEATURE 1: Loan Affordability - 'Can I afford this new loan?'"""
import streamlit as st
from components import ui, charts
from components.compat import plot
from components.navigation import back_to_home
from utils.finance import compute, scenario, emi_for, affordability, affordability_text, ratio_status
from utils.format import fmt, pct

def render(ctx):
    m, p = ctx["m"], ctx["profile"]
    back_to_home()
    ui.header("Loan Affordability", "Can I afford this new loan? Check how it may affect your monthly budget before you decide.")
    if not m: return ui.empty("la", ctx)
    a, b = st.columns([1, 1.55])
    with a, st.container(border=True):
        ui.section("Proposed loan", "Enter the offer you are considering", "calc")
        amt = st.number_input("Loan amount", min_value=0.0, value=300000.0, step=10000.0)
        rate = st.number_input("Interest rate (% per year)", min_value=0.0, max_value=100.0, value=10.5, step=0.25)
        yrs = st.number_input("Loan tenure (years)", min_value=0.5, max_value=40.0, value=3.0, step=0.5)
        st.markdown("**Your current position**")
        ui.stat("Monthly income", fmt(m["inc"])); ui.stat("Monthly expenses", fmt(m["ess"] + m["non"] + m["commit"]))
        ui.stat("Existing EMI", fmt(m["emi"])); ui.stat("Existing burden", pct(m["emi_r"]) + " of income")
    with b, st.container(border=True):
        ui.section("Affordability result", "Estimated under the loan terms entered", "shield")
        if amt <= 0: return st.info("Please enter a loan amount greater than zero to see the result.")
        months = int(round(yrs * 12))
        new_emi = emi_for(amt, rate, months); total = new_emi * months
        m2 = compute(scenario(p, new_loan=dict(amount=amt, rate=rate, years=yrs)))
        if m2 is None: return st.warning("Please enter a valid monthly income in My Finances first.")
        verdict, status = affordability(m, m2, new_emi)
        ui.verdict(status, verdict.upper(), affordability_text(verdict, m, m2, new_emi), "AFFORDABILITY")
        c = st.columns(3)
        with c[0]: ui.kpi("Estimated EMI", fmt(new_emi), "Proposed monthly payment", "card")
        with c[1]: ui.kpi("Remaining income", fmt(m2["remaining"]), "After spending and all EMIs", "wallet")
        with c[2]: ui.kpi("Total interest", fmt(max(total - amt, 0)), f"Total repayment {fmt(total)}", "coins")
        st.write("")
        ui.meter("EMI-to-income ratio", f"{pct(m['emi_r'])} to {pct(m2['emi_r'])}", m2["emi_r"] / .6, ratio_status(m2["emi_r"], .3, .45))
        ui.mini_grid([("Existing burden", pct(m["emi_r"])), ("New burden", pct(m2["emi_r"])),
                      ("Debt risk", f"{m['level'].title()} to {m2['level'].title()}")])
        ui.note("loan affordability check", f"A {fmt(amt)} loan at {rate}% for {yrs} years would have an EMI of about {fmt(new_emi)}; "
                f"EMIs would go from {pct(m['emi_r'])} to {pct(m2['emi_r'])} of income, remaining income {fmt(m2['remaining'])}, "
                f"verdict '{verdict}', debt risk {m['level']} to {m2['level']}.")
    st.write("")
    c1, c2 = st.columns(2)
    with c1, st.container(border=True):
        ui.section("Before and after", "Monthly amounts", "chart")
        plot(charts.before_after([("EMI", m["emi"], m2["emi"]), ("Available income", m["avail"], m2["avail"]),
                                  ("Left after spending", m["remaining"], m2["remaining"])]))
    with c2, st.container(border=True):
        ui.section("Income allocation after the loan", "Share of monthly income", "pulse")
        plot(charts.allocation(m2, 300))
    ui.disclaimer()
