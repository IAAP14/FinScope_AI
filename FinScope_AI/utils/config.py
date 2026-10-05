"""Central configuration. All values come from environment variables / .env (never hard-code keys)."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

def _path(v):
    p = Path(v)
    return p if p.is_absolute() else ROOT / p

def _int(name, default):
    try: return int(os.getenv(name, default))
    except ValueError: return default

DB_PATH = _path(os.getenv("DATABASE_PATH", "database/finscope.db"))
DATA_PATH = ROOT / "data" / "sample_financial_data.csv"
MODEL_PATH = ROOT / "models" / "debt_risk_model.joblib"

# --- Primary AI: Google GenAI (key comes ONLY from the environment)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"
AI_TIMEOUT = _int("AI_TIMEOUT_SECONDS", 60)

# --- Optional local fallback (Ollama through LangChain Community). Off by default.
OLLAMA_ENABLED = os.getenv("OLLAMA_ENABLED", "false").strip().lower() in ("1", "true", "yes")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_TIMEOUT = _int("OLLAMA_TIMEOUT_SECONDS", 90)

SESSION_TIMEOUT_MINUTES = _int("SESSION_TIMEOUT_MINUTES", 30)
MAX_FAILED_LOGINS = _int("MAX_FAILED_LOGINS", 5)
LOCKOUT_MINUTES = _int("LOCKOUT_MINUTES", 10)
CURRENCY = os.getenv("CURRENCY_SYMBOL", "₹")
