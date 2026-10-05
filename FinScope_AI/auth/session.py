import time
import streamlit as st
from utils import config

def login_user(user):
    st.session_state["user"] = {"id": int(user["id"]), "username": user["username"], "name": user["display_name"] or user["username"]}
    st.session_state["last_active"] = time.time()
    st.session_state["page"] = "Financial Health"

def logout():
    for k in list(st.session_state.keys()): del st.session_state[k]

def current_user():
    """Return the signed-in user, or None (also expires idle sessions)."""
    u = st.session_state.get("user")
    if not u: return None
    if time.time() - st.session_state.get("last_active", 0) > config.SESSION_TIMEOUT_MINUTES * 60:
        logout(); st.session_state["notice"] = "Your session expired. Please sign in again."
        return None
    st.session_state["last_active"] = time.time()
    return u
