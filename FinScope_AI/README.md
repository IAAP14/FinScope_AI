# FinScope AI

**Understand Your Debt. Make Smarter Financial Decisions.**

FinScope AI is an AI-powered financial decision-support app that helps people see whether they can safely take on a new financial
commitment, and warns them early when existing debt may become hard to manage.

---

## Problem Statement
People can take on financial commitments that become difficult to manage relative to their income.

## Proposed Solution
FinScope AI gives early warnings before additional borrowing, analyses the situation of people who already carry substantial debt,
and explains every result in simple language. It works with **sample data or the user's own numbers** - no bank connection needed.

## Features (the six core features)
| # | Feature | Question it answers |
|---|---------|--------------------|
| 1 | **Loan Affordability** | "Can I afford this new loan?" -> Affordable / Caution / Not Affordable, with EMI, EMI-to-income ratio, remaining income |
| 2 | **Debt Risk Analyzer** | "Is my existing debt becoming risky?" -> LOW / MODERATE / HIGH, predicted by an XGBoost model and explained in plain words |
| 3 | **What-If Simulator** | "What happens if my situation changes?" -> current vs simulated situation (Plotly). Nothing is saved unless you choose to |
| 4 | **Debt Repayment Analyzer** | "How does my repayment look?" -> estimated months, interest, and normal vs extra monthly payment |
| 5 | **AI Financial Explanation** | Explains your own calculated results (Google GenAI + LangChain) |
| 6 | **Financial Health Dashboard** | The home page after login: health status, debt risk, EMI, remaining income, warnings, quick actions |

The **Financial Health** page is always the first item in the sidebar, and every other page has a "Back to Financial Health" button.

## Technology Stack
| Package | How it is used |
|---------|---------------|
| Streamlit | App UI, navigation, forms |
| Pandas / NumPy | Demo dataset, feature building, numeric calculations |
| Scikit-learn | Train/test split, `StandardScaler` + `Pipeline`, accuracy / confusion matrix |
| XGBoost | The debt-risk classifier (LOW / MODERATE / HIGH) |
| Joblib | Saves and loads the trained model (`models/debt_risk_model.joblib`) |
| Statsmodels | OLS regression showing which factors move risk the most (Debt Risk page) |
| Matplotlib + Seaborn | Correlation heatmap of the sample data |
| Plotly | Interactive charts: dashboard, What-If, repayment |
| Google GenAI | The model that writes the AI explanations |
| LangChain | `PromptTemplate | LLM | StrOutputParser` chain that builds the prompt from the user's numbers |
| LangChain Community | `ChatMessageHistory` conversation memory + optional local Ollama fallback |
| Requests | Health check for the optional local Ollama server |
| python-dotenv | Loads settings and the API key from `.env` |
| bcrypt + SQLite | Secure login and local storage |

## Project Structure
```
FinScope_AI/
├── app.py                    # entry point: login, sidebar, page routing
├── requirements.txt  .env.example  .python-version
├── data/sample_financial_data.csv    # SYNTHETIC demo dataset (1,500 rows)
├── models/                           # debt_risk_model.joblib + metrics.json (created by training)
├── ml/
│   ├── generate_data.py      # creates the demo CSV
│   ├── preprocessing.py      # features + labels (scikit-learn side)
│   ├── train_model.py        # trains XGBoost, saves with Joblib
│   ├── predict.py            # loads model, predicts risk (never crashes the app)
│   └── analysis.py           # Statsmodels + Seaborn
├── modules/                  # one file per page (the six features + settings pages)
├── components/               # ui.py (cards), charts.py (Plotly), navigation.py, compat.py
├── utils/                    # finance.py (all calculations), ai_client.py (LangChain + GenAI), data.py, validation.py ...
├── auth/                     # register / login / sessions (bcrypt)
├── database/                 # SQLite schema + repository (parameterised SQL)
├── styles/style.css          # the navy fintech theme
└── tests/                    # unit tests
```

## Installation
You need **Python 3.11.9**.

### Virtual Environment
```bash
python -m venv venv
```
Windows PowerShell:
```powershell
.\venv\Scripts\Activate.ps1
```
macOS / Linux:
```bash
source venv/bin/activate
```
Then:
```bash
pip install -r requirements.txt
```

### Environment Variables
Copy `.env.example` to `.env` and add your own Google API key (free at https://aistudio.google.com/apikey):
```text
GOOGLE_API_KEY=your_api_key_here
```
The key is only ever read from `.env`; it is never written in the code. Without a key the app still works fully - the AI page then shows
a calculated explanation built from your numbers instead of a Gemini answer.

## Running the Project
```bash
python -m streamlit run app.py
```
1. Create an account and sign in -> you land on **Financial Health**.
2. Click **Load sample data** (or enter your own in **My Finances**).
3. Try Loan Affordability, Debt Risk, What-If, Repayment and the AI page.

The first launch trains the XGBoost model automatically if `models/debt_risk_model.joblib` does not exist (takes a couple of seconds).
You can also do it yourself: `python -m ml.train_model`.

Run the tests: `python -m unittest discover -s tests`

## Sample Data
`data/sample_financial_data.csv` is **synthetic demo data - not real bank customers**. Each row has income, expenses, EMI, total debt and
number of loans, plus a risk label. Labels come from a transparent rule (EMI share 50%, debt vs income 30%, money left 20%) plus a little random
noise. Regenerate with `python -m ml.generate_data`. The app also has a ready-made demo user profile (Income Rs 50,000, EMI Rs 18,000, debt Rs 3,20,000).

## Machine Learning
- **Goal:** classify debt risk as LOW, MODERATE or HIGH.
- **Features (5):** EMI share of income, total debt in years of income, money left over, expense share of income, number of loans.
- **Model:** scikit-learn `Pipeline` = `StandardScaler` -> `XGBClassifier`; evaluated on a 20% held-out split (accuracy and confusion matrix are saved in `models/metrics.json`).
- **Why XGBoost:** it handles non-linear combinations of ratios well, trains in seconds on small tables and is a standard, explainable choice for tabular data.
- **Joblib** stores the whole pipeline; `ml/predict.py` loads it once.
- The user never sees raw probabilities: the app shows "MODERATE DEBT RISK" and explains why. If the model cannot load, the app falls back to the same rule used to label the data.
- **Honest limit:** the model learned from synthetic data, so it demonstrates the method; it is not a credit-scoring system.

## AI Architecture
```
Your calculated numbers (EMI %, debt, remaining income, risk level, latest loan check / what-if)
        |
        v
LangChain PromptTemplate  (safety rules + your context + recent chat from ChatMessageHistory)
        |
        v
Google GenAI (Gemini) via a small LangChain LLM wrapper
        |
        v
StrOutputParser -> plain-language answer
```
- The AI **explains** calculations the app already did; it does not invent figures.
- Safety rules in the prompt: no guarantees, no loan-approval claims, no investment/legal advice, no access to bank accounts.
- Only calculated figures are sent - never passwords or usernames.
- If Gemini fails (no key, no internet), the app shows a rule-based explanation and keeps working. Optional local fallback: set `OLLAMA_ENABLED=true`.

## Disclaimer
FinScope AI provides educational and decision-support insights based on the information provided. Results are estimates and should not be
considered professional financial advice or guaranteed loan approval.
