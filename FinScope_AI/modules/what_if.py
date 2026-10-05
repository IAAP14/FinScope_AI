"""FEATURE 3: What-If Simulator - 'What happens if my financial situation changes?'
Nothing is saved unless the user explicitly applies the scenario at the bottom."""
import streamlit as st
from components import ui, charts
from components.compat import plot, STRETCH
from components.navigation import back_to_home
from database import repository as repo
from utils.finance import compute, scenario, simulate_repayment, RISK_TEXT
from utils.format import fmt, fmt_months, pct
from utils.validation import ValidationError

def _card(title, m, months):
    st.markdown(f'<div class="ba-title">{title}</div>', unsafe_allow_html=True)
    ui.mini_grid([("EMI", fmt(m["emi"])), ("Debt burden", f"{pct(m['emi_r'])} of income"), ("Disposable income", fmt(m["avail"])),
                  ("Debt vs yearly income", f"{m['dti']:.1f}x"), ("Debt risk", ui.badge(m["status"], m["level"])),
                  ("Financial health", ui.badge(m["health_status"], m["health"])), ("Repayment period", fmt_months(months))])

def _explain(m, m2):
    rank = {"LOW": 0, "MODERATE": 1, "HIGH": 2}
    d = rank[m2["level"]] - rank[m["level"]]
    core = (f"EMIs would move from {pct(m['emi_r'])} to {pct(m2['emi_r'])} of income, and the money left each month from "
            f"{fmt(m['remaining'])} to {fmt(m2['remaining'])}.")
    if d > 0: return "bad" if m2["level"] == "HIGH" else "warn", f"Debt risk would rise from {m['level'].title()} to {m2['level'].title()}. {core} {RISK_TEXT[m2['level']]}"
    if d < 0: return "ok", f"Debt risk would improve from {m['level'].title()} to {m2['level'].title()}. {core}"
    return ("ok" if m2["level"] == "LOW" else "warn" if m2["level"] == "MODERATE" else "bad",
            f"Debt risk would stay {m2['level'].title()}. {core}")

def render(ctx):
    m, p = ctx["m"], ctx["profile"]
    back_to_home()
    ui.header("What-If Simulator", "What happens if my situation changes? Try changes freely - your saved finances stay untouched.")
    if not m: return ui.empty("wi", ctx)
    a, b = st.columns([1, 1.7])
    with a, st.container(border=True):
        ui.section("Adjust the scenario", "Compared with your situation today", "sliders")
        di = st.slider("Monthly income change (%)", -50, 50, 0)
        de = st.slider("Monthly expenses change (%)", -30, 50, 0, help="Applies to essential expenses")
        dn = st.slider("Non-essential spending change (%)", -100, 50, 0)
        dm = st.slider("Existing EMI change (%)", -50, 50, 0, help="For example after refinancing")
        ex = st.number_input("Additional monthly repayment", min_value=0.0, value=0.0, step=500.0)
        st.markdown("**New loan (optional)**")
        la = st.number_input("New loan amount", min_value=0.0, value=0.0, step=10000.0, key="wi_la")
        lr = st.number_input("Interest rate (% per year)", min_value=0.0, max_value=100.0, value=10.5, step=0.25, key="wi_lr")
        ly = st.number_input("Tenure (years)", min_value=0.5, max_value=40.0, value=3.0, step=0.5, key="wi_ly")
    q = scenario(p, di, de, dn, dm, dict(amount=la, rate=lr, years=ly), extra=ex)
    m2 = compute(q)
    if m2 is None: return st.warning("This scenario leaves no income. Please adjust the income change.")
    sim0, sim1 = simulate_repayment(m["loans"]), simulate_repayment(q["loans"], ex)
    status, text = _explain(m, m2)
    with b:
        ui.verdict(status, f"{m['level'].title()} to {m2['level'].title()}", text, "DEBT RISK: CURRENT TO SIMULATED")
        with st.container(border=True):
            ui.section("Current vs simulated situation", "Estimated under the selections on the left", "chart")
            c1, c2 = st.columns(2)
            with c1: _card("CURRENT SITUATION", m, sim0["months"])
            with c2: _card("SIMULATED SITUATION", m2, sim1["months"])
            st.write("")
            plot(charts.before_after([("Income", m["inc"], m2["inc"]), ("Expenses", m["ess"] + m["non"] + m["commit"], m2["ess"] + m2["non"] + m2["commit"]),
                                      ("EMI", m["emi"], m2["emi"]), ("Disposable", m["avail"], m2["avail"])]))
            if m2["remaining"] < 0:
                ui.insight("bad", "This scenario overspends", f"It leaves you {fmt(-m2['remaining'])} short each month. Consider smaller changes.", "alert")
    ui.note("what-if simulation", f"Debt risk {m['level']} to {m2['level']}; financial health {m['health']} to {m2['health']}; EMI {fmt(m['emi'])} to {fmt(m2['emi'])}; "
            f"money left each month {fmt(m['remaining'])} to {fmt(m2['remaining'])}. Changes tried: income {di}%, expenses {de}%, EMI {dm}%, extra repayment {fmt(ex)}, new loan {fmt(la)}.")
    st.write("")
    with st.container(border=True):
        ui.section("Outstanding balance over time", "Estimated, assuming constant payments", "target")
        plot(charts.balances({"Current": sim0["balances"], "Simulated": sim1["balances"]}))
    with st.expander("Save this scenario to my finances (optional)"):
        st.caption("This replaces your saved income, expenses and loans with the simulated values. It cannot be undone.")
        if st.checkbox("Yes, apply this scenario to my saved finances", key="wi_confirm") and st.button("Save scenario", key="wi_save"):
            try:
                repo.save_profile(ctx["user"]["id"], q)
                m3 = compute(repo.get_profile(ctx["user"]["id"]))
                if m3: repo.add_record(ctx["user"]["id"], m3)
                st.success("Scenario saved. Your dashboard now reflects it.")
            except ValidationError as err: st.error(str(err))
            except Exception: st.error("Something went wrong while saving. Please try again.")
    ui.disclaimer()
