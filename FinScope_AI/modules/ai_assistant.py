"""FEATURE 5: AI Financial Explanation - plain-language answers about the user's own calculated figures."""
import streamlit as st
from components import ui
from components.compat import STRETCH
from components.navigation import back_to_home
from utils import ai_client

SUGGESTED = ["Why is my debt risk at this level?", "Why is my loan unaffordable?", "What is my debt-to-income ratio?",
             "What happens if I take another loan?", "What happens if my income decreases?",
             "How can additional repayment affect my debt?", "Why did my financial health status change?"]

def _answer(q, m):
    hist = st.session_state.setdefault("chat", [])
    notes = st.session_state.get("ctx_notes")
    with st.spinner("Thinking..."):
        text, err, engine = ai_client.ask(q, m, hist, notes)
    if text:
        reply = text
    else:
        why = ("*Showing a calculated explanation. Add GOOGLE_API_KEY to your .env file to turn on AI answers.*"
               if ai_client.status()[0] == "none" else "*AI explanation is temporarily unavailable. Your financial analysis is still available.*")
        reply = f"{ai_client.fallback_answer(q, m, notes)}\n\n{why}"
    hist.append(("user", q)); hist.append(("assistant", reply))

def render(ctx):
    m = ctx["m"]
    back_to_home()
    ui.header("AI Financial Explanation", "Ask about your numbers and get a plain-language explanation based on your own calculated results.")
    if not m: return ui.empty("ai", ctx)
    pending = st.session_state.pop("pending_q", None)
    if pending: _answer(pending, m)
    a, b = st.columns([2, 1])
    with b, st.container(border=True):
        ui.section("Suggested questions", "Tap to ask", "bulb")
        for i, q in enumerate(SUGGESTED):
            if st.button(q, key=f"sq{i}", **STRETCH):
                _answer(q, m); st.rerun()
        kind, label = ai_client.status()
        st.markdown(ui.badge("ok" if kind != "none" else "warn", label), unsafe_allow_html=True)
        st.caption("Only calculated figures are sent to the AI. Never your password or bank details.")
        with st.expander("What the AI can see"):
            st.write(ai_client.build_context(m, st.session_state.get("ctx_notes")))
        if st.session_state.get("chat") and st.button("Clear conversation", key="clr"):
            st.session_state["chat"] = []; st.rerun()
    with a, st.container(border=True):
        ui.section("Conversation", "Explanations are educational, not financial advice", "chat")
        hist = st.session_state.get("chat", [])
        if not hist: ui.insight("brn", "Ask anything about your numbers", "For example: why is my debt risk moderate, or what happens if my income decreases?", "chat")
        for role, text in hist:
            with st.chat_message(role): st.markdown(text)
    q = st.chat_input("Ask about your finances")
    if q: _answer(q, m); st.rerun()
    ui.disclaimer()
