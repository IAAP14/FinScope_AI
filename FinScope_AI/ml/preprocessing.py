"""Data + feature preparation for the debt-risk model (scikit-learn).

The model sees five simple, explainable numbers. They are computed the same way
for training rows (sample CSV) and for a real user (utils.finance.compute).
"""
import numpy as np
import pandas as pd
from utils import config

CLASSES = ["LOW", "MODERATE", "HIGH"]          # label 0, 1, 2
FEATURES = ["emi_ratio", "debt_to_income", "disposable_ratio", "expense_ratio", "num_loans"]
RAW_COLUMNS = ["monthly_income", "monthly_expenses", "monthly_emi", "total_debt", "num_loans"]

def make_features(income, expenses, emi, debt, num_loans):
    """Return the model features from raw monthly figures. Safe against zero income."""
    income = max(float(income), 1.0)
    return {
        "emi_ratio": float(emi) / income,                        # share of income going to EMIs
        "debt_to_income": float(debt) / (income * 12),           # total debt in years of income
        "disposable_ratio": (income - float(expenses) - float(emi)) / income,  # what is left
        "expense_ratio": float(expenses) / income,
        "num_loans": int(num_loans),
    }

def frame_from_raw(df):
    """Turn raw sample rows into the model feature table."""
    rows = [make_features(r.monthly_income, r.monthly_expenses, r.monthly_emi, r.total_debt, r.num_loans)
            for r in df.itertuples(index=False)]
    return pd.DataFrame(rows, columns=FEATURES)

def risk_score(emi_ratio, dti, disposable_ratio):
    """Transparent rule used to LABEL the demo data (also the app's no-model fallback)."""
    return (0.5 * np.minimum(np.asarray(emi_ratio) / 0.5, 1)
            + 0.3 * np.minimum(np.asarray(dti) / 3, 1)
            + 0.2 * (1 - np.clip(np.asarray(disposable_ratio) / 0.3, 0, 1)))

def label_from_score(score):
    s = np.asarray(score)
    return np.where(s < 0.35, 0, np.where(s < 0.60, 1, 2))

def load_dataset(path=None):
    df = pd.read_csv(path or config.DATA_PATH)
    missing = [c for c in RAW_COLUMNS + ["debt_risk"] if c not in df.columns]
    if missing: raise ValueError(f"Sample data is missing columns: {missing}")
    X = frame_from_raw(df)
    y = df["debt_risk"].map({c: i for i, c in enumerate(CLASSES)}).astype(int)
    return df, X, y
