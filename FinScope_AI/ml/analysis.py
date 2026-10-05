"""Statistical analysis with Statsmodels / Seaborn / Matplotlib on the demo dataset.

Answers a simple question: which financial factors move debt-risk pressure the most?
"""
import pandas as pd
from ml.preprocessing import load_dataset, risk_score

LABELS = {"emi_ratio": "EMI share of income", "debt_to_income": "Debt (years of income)",
          "disposable_ratio": "Income left over", "expense_ratio": "Expense share of income",
          "num_loans": "Number of loans"}

def _table():
    raw, X, _ = load_dataset()
    X = X.copy()
    X["risk_pressure"] = risk_score(X["emi_ratio"], X["debt_to_income"], X["disposable_ratio"])
    X["monthly_income"] = raw["monthly_income"].values
    return X

def regression_summary():
    """OLS: risk pressure ~ EMI share + debt + leftover + number of loans. Returns (DataFrame, r_squared) or (None, None)."""
    try:
        import statsmodels.api as sm
        t = _table()
        cols = ["emi_ratio", "debt_to_income", "disposable_ratio", "num_loans"]
        fit = sm.OLS(t["risk_pressure"], sm.add_constant(t[cols])).fit()
        out = pd.DataFrame({"Factor": [LABELS[c] for c in cols], "Effect (coef.)": fit.params[cols].round(3).values,
                            "p-value": fit.pvalues[cols].round(4).values})
        return out, float(fit.rsquared)
    except Exception:
        return None, None

def correlation_figure():
    """Seaborn heatmap of how the factors relate to each other and to risk pressure."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import seaborn as sns
        t = _table()[list(LABELS) + ["risk_pressure"]].rename(columns={**LABELS, "risk_pressure": "Risk pressure"})
        fig, ax = plt.subplots(figsize=(6.2, 4.4))
        sns.heatmap(t.corr(), annot=True, fmt=".2f", cmap="Blues", cbar=False, linewidths=.5, ax=ax, annot_kws={"size": 8})
        ax.tick_params(labelsize=8); plt.xticks(rotation=35, ha="right"); fig.tight_layout()
        return fig
    except Exception:
        return None
