from pathlib import Path
import streamlit as st
from components.compat import STRETCH

ICONS = {
 "wallet": '<path d="M19 7V5a2 2 0 0 0-2-2H5a2 2 0 0 0 0 4h14a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5"/><path d="M16 13h.01"/>',
 "landmark": '<path d="M3 22h18M6 18v-7M10 18v-7M14 18v-7M18 18v-7M12 2 3 7h18z"/>',
 "card": '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/>',
 "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
 "alert": '<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0zM12 9v4M12 17h.01"/>',
 "bulb": '<path d="M9 18h6M10 22h4M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.2 1 2V17h6v-.3c0-.8.4-1.5 1-2A7 7 0 0 0 12 2z"/>',
 "chart": '<path d="M3 3v18h18M7 15v3M12 9v9M17 5v13"/>',
 "calc": '<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M8 6h8M8 10h.01M12 10h.01M16 10h.01M8 14h.01M12 14h.01M16 14h.01M8 18h8"/>',
 "sliders": '<path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6"/>',
 "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/>',
 "chat": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
 "pulse": '<path d="M3 12h4l3-8 4 16 3-8h4"/>',
 "check": '<path d="M20 6 9 17l-5-5"/>',
 "home": '<path d="M3 11 12 3l9 8M5 10v10h5v-6h4v6h5V10"/>',
 "send": '<path d="m22 2-7 20-4-9-9-4zM22 2 11 13"/>',
 "coins": '<circle cx="8" cy="8" r="6"/><path d="M18.1 10.4a6 6 0 1 1-7.7 7.7M7 6h1v4"/>',
}

def icon(name, size=18):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>')

def load_css():
    css = (Path(__file__).resolve().parent.parent / "styles" / "style.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

def header(title, subtitle):
    st.markdown(f'<div class="fs-head"><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)

def section(title, sub="", ic="chart"):
    st.markdown(f'<div class="fs-sec"><span class="ic">{icon(ic,16)}</span><h3>{title}</h3></div><div class="fs-sub">{sub}</div>', unsafe_allow_html=True)

def kpi(title, value, desc, ic):
    st.markdown(f'<div class="kpi"><div class="top"><span>{title}</span><span class="ic">{icon(ic,18)}</span></div>'
                f'<div class="v">{value}</div><div class="d">{desc}</div></div>', unsafe_allow_html=True)

def status_kpi(title, value, desc, status, ic):
    """KPI card whose headline value is coloured by status (ok / warn / bad)."""
    st.markdown(f'<div class="kpi"><div class="top"><span>{title}</span><span class="ic">{icon(ic,18)}</span></div>'
                f'<div class="v {status}-t">{value}</div><div class="d">{desc}</div></div>', unsafe_allow_html=True)

def meter(label, value_text, pct, status="brn"):
    pct = max(0, min(pct, 1)) * 100
    st.markdown(f'<div class="mrow"><div class="l"><span>{label}</span><span>{value_text}</span></div>'
                f'<div class="bar"><i class="{status}" style="width:{pct:.0f}%"></i></div></div>', unsafe_allow_html=True)

def badge(status, text): return f'<span class="badge {status}">{text}</span>'

def stat(label, value):
    st.markdown(f'<div class="stat"><span>{label}</span><b>{value}</b></div>', unsafe_allow_html=True)

def mini_grid(items):
    cells = "".join(f'<div class="mini"><span>{l}</span><b>{v}</b></div>' for l, v in items)
    st.markdown(f'<div class="mini-grid">{cells}</div>', unsafe_allow_html=True)

def insight(status, title, text, ic="bulb", kind=""):
    cls = status if status in ("ok", "warn", "bad") else "brn"
    k = f'<small>{kind}</small>' if kind else ""
    st.markdown(f'<div class="ins"><span class="ic {cls}">{icon(ic,16)}</span><div>{k}<b>{title}</b><p>{text}</p></div></div>', unsafe_allow_html=True)

def _load_demo(uid):
    from database import repository as repo
    from utils.data import demo_profile
    repo.save_profile(uid, demo_profile())
    st.session_state["notice_ok"] = "Sample data loaded. You can edit it any time in My Finances."

def empty(key, ctx=None):
    st.markdown('<div class="empty"><b>No financial data yet</b><br>Add your income, expenses and loans in My Finances, '
                'or try the app instantly with sample data.</div>', unsafe_allow_html=True)
    c = st.columns(2)
    with c[0]: st.button("Open My Finances", key=f"empty_{key}", type="primary", **STRETCH, on_click=lambda: st.session_state.update(page="My Finances"))
    if ctx:
        with c[1]: st.button("Load sample data", key=f"demo_{key}", **STRETCH, on_click=_load_demo, args=(ctx["user"]["id"],))

def disclaimer():
    st.caption("FinScope AI provides educational and decision-support insights based on the information provided. Results are estimates and should not be considered professional financial advice or guaranteed loan approval.")

def verdict(status, big, text, kicker=""):
    """Large plain-language result banner (status: ok / warn / bad)."""
    k = f'<div class="ba-title">{kicker}</div>' if kicker else ""
    st.markdown(f'<div class="verdict {status}"><div>{k}<div class="big">{big}</div><p>{text}</p></div></div>', unsafe_allow_html=True)

def note(key, text):
    """Remember the latest result of a page so the AI can explain it (context-aware answers)."""
    st.session_state.setdefault("ctx_notes", {})[key] = text
