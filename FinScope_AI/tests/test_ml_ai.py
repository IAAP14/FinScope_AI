import os, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sklearn.ensemble import GradientBoostingClassifier
from ml import preprocessing, train_model, predict
from utils import finance, ai_client
from utils.data import demo_profile
from utils.format import fmt

def _estimator():
    """Use XGBoost when installed (the real model); otherwise a scikit-learn stand-in so tests still run."""
    try:
        return train_model.default_estimator()
    except ImportError:
        return GradientBoostingClassifier(random_state=1)

class MLTests(unittest.TestCase):
    def test_features_safe_for_zero_income(self):
        f = preprocessing.make_features(0, 100, 50, 1000, 1)
        self.assertTrue(all(v == v for v in f.values()))
    def test_dataset_loads_with_three_classes(self):
        _, X, y = preprocessing.load_dataset()
        self.assertEqual(list(X.columns), preprocessing.FEATURES); self.assertEqual(set(y), {0, 1, 2})
    def test_train_save_load_predict(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "m.joblib"
            b = train_model.train(estimator=_estimator(), save=True, model_path=path)
            self.assertTrue(path.exists()); self.assertGreater(b["metrics"]["accuracy"], 0.8)
            import joblib; loaded = joblib.load(path)
            row = preprocessing.make_features(50000, 26000, 18000, 320000, 3)
            import pandas as pd
            p = loaded["pipeline"].predict_proba(pd.DataFrame([row], columns=preprocessing.FEATURES))[0]
            self.assertAlmostEqual(float(p.sum()), 1.0, places=4)
    def test_obvious_cases(self):
        predict._bundle = train_model.train(estimator=_estimator(), save=False)
        try:
            low = predict.predict_risk(100000, 30000, 5000, 100000, 1)
            high = predict.predict_risk(40000, 20000, 25000, 900000, 5)
            self.assertEqual(low["level"], "LOW"); self.assertEqual(high["level"], "HIGH")
        finally:
            predict._bundle = None

class FinanceTests(unittest.TestCase):
    def test_demo_profile_is_moderate_caution(self):
        m = finance.compute(demo_profile())
        self.assertEqual(m["level"], "MODERATE"); self.assertEqual(m["health"], "Caution")
        self.assertAlmostEqual(m["emi_r"], .36)
    def test_affordability_verdicts(self):
        p = demo_profile(); m = finance.compute(p)
        small = finance.compute(finance.scenario(p, new_loan=dict(amount=20000, rate=10, years=3)))
        huge = finance.compute(finance.scenario(p, new_loan=dict(amount=2000000, rate=12, years=3)))
        self.assertEqual(finance.affordability(m, huge, 60000)[0], "Not Affordable")
        self.assertIn(finance.affordability(m, small, 700)[0], ("Affordable", "Caution"))
    def test_extra_repayment_reduces_remaining(self):
        p = demo_profile()
        self.assertEqual(finance.compute(finance.scenario(p, extra=2000))["remaining"], finance.compute(p)["remaining"] - 2000)
    def test_warnings_empty_when_healthy(self):
        p = demo_profile(); p["monthly_income"] = 200000; p["loans"] = p["loans"][:1]
        self.assertEqual(finance.warnings(finance.compute(p)), [])
    def test_indian_format(self): self.assertEqual(fmt(320000), "₹3,20,000")

class AITests(unittest.TestCase):
    def test_context_contains_calculated_figures(self):
        c = ai_client.build_context(finance.compute(demo_profile()), {"loan check": "EMI 9000"})
        self.assertIn("₹18,000", c); self.assertIn("MODERATE", c); self.assertIn("EMI 9000", c)
    def test_no_key_returns_friendly_error(self):
        from utils import config
        old = (config.GOOGLE_API_KEY, config.OLLAMA_ENABLED); config.GOOGLE_API_KEY, config.OLLAMA_ENABLED = "", False
        try:
            text, err, eng = ai_client.ask("Why?", finance.compute(demo_profile()))
            self.assertIsNone(text); self.assertIn("GOOGLE_API_KEY", err)
        finally: config.GOOGLE_API_KEY, config.OLLAMA_ENABLED = old
    def test_fallback_answers_use_user_numbers(self):
        m = finance.compute(demo_profile())
        for q in ["Why is my debt risk moderate?", "What is my debt-to-income ratio?", "What if my income decreases?",
                  "How can extra repayment help?", "What if I take another loan?", "Why did my health status change?"]:
            a = ai_client.fallback_answer(q, m); self.assertTrue(len(a) > 40); self.assertNotIn("guarantee", a.lower())
    def test_no_hardcoded_key_in_source(self):
        root = Path(__file__).resolve().parent.parent
        for f in root.rglob("*.py"):
            self.assertNotRegex(f.read_text(encoding="utf-8"), r"AIza[0-9A-Za-z_\-]{20,}")

if __name__ == "__main__": unittest.main()
