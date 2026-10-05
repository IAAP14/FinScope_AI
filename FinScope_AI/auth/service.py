"""Registration and login logic (no UI). Errors never reveal which part of a login was wrong."""
import sqlite3
from datetime import datetime, timedelta, timezone
from auth.security import hash_password, verify_password
from database import repository as repo
from utils import config
from utils.validation import validate_username, validate_password, clean_display_name, ValidationError

GENERIC_FAIL = "Incorrect username or password."
_DUMMY = None

def register(username, password, confirm, display_name="", db=None):
    username = validate_username(username)
    password = validate_password(password)
    if password != confirm: raise ValidationError("Passwords do not match.")
    try:
        return repo.create_user(username, hash_password(password), clean_display_name(display_name) or username, db=db)
    except sqlite3.IntegrityError:
        raise ValidationError("That username is already taken.")

def authenticate(username, password, db=None):
    """Return the user row on success; raise ValidationError otherwise."""
    global _DUMMY
    user = repo.get_user_by_username((username or "").strip(), db=db)
    if user is None:
        _DUMMY = _DUMMY or hash_password("dummy-password-1")
        verify_password(password or "", _DUMMY)  # keep timing similar
        raise ValidationError(GENERIC_FAIL)
    now = datetime.now(timezone.utc)
    if user["locked_until"] and datetime.fromisoformat(user["locked_until"]) > now:
        raise ValidationError("Too many attempts. Please try again in a few minutes.")
    if verify_password(password or "", user["password_hash"]):
        if user["failed_attempts"]: repo.set_login_failure(user["id"], 0, None, db=db)
        return user
    attempts = user["failed_attempts"] + 1
    locked = None
    if attempts >= config.MAX_FAILED_LOGINS:
        locked = (now + timedelta(minutes=config.LOCKOUT_MINUTES)).isoformat(timespec="seconds"); attempts = 0
    repo.set_login_failure(user["id"], attempts, locked, db=db)
    raise ValidationError(GENERIC_FAIL)

def change_password(user_id, current, new, confirm, db=None):
    user = repo.get_user(user_id, db=db)
    if not user or not verify_password(current or "", user["password_hash"]):
        raise ValidationError("Current password is incorrect.")
    new = validate_password(new)
    if new != confirm: raise ValidationError("New passwords do not match.")
    repo.update_password(user_id, hash_password(new), db=db)
