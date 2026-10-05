import streamlit as st
from components import ui
from components.navigation import back_to_home

def render(ctx):
    back_to_home()
    ui.header("Privacy", "How FinScope AI handles your information.")
    with st.container(border=True):
        ui.section("What we store", "", "shield")
        st.markdown("- A username and a **bcrypt-hashed** password (never the password itself).\n"
                    "- The income, expense, loan and commitment amounts you enter.\n"
                    "- Snapshots of your totals each time you save, used for progress charts.")
        ui.section("What we never ask for", "", "alert")
        st.markdown("Banking passwords, card numbers, PINs, OTPs or any bank login. Please do not enter them anywhere.")
        ui.section("AI and your data", "", "bulb")
        st.markdown("AI explanations use Google GenAI (through LangChain). Only calculated figures, such as ratios and totals, are sent to the model "
                    "- never your username, password or bank details. Your records stay in the SQLite database on this computer. "
                    "If you enable the optional local Ollama fallback, nothing leaves your computer.")
        ui.section("Your controls", "", "wallet")
        st.markdown("You can change your password, delete your financial data or delete your account in **Profile & Settings**.")
    ui.disclaimer()
