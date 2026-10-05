"""Demo (sample) financial profile so the app works immediately, without any bank connection."""
import copy

DEMO_PROFILE = {
    "monthly_income": 50000.0, "other_income": 0.0,
    "essential": {"household": 8000.0, "food": 5000.0, "education": 0.0, "transport": 2500.0,
                  "utilities": 2000.0, "essential_other": 500.0},
    "non_essential": {"shopping": 2000.0, "entertainment": 1500.0, "non_essential_other": 0.0},
    "loans": [
        {"name": "Personal loan", "original_amount": 250000.0, "outstanding": 140000.0, "rate": 14.0, "emi": 8000.0, "remaining_months": 20},
        {"name": "Two-wheeler loan", "original_amount": 120000.0, "outstanding": 60000.0, "rate": 11.0, "emi": 4000.0, "remaining_months": 16},
        {"name": "Consumer / card loan", "original_amount": 150000.0, "outstanding": 120000.0, "rate": 16.0, "emi": 6000.0, "remaining_months": 24},
    ],
    "commitments": [{"name": "Insurance", "monthly_amount": 1000.0}],
}

def demo_profile():
    return copy.deepcopy(DEMO_PROFILE)
