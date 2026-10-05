PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE COLLATE NOCASE,
  display_name TEXT NOT NULL DEFAULT '',
  password_hash TEXT NOT NULL,
  failed_attempts INTEGER NOT NULL DEFAULT 0,
  locked_until TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS financial_profiles (
  user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  monthly_income REAL NOT NULL DEFAULT 0 CHECK (monthly_income >= 0),
  other_income REAL NOT NULL DEFAULT 0 CHECK (other_income >= 0),
  household REAL NOT NULL DEFAULT 0 CHECK (household >= 0),
  food REAL NOT NULL DEFAULT 0 CHECK (food >= 0),
  education REAL NOT NULL DEFAULT 0 CHECK (education >= 0),
  transport REAL NOT NULL DEFAULT 0 CHECK (transport >= 0),
  utilities REAL NOT NULL DEFAULT 0 CHECK (utilities >= 0),
  essential_other REAL NOT NULL DEFAULT 0 CHECK (essential_other >= 0),
  shopping REAL NOT NULL DEFAULT 0 CHECK (shopping >= 0),
  entertainment REAL NOT NULL DEFAULT 0 CHECK (entertainment >= 0),
  non_essential_other REAL NOT NULL DEFAULT 0 CHECK (non_essential_other >= 0),
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS loans (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  original_amount REAL NOT NULL DEFAULT 0 CHECK (original_amount >= 0),
  outstanding REAL NOT NULL DEFAULT 0 CHECK (outstanding >= 0),
  interest_rate REAL NOT NULL DEFAULT 0 CHECK (interest_rate >= 0 AND interest_rate <= 100),
  emi REAL NOT NULL DEFAULT 0 CHECK (emi >= 0),
  remaining_months INTEGER CHECK (remaining_months IS NULL OR remaining_months >= 0)
);
CREATE INDEX IF NOT EXISTS idx_loans_user ON loans(user_id);
CREATE TABLE IF NOT EXISTS commitments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  monthly_amount REAL NOT NULL DEFAULT 0 CHECK (monthly_amount >= 0)
);
CREATE INDEX IF NOT EXISTS idx_commit_user ON commitments(user_id);
CREATE TABLE IF NOT EXISTS financial_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  recorded_at TEXT NOT NULL,
  income REAL NOT NULL, expenses REAL NOT NULL, emi REAL NOT NULL,
  total_debt REAL NOT NULL, available_income REAL NOT NULL, risk_level TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rec_user ON financial_records(user_id);
