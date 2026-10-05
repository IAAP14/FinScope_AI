"""Load the saved model and predict debt risk. Never raises: returns None if the model cannot be used,
so the app falls back to the rule-based score instead of crashing."""
import threading
import joblib
import pandas as pd
from ml.preprocessing import make_features, FEATURES, CLASSES
from utils import config

_lock = threading.Lock()
_bundle = None
_failed = False

def ensure_model():
    """Load the joblib model; train it once if the file is missing. Returns the bundle or None."""
    global _bundle, _failed
    with _lock:
        if _bundle is not None: return _bundle
        if _failed: return None
        try:
            if config.MODEL_PATH.exists():
                _bundle = joblib.load(config.MODEL_PATH)
            else:
                from ml.train_model import train
                try:
                    _bundle = train(save=True)
                except OSError:           # read-only folder: keep the model in memory only
                    _bundle = train(save=False)
        except Exception:
            _bundle = None; _failed = True
        return _bundle

def model_info():
    b = ensure_model()
    return b["metrics"] if b else None

def predict_risk(income, expenses, emi, debt, num_loans):
    """Return {'level': 'LOW'|'MODERATE'|'HIGH', 'proba': {...}, 'score': 0..1} or None."""
    b = ensure_model()
    if b is None: return None
    try:
        row = pd.DataFrame([make_features(income, expenses, emi, debt, num_loans)], columns=FEATURES)
        p = b["pipeline"].predict_proba(row)[0]
        proba = {c: float(x) for c, x in zip(CLASSES, p)}
        level = max(proba, key=proba.get)
        # one 0-1 "pressure" number for gauges: class probabilities weighted by band midpoints
        score = 0.17 * proba["LOW"] + 0.47 * proba["MODERATE"] + 0.80 * proba["HIGH"]
        return {"level": level, "proba": proba, "score": score}
    except Exception:
        return None
