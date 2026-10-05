import re

class ValidationError(ValueError):
    pass

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,30}$")

def validate_username(u):
    u = (u or "").strip()
    if not USERNAME_RE.match(u):
        raise ValidationError("Username must be 3-30 characters: letters, numbers, dot, dash or underscore.")
    return u

def validate_password(p):
    p = p or ""
    if len(p) < 8 or len(p) > 128:
        raise ValidationError("Password must be 8-128 characters.")
    if not (re.search(r"[A-Za-z]", p) and re.search(r"\d", p)):
        raise ValidationError("Password must include at least one letter and one number.")
    return p

def clean_display_name(n):
    n = re.sub(r"[^\w .'-]", "", (n or "").strip(), flags=re.UNICODE)[:60]
    return n

def clean_amount(value, label, maximum=1e10, allow_none=False):
    if value is None or (isinstance(value, float) and value != value):
        if allow_none: return None
        return 0.0
    try: v = float(value)
    except (TypeError, ValueError): raise ValidationError(f"{label} must be a number.")
    if v != v or v in (float("inf"), float("-inf")): raise ValidationError(f"{label} must be a valid number.")
    if v < 0: raise ValidationError(f"{label} cannot be negative.")
    if v > maximum: raise ValidationError(f"{label} is too large.")
    return v

def clean_text(value, label, max_len=60, required=False):
    t = re.sub(r"[\x00-\x1f]", "", str(value or "")).strip()[:max_len]
    if required and not t: raise ValidationError(f"{label} is required.")
    return t
