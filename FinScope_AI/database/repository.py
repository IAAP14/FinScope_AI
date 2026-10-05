"""All SQL lives here. Every query is parameterized and scoped to a user_id."""
from datetime import datetime, timezone
from database.db import connect
from utils.validation import clean_amount, clean_text, ValidationError

ESS = ["household", "food", "education", "transport", "utilities", "essential_other"]
NON = ["shopping", "entertainment", "non_essential_other"]

def _now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")

# ---- users
def create_user(username, password_hash, display_name="", db=None):
    with connect(db) as c:
        cur = c.execute("INSERT INTO users (username, display_name, password_hash, created_at) VALUES (?,?,?,?)",
                        (username, display_name, password_hash, _now()))
        return cur.lastrowid

def get_user_by_username(username, db=None):
    with connect(db) as c:
        return c.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

def get_user(user_id, db=None):
    with connect(db) as c:
        return c.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

def set_login_failure(user_id, attempts, locked_until, db=None):
    with connect(db) as c:
        c.execute("UPDATE users SET failed_attempts = ?, locked_until = ? WHERE id = ?", (attempts, locked_until, user_id))

def update_password(user_id, password_hash, db=None):
    with connect(db) as c:
        c.execute("UPDATE users SET password_hash = ?, failed_attempts = 0, locked_until = NULL WHERE id = ?", (password_hash, user_id))

def delete_user(user_id, db=None):
    with connect(db) as c:
        c.execute("DELETE FROM users WHERE id = ?", (user_id,))

# ---- profile
def empty_profile():
    return {"monthly_income": 0.0, "other_income": 0.0, "essential": {k: 0.0 for k in ESS},
            "non_essential": {k: 0.0 for k in NON}, "loans": [], "commitments": []}

def get_profile(user_id, db=None):
    p = empty_profile()
    with connect(db) as c:
        r = c.execute("SELECT * FROM financial_profiles WHERE user_id = ?", (user_id,)).fetchone()
        if r:
            p["monthly_income"], p["other_income"] = r["monthly_income"], r["other_income"]
            p["essential"] = {k: r[k] for k in ESS}
            p["non_essential"] = {k: r[k] for k in NON}
        p["loans"] = [dict(x) for x in c.execute(
            "SELECT id, name, original_amount, outstanding, interest_rate AS rate, emi, remaining_months "
            "FROM loans WHERE user_id = ? ORDER BY id", (user_id,))]
        p["commitments"] = [dict(x) for x in c.execute(
            "SELECT id, name, monthly_amount FROM commitments WHERE user_id = ? ORDER BY id", (user_id,))]
    return p

def save_profile(user_id, p, db=None):
    """Validate and replace the user's profile, loans and commitments atomically."""
    vals = {"monthly_income": clean_amount(p.get("monthly_income"), "Monthly income"),
            "other_income": clean_amount(p.get("other_income"), "Other income")}
    for k in ESS: vals[k] = clean_amount(p["essential"].get(k), k.replace("_", " ").title())
    for k in NON: vals[k] = clean_amount(p["non_essential"].get(k), k.replace("_", " ").title())
    loans = []
    for l in p.get("loans", []):
        name = clean_text(l.get("name"), "Loan name", 60)
        if not name and not l.get("outstanding") and not l.get("emi"): continue
        if not name: raise ValidationError("Every loan needs a name.")
        rate = clean_amount(l.get("rate"), "Interest rate", 100)
        rm = clean_amount(l.get("remaining_months"), "Remaining duration", 1200, allow_none=True)
        loans.append((name, clean_amount(l.get("original_amount"), "Original amount"),
                      clean_amount(l.get("outstanding"), "Outstanding balance"), rate,
                      clean_amount(l.get("emi"), "EMI"), None if rm is None else int(rm)))
    commits = []
    for x in p.get("commitments", []):
        name = clean_text(x.get("name"), "Commitment name", 60)
        amt = clean_amount(x.get("monthly_amount"), "Commitment amount")
        if not name and not amt: continue
        if not name: raise ValidationError("Every commitment needs a name.")
        commits.append((name, amt))
    cols = ["monthly_income", "other_income"] + ESS + NON
    with connect(db) as c:
        c.execute(f"INSERT INTO financial_profiles (user_id, {', '.join(cols)}, updated_at) VALUES (?, {', '.join('?'*len(cols))}, ?) "
                  f"ON CONFLICT(user_id) DO UPDATE SET {', '.join(f'{k}=excluded.{k}' for k in cols)}, updated_at=excluded.updated_at",
                  (user_id, *[vals[k] for k in cols], _now()))
        c.execute("DELETE FROM loans WHERE user_id = ?", (user_id,))
        c.executemany("INSERT INTO loans (user_id, name, original_amount, outstanding, interest_rate, emi, remaining_months) "
                      "VALUES (?,?,?,?,?,?,?)", [(user_id, *l) for l in loans])
        c.execute("DELETE FROM commitments WHERE user_id = ?", (user_id,))
        c.executemany("INSERT INTO commitments (user_id, name, monthly_amount) VALUES (?,?,?)", [(user_id, *x) for x in commits])

def delete_financial_data(user_id, db=None):
    with connect(db) as c:
        for t in ("loans", "commitments", "financial_records", "financial_profiles"):
            c.execute(f"DELETE FROM {t} WHERE user_id = ?", (user_id,))

# ---- records (history snapshots)
def add_record(user_id, m, db=None):
    with connect(db) as c:
        c.execute("INSERT INTO financial_records (user_id, recorded_at, income, expenses, emi, total_debt, available_income, risk_level) "
                  "VALUES (?,?,?,?,?,?,?,?)", (user_id, _now(), m["inc"], m["ess"] + m["non"], m["emi"], m["debt"], m["avail"], m["level"]))

def list_records(user_id, limit=24, db=None):
    with connect(db) as c:
        return [dict(r) for r in c.execute("SELECT * FROM financial_records WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit))]
