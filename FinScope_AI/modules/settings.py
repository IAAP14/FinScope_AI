import streamlit as st
from auth import service, session
from components import ui
from components.navigation import back_to_home
from database import repository as repo
from utils.validation import ValidationError

def render(ctx):
    u = ctx["user"]
    back_to_home()
    ui.header("Profile & Settings", "Manage your account and your stored data.")
    a, b = st.columns(2)
    with a, st.container(border=True):
        ui.section("Account", "", "wallet"); ui.stat("Username", u["username"]); ui.stat("Display name", u["name"])
        st.markdown("**Change password**")
        with st.form("pw"):
            cur = st.text_input("Current password", type="password"); new = st.text_input("New password", type="password")
            conf = st.text_input("Confirm new password", type="password")
            if st.form_submit_button("Update password", type="primary"):
                try: service.change_password(u["id"], cur, new, conf); st.success("Password updated.")
                except ValidationError as e: st.error(str(e))
    with b, st.container(border=True):
        ui.section("Your data", "You stay in control", "shield")
        st.caption("Delete your financial information but keep your account, or remove the account entirely.")
        if st.checkbox("I understand this cannot be undone"):
            if st.button("Delete my financial data"): repo.delete_financial_data(u["id"]); st.success("Financial data deleted.")
            if st.button("Delete my account"): repo.delete_user(u["id"]); session.logout(); st.rerun()
