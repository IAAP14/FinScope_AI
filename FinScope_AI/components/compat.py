"""Small helpers so the app runs on both older and newer Streamlit 1.x releases.

Newer Streamlit replaces `use_container_width=True` with `width="stretch"`; this picks the right one.
"""
import streamlit as st

def _version():
    try:
        return tuple(int(x) for x in st.__version__.split(".")[:2])
    except Exception:
        return (1, 40)

STRETCH = {"width": "stretch"} if _version() >= (1, 50) else {"use_container_width": True}

def plot(fig, key=None):
    """Show a Plotly figure full-width without the hover toolbar."""
    kw = dict(STRETCH); kw["config"] = {"displayModeBar": False}
    if key: kw["key"] = key
    st.plotly_chart(fig, **kw)
