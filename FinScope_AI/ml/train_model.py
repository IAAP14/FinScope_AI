"""Train the debt-risk classifier and save it with Joblib.

Run:  python -m ml.train_model

Pipeline = scikit-learn StandardScaler -> XGBoost classifier (3 classes: LOW / MODERATE / HIGH).
Trained ONLY on the synthetic demo dataset in data/sample_financial_data.csv.
"""
import json
import joblib
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from ml.preprocessing import load_dataset, FEATURES, CLASSES
from utils import config

def default_estimator():
    from xgboost import XGBClassifier
    return XGBClassifier(objective="multi:softprob", n_estimators=150, max_depth=4, learning_rate=0.1,
                         subsample=0.9, colsample_bytree=0.9, eval_metric="mlogloss", random_state=42)

def train(estimator=None, save=True, data_path=None, model_path=None):
    """Train, evaluate on a held-out 20% split and (optionally) save. Returns the bundle dict."""
    _, X, y = load_dataset(data_path)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    pipe = Pipeline([("scale", StandardScaler()), ("clf", estimator if estimator is not None else default_estimator())])
    pipe.fit(X_tr, y_tr)
    pred = pipe.predict(X_te)
    metrics = {"accuracy": round(float(accuracy_score(y_te, pred)), 4),
               "report": classification_report(y_te, pred, target_names=CLASSES, output_dict=True, zero_division=0),
               "confusion_matrix": confusion_matrix(y_te, pred).tolist(),
               "train_rows": int(len(X_tr)), "test_rows": int(len(X_te)),
               "algorithm": type(pipe.named_steps["clf"]).__name__}
    bundle = {"pipeline": pipe, "features": FEATURES, "classes": CLASSES, "metrics": metrics,
              "note": "Trained on synthetic demo data, not real bank customers."}
    if save:
        path = model_path or config.MODEL_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(bundle, path)
        (path.parent / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return bundle

if __name__ == "__main__":
    b = train()
    print("Algorithm:", b["metrics"]["algorithm"], "| held-out accuracy:", b["metrics"]["accuracy"])
    print("Saved to", config.MODEL_PATH)
