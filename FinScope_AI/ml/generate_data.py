"""Create the DEMO dataset (synthetic, NOT real bank data).

Run:  python -m ml.generate_data
Labels come from a transparent rule (ml.preprocessing.risk_score) plus a little random noise,
so the data behaves realistically but is clearly artificial.
"""
import numpy as np
import pandas as pd
from ml.preprocessing import risk_score, label_from_score, CLASSES
from utils import config

def generate(n=1500, seed=42):
    rng = np.random.default_rng(seed)
    income = np.round(rng.lognormal(mean=10.7, sigma=0.45, size=n), -2).clip(15000, 250000)
    expense_ratio = rng.beta(5, 5, n) * 0.55 + 0.25             # 25%..80% of income
    expenses = np.round(income * expense_ratio, -1)
    num_loans = rng.choice([0, 1, 2, 3, 4, 5], size=n, p=[.06, .22, .28, .22, .14, .08])
    emi_ratio = np.where(num_loans == 0, 0.0, np.clip(rng.beta(2, 4, n) * 0.85 * (0.6 + num_loans * 0.16), 0, 0.75))
    emi = np.round(income * emi_ratio, -1)
    months_left = rng.integers(8, 100, n)
    debt = np.round(emi * months_left * rng.uniform(0.55, 0.9, n), -2)
    disposable = (income - expenses - emi) / income
    score = risk_score(emi / income, debt / (income * 12), disposable) + rng.normal(0, 0.05, n)
    labels = label_from_score(score)
    df = pd.DataFrame({"monthly_income": income.astype(int), "monthly_expenses": expenses.astype(int),
                       "monthly_emi": emi.astype(int), "total_debt": debt.astype(int),
                       "num_loans": num_loans, "debt_risk": [CLASSES[i] for i in labels]})
    return df

if __name__ == "__main__":
    config.DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    d = generate(); d.to_csv(config.DATA_PATH, index=False)
    print(f"Saved {len(d)} demo rows to {config.DATA_PATH}"); print(d["debt_risk"].value_counts())
