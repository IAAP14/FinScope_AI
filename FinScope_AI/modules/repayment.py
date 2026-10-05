"""FEATURE 4: Debt Repayment Analyzer - 'How does my existing debt repayment look?'"""
import pandas as pd
import streamlit as st
from components import ui, charts
from components.compat import plot, STRETCH
from components.navigation import back_to_home
from utils.finance import simulate_repayment
from utils.format import fmt, fmt_months

def _overview(m, records):
    ui.section("Repayment overview", "Timelines are estimates under your current payments, not guarantees", "target")
    c = st.columns(4)
    with c[0]: ui.stat("Outstanding debt", fmt(m["debt"]))
    with c[1]: ui.stat("Current EMI", fmt(m["emi"]) + " / month")
    with c[2]: ui.stat("Estimated period", fmt_months(m["months"]))
    with c[3]: ui.stat("Estimated interest", fmt(m["total_interest"]))
    if m["has_repaid"] and m["original"] > 0:
        ui.meter("Repaid so far", f"{m['repaid'] / m['original']:.0%} of original loan amounts ({fmt(m['repaid'])})", m["repaid"] / m["original"], "ok")
    else:
        st.caption("Add the original loan amounts in My Finances to see how much you have already repaid.")
    if records and len(records) >= 2:
        r = list(reversed(records))
        st.caption("Total debt each time you saved your finances (monthly repayment progress)")
        plot(charts.progress_line([x["recorded_at"][:10] for x in r], [x["total_debt"] for x in r]))

def render(ctx):
    m = ctx["m"]
    back_to_home()
    ui.header("Debt Repayment Analyzer", "How does my existing debt repayment look? Compare normal repayment with paying a little extra.")
    if not m: return ui.empty("rp", ctx)
    if m["debt"] <= 0: return st.success("No outstanding debt is recorded. Nothing to repay right now.")
    with st.container(border=True): _overview(m, ctx.get("records"))
    st.write("")
    a, b = st.columns([1, 1.6])
    with a, st.container(border=True):
        ui.section("Additional monthly payment", "Applied to the highest-rate loan first", "coins")
        cap = int(max(m["inc"] * .3, 5000))
        default = min(2000, cap)
        ex = st.slider("Additional repayment per month", 0, cap, default, step=500)
        if m["remaining"] < ex: st.warning("This is more than the income left after your current spending.")
        st.caption("Estimates assume constant payments and fixed interest rates.")
    s0, s1 = simulate_repayment(m["loans"]), simulate_repayment(m["loans"], ex)
    with b, st.container(border=True):
        ui.section("Normal vs additional repayment", "Estimated, not guaranteed", "target")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="ba-title">NORMAL REPAYMENT</div>', unsafe_allow_html=True)
            ui.mini_grid([("Estimated period", fmt_months(s0["months"])), ("Total repayment", fmt(s0["total_paid"])), ("Interest paid", fmt(s0["total_interest"]))])
        with c2:
            st.markdown(f'<div class="ba-title">WITH {fmt(ex)} EXTRA EACH MONTH</div>', unsafe_allow_html=True)
            ui.mini_grid([("Estimated period", fmt_months(s1["months"])), ("Total repayment", fmt(s1["total_paid"])), ("Interest paid", fmt(s1["total_interest"]))])
        if s0["months"] and s1["months"] and ex > 0:
            ui.insight("ok", "Estimated effect of extra payments",
                       f"Current estimated repayment: {s0['months']} months. With {fmt(ex)} additional monthly payment: {s1['months']} months "
                       f"(about {fmt_months(s0['months'] - s1['months'])} sooner and roughly {fmt(max(s0['total_interest'] - s1['total_interest'], 0))} less interest), under these assumptions.", "target")
        if all(l["rate"] == 0 for l in m["loans"]): st.caption("Interest rates are 0 or missing, so the interest impact is not shown. Add rates in My Finances.")
    ui.note("repayment analysis", f"Current estimated repayment {fmt_months(s0['months'])}; with {fmt(ex)} extra per month {fmt_months(s1['months'])}; "
            f"interest {fmt(s0['total_interest'])} vs {fmt(s1['total_interest'])}.")
    st.write("")
    with st.container(border=True):
        ui.section("Outstanding balance over time", "Estimated", "chart")
        plot(charts.balances({"Normal": s0["balances"], "With extra": s1["balances"]}))
    with st.container(border=True):
        ui.section("Your loans", "", "landmark")
        df = pd.DataFrame(m["loans"])[["name", "outstanding", "rate", "emi", "remaining_months"]]
        df.columns = ["Loan", "Outstanding", "Rate %", "EMI", "Remaining months"]
        st.dataframe(df, hide_index=True, **STRETCH)
    ui.disclaimer()
