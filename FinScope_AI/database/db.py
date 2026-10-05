import sqlite3
from contextlib import contextmanager
from pathlib import Path
from utils import config

SCHEMA = Path(__file__).with_name("schema.sql")

def _path(db_path=None):
    p = Path(db_path) if db_path else config.DB_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

@contextmanager
def connect(db_path=None):
    conn = sqlite3.connect(_path(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db(db_path=None):
    with connect(db_path) as c:
        c.executescript(SCHEMA.read_text(encoding="utf-8"))
