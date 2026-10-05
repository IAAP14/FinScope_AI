"""FEATURE 2: Debt Risk Analyzer - 'Is my existing debt becoming risky?'"""
import streamlit as st
from components import ui, charts
from components.compat import plot, STRETCH
from components.navigation import back_to_home
from utils.finance import ratio_status, RISK_TEXT, warnings
from utils.format import fmt, pct

def _why(m):
    parts = [f"EMIs take {pct(m['emi_r'])} of your income", f"your total debt is about {m['dti']:.1f} years of income",
             f"{fmt(max(m['remaining'], 0))} is left each month after spending"]
    return "This rating considers that " + ", ".join(parts[:2]) + ", and that " + parts[2] + "."

def _technical(m):
    from ml import analysis
    from ml.predict import model_info
    with st.expander("How is this calculated? (technical details)"):
        info = model_info()
        if m.get("risk_source") == "model" and info:
            st.markdown(f"The risk level comes from an **{info['algorithm']}** classifier trained on a **synthetic demo dataset** "
                        f"({info['train_rows'] + info['test_rows']:,} sample rows, not real bank customers). "
                        f"Held-out accuracy on the demo data: **{info['accuracy']:.0%}**. It looks at five numbers: EMI share of income, "
                        "debt compared with yearly income, money left over, expense share and number of loans.")
        else:
            st.markdown("The saved machine-learning model could not be loaded, so a transparent rule-based score is being used instead "
                        "(EMI share 50%, debt vs income 30%, money left 20%).")
        table, r2 = analysis.regression_summary()
        if table is not None:
            st.markdown(f"**Statistical view (Statsmodels regression on the sample data, R² = {r2:.2f})** - which factors move risk pressure most:")
            st.dataframe(table, hide_index=True, **STRETCH)
        fig = analysis.correlation_figure()
        if fig is not None:
            st.markdown("**How the factors relate to each other (Seaborn heatmap, sample data):**")
            st.pyplot(fig, clear_figure=True)

def render(ctx):
    m = ctx["m"]
    back_to_home()
    ui.header("Debt Risk Analyzer", "Is my existing debt becoming risky? See how your debt compares with your income.")
    if not m: return ui.empty("dr", ctx)
    ui.verdict(m["status"], f"{m['level']} DEBT RISK", f"{RISK_TEXT[m['level']]} {_why(m)}", "DEBT RISK")
    ui.note("debt risk analysis", f"Debt risk is {m['level']}. {_why(m)}")
    a, b = st.columns(2)
    with a, st.container(border=True):
        ui.section("Risk indicators", "Each measure against common guidelines", "pulse")
        ui.meter("EMI burden (comfortable under 30%)", pct(m["emi_r"]), m["emi_r"] / .6, ratio_status(m["emi_r"], .3, .45))
        ui.meter("Debt vs yearly income (under 1.5x)", f"{m['dti']:.1f}x", m["dti"] / 4, ratio_status(m["dti"], 1.5, 3))
        ui.meter("Disposable income (above 30%)", pct(max(m["disp_r"], 0)), max(m["disp_r"], 0),
                 "ok" if m["disp_r"] >= .3 else "warn" if m["disp_r"] >= .15 else "bad")
        ui.meter("Pressure from additional borrowing", m["pressure"], {"Low": .25, "Moderate": .6, "High": .95}[m["pressure"]], m["pressure_status"])
        st.caption("Guidelines are general rules of thumb; lenders and situations differ.")
        ui.mini_grid([("Monthly income", fmt(m["inc"])), ("Monthly EMI", fmt(m["emi"])), ("Outstanding debt", fmt(m["debt"])),
                      ("Active loans", m["n"]), ("Disposable income", fmt(m["avail"]))])
    with b, st.container(border=True):
        ui.section("Debt pressure", "Higher means more strain on income", "shield")
        plot(charts.gauge(m["score"], m["status"], 230))
        ui.section("Points to review", "Based on the information entered", "alert")
        ws = warnings(m)
        if not ws: ui.insight("ok", "No major points to review", "Your figures do not trigger the warning signs we check.", "check")
        for w in ws: ui.insight(w["status"], w["title"], w["text"], "alert")
    if m["loans"]:
        with st.container(border=True):
            ui.section("Debt by loan", "Outstanding balances", "landmark")
            plot(charts.debt_split(m["loans"]))
    _technical(m)
    ui.disclaimer()
