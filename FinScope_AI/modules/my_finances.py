import pandas as pd
import streamlit as st
from components import ui
from components.compat import STRETCH
from components.navigation import back_to_home
from utils.data import demo_profile
from database import repository as repo
from utils.finance import compute
from utils.validation import ValidationError

LOAN_COLS = ["name", "original_amount", "outstanding", "rate", "emi", "remaining_months"]

def _num(label, key, val, step=500.0):
    return st.number_input(label, min_value=0.0, value=float(val or 0), step=step, key=key)

def _rows(df, cols):
    out = []
    for r in df.to_dict("records"):
        out.append({c: (None if pd.isna(r.get(c)) else r.get(c)) for c in cols})
    return out

def render(ctx):
    back_to_home()
    ui.header("My Finances", "Keep your income, expenses and loans up to date so every page reflects your real position.")
    p = ctx["profile"]
    with st.expander("Try with sample data"):
        st.caption("Fills in a realistic demo profile (clearly sample data). This replaces what you have saved.")
        if st.checkbox("Yes, replace my entries with sample data", key="demo_confirm") and st.button("Load sample data", key="demo_load"):
            repo.save_profile(ctx["user"]["id"], demo_profile()); st.session_state["notice_ok"] = "Sample data loaded."; st.rerun()
    with st.form("finances"):
        with st.container(border=True):
            ui.section("Income", "Monthly amounts", "wallet")
            c = st.columns(2)
            with c[0]: inc = _num("Monthly income", "inc", p["monthly_income"], 1000.0)
            with c[1]: oth = _num("Other income", "oth", p["other_income"], 500.0)
        with st.container(border=True):
            ui.section("Essential expenses", "Needs you have to cover each month", "card")
            e = p["essential"]; c = st.columns(3)
            ess = {}
            for i, (k, lbl) in enumerate([("household", "Household"), ("food", "Food"), ("education", "Education"),
                                          ("transport", "Transport"), ("utilities", "Utilities"), ("essential_other", "Other")]):
                with c[i % 3]: ess[k] = _num(lbl, f"e_{k}", e[k])
        with st.container(border=True):
            ui.section("Non-essential expenses", "Spending that could be reviewed", "sliders")
            n = p["non_essential"]; c = st.columns(3); non = {}
            for i, (k, lbl) in enumerate([("shopping", "Shopping"), ("entertainment", "Entertainment"), ("non_essential_other", "Other")]):
                with c[i]: non[k] = _num(lbl, f"n_{k}", n[k])
        with st.container(border=True):
            ui.section("Loans", "One row per loan. Add rows with the + at the bottom of the table.", "landmark")
            df = pd.DataFrame(p["loans"], columns=LOAN_COLS)
            loans_df = st.data_editor(df, num_rows="dynamic", **STRETCH, hide_index=True, key="loans_editor", column_config={
                "name": "Loan name", "original_amount": st.column_config.NumberColumn("Original amount", min_value=0),
                "outstanding": st.column_config.NumberColumn("Outstanding balance", min_value=0),
                "rate": st.column_config.NumberColumn("Interest rate (% p.a.)", min_value=0, max_value=100),
                "emi": st.column_config.NumberColumn("EMI", min_value=0),
                "remaining_months": st.column_config.NumberColumn("Remaining (months)", min_value=0, step=1)})
        with st.container(border=True):
            ui.section("Other commitments", "Fixed monthly payments such as insurance, rent-to-own or family support", "shield")
            cdf = pd.DataFrame(p["commitments"], columns=["name", "monthly_amount"])
            commits_df = st.data_editor(cdf, num_rows="dynamic", **STRETCH, hide_index=True, key="commit_editor",
                                        column_config={"name": "Commitment", "monthly_amount": st.column_config.NumberColumn("Monthly amount", min_value=0)})
        st.caption("Enter only amounts. Never enter banking passwords, card PINs or OTPs. Figures are estimates based on what you provide.")
        saved = st.form_submit_button("Save changes", type="primary")
    if saved:
        new = {"monthly_income": inc, "other_income": oth, "essential": ess, "non_essential": non,
               "loans": _rows(loans_df, LOAN_COLS), "commitments": _rows(commits_df, ["name", "monthly_amount"])}
        try:
            repo.save_profile(ctx["user"]["id"], new)
            m = compute(repo.get_profile(ctx["user"]["id"]))
            if m: repo.add_record(ctx["user"]["id"], m)
            st.success("Saved. Your dashboard now reflects these figures.")
        except ValidationError as err:
            st.error(str(err))
        except Exception:
            st.error("Something went wrong while saving. Please check the values and try again.")
