"""Plotly chart builders. One consistent navy / soft-blue palette."""
import plotly.graph_objects as go
from utils.format import fmt

NAVY, BLUE, SOFT, GREEN, AMBER, RED = "#0B2545", "#3E7CB1", "#A9C6E8", "#2E7D5B", "#C98A1B", "#C0504D"
PALETTE = [NAVY, BLUE, SOFT, GREEN, AMBER]
STATUS = {"ok": GREEN, "warn": AMBER, "bad": RED}
GRID = "#E6ECF4"

def style(fig, h=320):
    fig.update_layout(height=h, margin=dict(l=10, r=10, t=20, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Inter, Segoe UI, sans-serif", color="#1B2B44", size=12), legend=dict(orientation="h", y=-0.2))
    fig.update_xaxes(gridcolor=GRID, zeroline=False); fig.update_yaxes(gridcolor=GRID, zeroline=False)
    return fig

def flow(m, h=320):
    labels = ["Income", "Essential", "Non-essential", "EMI & commitments", "Left over"]
    vals = [m["inc"], m["ess"], m["non"], m["emi"] + m["commit"], max(m["remaining"], 0)]
    fig = go.Figure(go.Bar(x=labels, y=vals, marker_color=[NAVY, BLUE, SOFT, AMBER, GREEN], text=[fmt(v) for v in vals],
                           textposition="outside", cliponaxis=False))
    return style(fig, h)

def allocation(m, h=320):
    labels = ["Essential", "Non-essential", "EMI & commitments", "Left over"]
    vals = [m["ess"], m["non"], m["emi"] + m["commit"], max(m["remaining"], 0)]
    fig = go.Figure(go.Pie(labels=labels, values=vals, hole=.62, marker=dict(colors=[BLUE, SOFT, AMBER, GREEN]),
                           textinfo="percent", sort=False))
    return style(fig, h).update_layout(showlegend=True)

def gauge(score, status, h=220):
    fig = go.Figure(go.Indicator(mode="gauge", value=score * 100, gauge=dict(
        axis=dict(range=[0, 100], tickcolor="#9DB0C9"), bar=dict(color=STATUS[status], thickness=.35), bgcolor="#EEF3F9", borderwidth=0,
        steps=[dict(range=[0, 35], color="#E3F1EA"), dict(range=[35, 60], color="#FAF0DA"), dict(range=[60, 100], color="#F6E1E0")])))
    fig.add_annotation(text=f"<b>{score*100:.0f}</b><br><span style='font-size:11px;color:#6B7C93'>pressure score</span>",
                       x=.5, y=.05, showarrow=False, font=dict(size=30, color=NAVY))
    return style(fig, h)

def before_after(rows, h=300):
    """rows: [(label, before, after)] in the same unit."""
    fig = go.Figure()
    fig.add_bar(name="Current", x=[r[0] for r in rows], y=[r[1] for r in rows], marker_color=SOFT)
    fig.add_bar(name="Simulated", x=[r[0] for r in rows], y=[r[2] for r in rows], marker_color=NAVY)
    return style(fig, h).update_layout(barmode="group")

def balances(series_by_name, h=300):
    fig = go.Figure()
    for (name, ys), c in zip(series_by_name.items(), [SOFT, NAVY, GREEN]):
        fig.add_scatter(y=ys, mode="lines", name=name, line=dict(color=c, width=3))
    fig.update_xaxes(title="Months"); fig.update_yaxes(title="Outstanding balance")
    return style(fig, h)

def debt_split(loans, h=280):
    fig = go.Figure(go.Pie(labels=[l["name"] for l in loans], values=[l["outstanding"] for l in loans], hole=.6,
                           marker=dict(colors=PALETTE + PALETTE)))
    return style(fig, h)

def progress_line(dates, debts, h=200):
    fig = go.Figure(go.Scatter(x=dates, y=debts, mode="lines+markers", line=dict(color=NAVY, width=3)))
    return style(fig, h)
