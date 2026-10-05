import os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import init_db
from database import repository as repo
from utils import finance
from utils.validation import ValidationError, validate_password, validate_username, clean_amount

try:
    from auth import service
    from auth.security import hash_password, verify_password
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False

def profile(**kw):
    p = {"monthly_income": 60000, "other_income": 0, "essential": {"household": 20000, "food": 0, "education": 0, "transport": 0, "utilities": 0, "essential_other": 0},
         "non_essential": {"shopping": 6000, "entertainment": 0, "non_essential_other": 0},
         "loans": [{"name": "Home", "original_amount": 500000, "outstanding": 300000, "rate": 9, "emi": 12000, "remaining_months": 40}],
         "commitments": [{"name": "Insurance", "monthly_amount": 1000}]}
    p.update(kw); return p

class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.db = os.path.join(self.tmp.name, "t.db"); init_db(self.db)
    def tearDown(self): self.tmp.cleanup()

class FinanceTests(unittest.TestCase):
    def test_emi_zero_rate(self): self.assertAlmostEqual(finance.emi_for(1200, 0, 12), 100)
    def test_emi_positive_rate(self): self.assertAlmostEqual(finance.emi_for(100000, 12, 12), 8884.88, places=1)
    def test_metrics(self):
        m = finance.compute(profile())
        self.assertEqual(m["avail"], 60000 - 20000 - 12000 - 1000); self.assertAlmostEqual(m["emi_r"], .2)
    def test_no_income(self): self.assertIsNone(finance.compute(profile(monthly_income=0)))
    def test_extra_payment_is_faster(self):
        l = profile()["loans"]
        self.assertLess(finance.simulate_repayment(l, 5000)["months"], finance.simulate_repayment(l)["months"])
    def test_unpayable_loan(self):
        l = [{"outstanding": 100000, "rate": 24, "emi": 1000}]
        self.assertIsNone(finance.simulate_repayment(l)["months"])
    def test_high_risk(self):
        p = profile(loans=[{"name": "x", "original_amount": 0, "outstanding": 900000, "rate": 12, "emi": 35000, "remaining_months": 30}])
        self.assertEqual(finance.compute(p)["level"], "HIGH")
    def test_scenario_new_loan_raises_emi(self):
        m2 = finance.compute(finance.scenario(profile(), new_loan=dict(amount=200000, rate=10, years=3)))
        self.assertGreater(m2["emi"], 12000)
    def test_insights_cautious(self):
        for i in finance.build_insights(finance.compute(profile())):
            self.assertNotIn("guarantee", i["text"].lower().replace("not guarantee", ""))

class ValidationTests(unittest.TestCase):
    def test_password_rules(self):
        for bad in ["short1", "onlyletters", "12345678"]:
            with self.assertRaises(ValidationError): validate_password(bad)
        validate_password("goodpass1")
    def test_username(self):
        with self.assertRaises(ValidationError): validate_username("a b;--")
    def test_amount(self):
        with self.assertRaises(ValidationError): clean_amount(-5, "x")
        with self.assertRaises(ValidationError): clean_amount("abc", "x")

class RepoTests(Base):
    def test_save_and_isolation(self):
        a = repo.create_user("alice", "h", "A", db=self.db); b = repo.create_user("bob", "h", "B", db=self.db)
        repo.save_profile(a, profile(), db=self.db)
        self.assertEqual(len(repo.get_profile(a, db=self.db)["loans"]), 1)
        self.assertEqual(repo.get_profile(b, db=self.db)["loans"], []); self.assertEqual(repo.get_profile(b, db=self.db)["monthly_income"], 0)
    def test_sql_injection_text_is_inert(self):
        a = repo.create_user("alice", "h", db=self.db)
        p = profile(); p["loans"][0]["name"] = "x'); DROP TABLE users;--"
        repo.save_profile(a, p, db=self.db); self.assertIsNotNone(repo.get_user(a, db=self.db))
    def test_negative_rejected(self):
        a = repo.create_user("alice", "h", db=self.db)
        with self.assertRaises(ValidationError): repo.save_profile(a, profile(monthly_income=-1), db=self.db)
    def test_blank_rows_skipped_and_records(self):
        a = repo.create_user("alice", "h", db=self.db); p = profile(); p["loans"].append({"name": None, "outstanding": None, "emi": None})
        repo.save_profile(a, p, db=self.db); self.assertEqual(len(repo.get_profile(a, db=self.db)["loans"]), 1)
        repo.add_record(a, finance.compute(repo.get_profile(a, db=self.db)), db=self.db); self.assertEqual(len(repo.list_records(a, db=self.db)), 1)
    def test_delete_cascades(self):
        a = repo.create_user("alice", "h", db=self.db); repo.save_profile(a, profile(), db=self.db); repo.delete_user(a, db=self.db)
        self.assertEqual(repo.get_profile(a, db=self.db)["loans"], [])

@unittest.skipUnless(HAS_BCRYPT, "bcrypt not installed")
class AuthTests(Base):
    def test_hash_not_plaintext(self):
        h = hash_password("secret123"); self.assertNotIn("secret123", h); self.assertTrue(verify_password("secret123", h)); self.assertFalse(verify_password("nope", h))
    def test_register_login(self):
        service.register("alice", "secret123", "secret123", db=self.db)
        self.assertEqual(service.authenticate("alice", "secret123", db=self.db)["username"], "alice")
        with self.assertRaises(ValidationError): service.authenticate("alice", "wrong", db=self.db)
    def test_duplicate_and_mismatch(self):
        service.register("alice", "secret123", "secret123", db=self.db)
        with self.assertRaises(ValidationError): service.register("ALICE", "secret123", "secret123", db=self.db)
        with self.assertRaises(ValidationError): service.register("bob", "secret123", "different1", db=self.db)
    def test_lockout(self):
        service.register("alice", "secret123", "secret123", db=self.db)
        for _ in range(5):
            with self.assertRaises(ValidationError): service.authenticate("alice", "bad", db=self.db)
        with self.assertRaises(ValidationError) as c: service.authenticate("alice", "secret123", db=self.db)
        self.assertIn("Too many", str(c.exception))

if __name__ == "__main__": unittest.main()
