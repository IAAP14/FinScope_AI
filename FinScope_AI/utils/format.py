from utils.config import CURRENCY

def _indian(n):
    """Group digits the Indian way: 3,20,000."""
    s = str(int(round(n)))
    if len(s) <= 3: return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2: parts.insert(0, head[-2:]); head = head[:-2]
    if head: parts.insert(0, head)
    return ",".join(parts + [tail])

def fmt(x):
    x = float(x or 0)
    return f"{CURRENCY}{_indian(x)}" if x >= 0 else f"-{CURRENCY}{_indian(abs(x))}"

def fmt_months(m):
    if m is None: return "Not reached at this payment"
    y, mo = divmod(int(m), 12)
    return " ".join(filter(None, [f"{y} yr" if y else "", f"{mo} mo" if mo else ""])) or "Under 1 month"

def pct(x): return f"{x:.0%}"
