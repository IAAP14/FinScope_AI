"""Pure financial calculations. No UI, no database. All outputs are estimates under stated assumptions."""
import copy
from utils.format import fmt, fmt_months

LEVELS = {"ok": "LOW", "warn": "MODERATE", "bad": "HIGH"}

def emi_for(principal, annual_rate, months):
    if principal <= 0 or months <= 0: return 0.0
    r = annual_rate / 1200
    if r == 0: return principal / months
    f = (1 + r) ** months
    return principal * r * f / (f - 1)

def simulate_repayment(loans, extra=0.0, cap=600):
    """Month-by-month payoff. Each loan accrues monthly interest and receives its EMI; any extra
    amount goes to the highest-rate loan first. Returns months=None if not cleared within `cap` months."""
    act = [dict(bal=float(l["outstanding"]), r=float(l.get("rate") or 0) / 1200, emi=float(l.get("emi") or 0))
           for l in loans if float(l.get("outstanding") or 0) > 0]
    if not act: return dict(months=0, total_paid=0.0, total_interest=0.0, balances=[0.0])
    series, paid, interest = [sum(a["bal"] for a in act)], 0.0, 0.0
    for month in range(1, cap + 1):
        for a in act:
            if a["bal"] > 0: i = a["bal"] * a["r"]; a["bal"] += i; interest += i
        for a in act:
            p = min(a["emi"], a["bal"]); a["bal"] -= p; paid += p
        pool = max(extra, 0.0)
        for a in sorted(act, key=lambda x: -x["r"]):
            if pool <= 0: break
            p = min(pool, a["bal"]); a["bal"] -= p; pool -= p; paid += p
        total = sum(a["bal"] for a in act)
        series.append(total if total > 0.005 else 0.0)
        if total <= 0.005: return dict(months=month, total_paid=paid, total_interest=interest, balances=series)
    return dict(months=None, total_paid=paid, total_interest=interest, balances=series)

def compute(p):
    """Turn a stored profile into the metrics every page uses. Returns None if no income is entered."""
    inc = float(p["monthly_income"]) + float(p["other_income"])
    if inc <= 0: return None
    ess = sum(p["essential"].values()); non = sum(p["non_essential"].values())
    loans = p["loans"]; commit = sum(c["monthly_amount"] for c in p["commitments"])
    emi = sum(l["emi"] for l in loans); debt = sum(l["outstanding"] for l in loans)
    orig = [l for l in loans if l["original_amount"] > 0 and l["original_amount"] >= l["outstanding"]]
    repaid = sum(l["original_amount"] - l["outstanding"] for l in orig)
    avail = inc - ess - emi - commit
    emi_r, dti, disp_r = emi / inc, debt / (inc * 12), avail / inc
    wr = sum(l["rate"] * l["outstanding"] for l in loans) / debt if debt else 0.0
    score = 0.5 * min(emi_r / 0.5, 1) + 0.3 * min(dti / 3, 1) + 0.2 * (1 - max(min(disp_r / 0.3, 1), 0))
    status = "ok" if score < .35 else "warn" if score < .6 else "bad"
    if avail - non < 0 and status == "ok": status = "warn"
    sim = simulate_repayment(loans)
    m = dict(inc=inc, ess=ess, non=non, commit=commit, emi=emi, debt=debt, repaid=repaid,
             original=sum(l["original_amount"] for l in orig), has_repaid=bool(orig), avail=avail, remaining=avail - non,
             emi_r=emi_r, dti=dti, disp_r=disp_r, wr=wr, n=len(loans), score=score, status=status, level=LEVELS[status],
             loans=loans, months=sim["months"], total_interest=sim["total_interest"], total_paid=sim["total_paid"],
             ess_items=p["essential"], non_items=p["non_essential"])
    m["rule_level"] = m["level"]
    _apply_ml_risk(m)
    m["pressure"], m["pressure_status"] = borrowing_pressure(m)
    m["health"], m["health_status"] = health_status(m)
    return m

STATUS_OF = {"LOW": "ok", "MODERATE": "warn", "HIGH": "bad"}

def _apply_ml_risk(m):
    """Use the saved XGBoost model for the risk level. If it is unavailable, keep the rule-based level."""
    m["risk_source"] = "rules"; m["proba"] = None
    try:
        from ml.predict import predict_risk
        r = predict_risk(m["inc"], m["ess"] + m["non"] + m["commit"], m["emi"], m["debt"], m["n"])
    except Exception:
        r = None
    if r:
        m.update(level=r["level"], status=STATUS_OF[r["level"]], score=r["score"], proba=r["proba"], risk_source="model")

def health_status(m):
    """Overall financial health: Healthy / Stable / Caution / At Risk (plain-language summary of the picture)."""
    if m["remaining"] < 0 or m["level"] == "HIGH": return "At Risk", "bad"
    if m["level"] == "MODERATE": return "Caution", "warn"
    if m["disp_r"] >= .30 and m["emi_r"] < .20: return "Healthy", "ok"
    return "Stable", "ok"

RISK_TEXT = {
    "LOW": "Debt appears manageable based on the information provided.",
    "MODERATE": "Debt is manageable, but additional borrowing may increase financial pressure.",
    "HIGH": "Current debt commitments may be placing significant pressure on your income."}

def affordability(m_before, m_after, new_emi):
    """Plain verdict for a proposed loan: ('Affordable'|'Caution'|'Not Affordable', status). Not a loan decision."""
    inc = m_after["inc"]
    if m_after["remaining"] < 0 or m_after["emi_r"] >= .50: return "Not Affordable", "bad"
    if m_after["emi_r"] >= .40 or m_after["level"] == "HIGH" or m_after["remaining"] < .10 * inc: return "Caution", "warn"
    if m_after["emi_r"] >= .30 or m_after["level"] == "MODERATE": return "Caution", "warn"
    return "Affordable", "ok"

def affordability_text(verdict, m_before, m_after, new_emi):
    from utils.format import fmt
    base = (f"Your new EMI would be about {fmt(new_emi)} a month, taking your total EMIs from {m_before['emi_r']:.0%} "
            f"to {m_after['emi_r']:.0%} of income. ")
    tail = {"Affordable": "Based on the information entered, this loan appears manageable. Lenders decide approvals independently.",
            "Caution": "Based on your current income, expenses and existing EMI commitments, this loan may tighten your monthly budget. Consider a smaller amount or a longer tenure.",
            "Not Affordable": "Based on your current income, expenses and existing EMI commitments, this loan may place significant pressure on your monthly finances."}[verdict]
    return base + tail

def borrowing_pressure(m):
    if m["emi_r"] >= .45 or m["remaining"] <= 0: return "High", "bad"
    if m["emi_r"] >= .30 or m["disp_r"] < .15: return "Moderate", "warn"
    return "Low", "ok"

def ratio_status(v, warn, bad): return "ok" if v < warn else "warn" if v < bad else "bad"

def scenario(p, income_pct=0, ess_pct=0, non_pct=0, emi_pct=0, new_loan=None, extra=0.0):
    """Return a modified copy of the profile for what-if analysis."""
    q = copy.deepcopy(p)
    q["monthly_income"] *= 1 + income_pct / 100; q["other_income"] *= 1 + income_pct / 100
    q["essential"] = {k: v * (1 + ess_pct / 100) for k, v in q["essential"].items()}
    q["non_essential"] = {k: v * (1 + non_pct / 100) for k, v in q["non_essential"].items()}
    for l in q["loans"]: l["emi"] *= 1 + emi_pct / 100
    if new_loan and new_loan["amount"] > 0:
        months = int(new_loan["years"] * 12)
        q["loans"].append(dict(name="Proposed loan", original_amount=new_loan["amount"], outstanding=new_loan["amount"],
                               rate=new_loan["rate"], emi=emi_for(new_loan["amount"], new_loan["rate"], months), remaining_months=months))
    if extra and extra > 0:
        q["commitments"] = list(q["commitments"]) + [dict(name="Additional repayment", monthly_amount=float(extra))]
    return q

def build_insights(m):
    """Rule-based, cautious guidance cards: [{kind, status, title, text, icon}]."""
    out = []
    out.append(dict(kind="INSIGHT", status=ratio_status(m["emi_r"], .3, .45),
        title="EMI share of income", icon="pulse",
        text=f"Based on the information entered, EMIs take {m['emi_r']:.0%} of monthly income. "
             + ("This is within a range many lenders consider manageable." if m["emi_r"] < .3 else
                "Reviewing discretionary expenses may increase your available repayment capacity.")))
    if m["debt"] > 0 and m["remaining"] > 0:
        extra = round(m["remaining"] * .5, -2) or m["remaining"] * .5
        base = simulate_repayment(m["loans"]); fast = simulate_repayment(m["loans"], extra)
        t = f"Estimated under the selected assumptions, paying about {fmt(extra)} extra each month (half of your remaining income) "
        t += (f"could shorten repayment from {fmt_months(base['months'])} to {fmt_months(fast['months'])}." if fast["months"] and base["months"]
              else "may improve how quickly the balance falls.")
        out.append(dict(kind="REPAYMENT GUIDANCE", status="ok", title="Possible extra repayment", icon="target", text=t))
    elif m["debt"] > 0:
        out.append(dict(kind="REPAYMENT GUIDANCE", status="warn", title="Little room for extra repayment", icon="target",
            text="After expenses and EMIs there is no surplus right now. Consider reviewing expenses before adding repayments."))
    items = {k: v for k, v in {**m["non_items"]}.items() if v > 0}
    if items:
        k, v = max(items.items(), key=lambda kv: kv[1])
        out.append(dict(kind="SPENDING REVIEW", status="brn", title=f"Consider reviewing {k.replace('_', ' ')}", icon="wallet",
            text=f"Your largest non-essential category is {k.replace('_', ' ')} at {fmt(v)} a month. A 15% reduction would free about {fmt(v * .15)}."))
    elif m["non"] == 0:
        out.append(dict(kind="SPENDING REVIEW", status="brn", title="No non-essential spending entered", icon="wallet",
            text="Add shopping and entertainment in My Finances for a more complete spending review."))
    if m["status"] != "ok" or m["remaining"] < 0:
        t = ("Spending, EMIs and commitments exceed income by " + fmt(-m["remaining"]) + " a month. " if m["remaining"] < 0 else "")
        out.append(dict(kind="DEBT RISK WARNING", status=m["status"] if m["status"] != "ok" else "warn", title=f"Debt risk is {m['level'].lower()}", icon="alert",
            text=t + f"Additional borrowing pressure appears {m['pressure'].lower()}. Taking on another loan may add strain on your monthly budget."))
    else:
        out.append(dict(kind="DEBT RISK WARNING", status="ok", title="No major risk signals", icon="check",
            text="Based on the information entered, your EMI burden and disposable income are in a comfortable range."))
    if m["non"] > 0:
        s = scenario({"monthly_income": m["inc"], "other_income": 0, "essential": m["ess_items"], "non_essential": m["non_items"],
                      "loans": m["loans"], "commitments": [{"monthly_amount": m["commit"]}]}, non_pct=-10)
        out.append(dict(kind="WHAT-IF INSIGHT", status="brn", title="If non-essential spending fell 10%", icon="sliders",
            text=f"This scenario suggests about {fmt(m['non'] * .1)} more each month toward savings or repayment. Try the What-If Simulator to explore other changes."))
    return out

def warnings(m):
    """Only genuinely relevant warnings: [{status, title, text}]. Empty list means nothing to flag."""
    out = []
    if m["remaining"] < 0:
        out.append(dict(status="bad", title="Monthly shortfall", text=f"Spending, EMIs and commitments exceed income by {fmt(-m['remaining'])} a month."))
    if m["emi_r"] >= .45:
        out.append(dict(status="bad", title="High EMI burden", text="More than 45% of your income goes to EMIs, which leaves little room for surprises."))
    elif m["emi_r"] >= .30:
        out.append(dict(status="warn", title="EMI burden is getting heavy", text="EMIs take over 30% of income, so another large loan may add pressure."))
    if m["remaining"] >= 0 and m["disp_r"] < .15:
        out.append(dict(status="warn", title="Little income left over", text="After essentials, EMIs and commitments, less than 15% of income remains."))
    if m["debt"] > 0 and m["wr"] >= 15:
        out.append(dict(status="warn", title="High average interest rate", text=f"Your loans average {m['wr']:.1f}% interest. Reviewing the costliest loan first may help."))
    if m["n"] >= 4:
        out.append(dict(status="warn", title="Many active loans", text=f"You have {m['n']} active loans. Several payments at once can be harder to manage."))
    if m["debt"] > 0 and m["months"] is None:
        out.append(dict(status="bad", title="Payments may not clear the debt", text="At the current EMIs and rates, the balance is not estimated to be cleared. Please check the loan details."))
    return out

def drivers(m):
    """The 3 main things shaping the financial-health picture, in plain words: [(status, title, text)]."""
    return [
        (ratio_status(m["emi_r"], .3, .45), "EMI share of income",
         f"Your EMIs take {m['emi_r']:.0%} of your monthly income ({fmt(m['emi'])} of {fmt(m['inc'])})."),
        (ratio_status(m["dti"], 1.5, 3), "Total debt compared with income",
         f"Your outstanding debt of {fmt(m['debt'])} equals about {m['dti']:.1f} years of income."),
        ("ok" if m["remaining"] >= .15 * m["inc"] else "warn" if m["remaining"] >= 0 else "bad", "Money left each month",
         f"After expenses, EMIs and commitments, about {fmt(m['remaining'])} is left over."),
    ]
