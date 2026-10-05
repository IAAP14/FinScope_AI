"""AI Financial Explanation backend.

Stack (all three are required by the project brief):
  * Google GenAI (google-genai)  -> the model that writes the explanation
  * LangChain (langchain-core)   -> PromptTemplate + LCEL chain:  prompt | llm | StrOutputParser
  * LangChain Community          -> ChatMessageHistory (conversation memory) and the optional Ollama fallback

Only CALCULATED figures are sent to the model (no username, no password, no raw database rows).
If the AI is unavailable, the app still shows a rule-based explanation built from the same numbers.
"""
from utils import config
from utils.format import fmt, fmt_months

SYSTEM = (
    "You are FinScope AI, a calm, supportive financial education assistant inside a debt-awareness app. "
    "Explain the user's ALREADY CALCULATED figures in simple language for a non-expert. "
    "Rules: use only the figures given below; if something is missing, say it was not provided. "
    "Never guarantee loan approval, outcomes or debt-free dates; use phrases like 'based on the information entered' "
    "and 'estimated'. Do not give investment, tax or legal advice, do not encourage new borrowing, and never claim to "
    "access bank accounts. Do not show raw model probabilities. Answer the question directly in under 160 words, "
    "short paragraphs, and end with one practical thing the user could review.")

TEMPLATE = (
    "{system}\n\n"
    "=== USER'S CALCULATED FINANCIAL CONTEXT ===\n{context}\n\n"
    "=== RECENT CONVERSATION ===\n{history}\n\n"
    "=== QUESTION ===\n{question}\n\nAnswer:")

# ---------------------------------------------------------------- context
def build_context(m, notes=None):
    """Turn the app's calculated metrics (and the latest loan / what-if results) into text for the prompt."""
    if not m: return "The user has not entered any financial information yet."
    loans = "; ".join(f"{l['name']}: outstanding {fmt(l['outstanding'])}, EMI {fmt(l['emi'])}, rate {l['rate']}%"
                      for l in m["loans"]) or "none"
    text = (f"Monthly income {fmt(m['inc'])}; essential expenses {fmt(m['ess'])}; non-essential expenses {fmt(m['non'])}; "
            f"other commitments {fmt(m['commit'])}; total EMI {fmt(m['emi'])} ({m['emi_r']:.0%} of income); "
            f"total debt {fmt(m['debt'])} ({m['dti']:.1f} years of income); income left after essentials, EMIs and commitments "
            f"{fmt(m['avail'])}; left after non-essential spending {fmt(m['remaining'])}; active loans {m['n']} ({loans}); "
            f"debt risk level {m['level']}; overall financial health {m.get('health', 'n/a')}; "
            f"pressure from additional borrowing {m['pressure']}; estimated time to clear current debt {fmt_months(m['months'])}.")
    for k, v in (notes or {}).items(): text += f"\nLatest {k}: {v}"
    return text

def _history_text(history):
    return "\n".join(f"{'User' if r == 'user' else 'Assistant'}: {t}" for r, t in (history or [])[-6:]) or "(none)"

# ---------------------------------------------------------------- LangChain pieces
def _make_gemini_llm():
    """A LangChain LLM that calls Google GenAI. Built lazily so the app starts even without the packages."""
    from langchain_core.language_models.llms import LLM
    from google import genai
    from google.genai import types

    class GeminiLLM(LLM):
        model: str = config.GEMINI_MODEL
        api_key: str = ""
        temperature: float = 0.3

        @property
        def _llm_type(self): return "google-genai"

        def _call(self, prompt, stop=None, run_manager=None, **kwargs):
            client = genai.Client(api_key=self.api_key, http_options=types.HttpOptions(timeout=config.AI_TIMEOUT * 1000))
            # generous token cap: Gemini 2.5 models count internal "thinking" tokens toward the limit
            resp = client.models.generate_content(
                model=self.model, contents=prompt,
                config=types.GenerateContentConfig(temperature=self.temperature, max_output_tokens=2048))
            return (resp.text or "").strip()

    return GeminiLLM(api_key=config.GOOGLE_API_KEY)

def _make_ollama_llm():
    """Optional local fallback through LangChain Community."""
    from langchain_community.llms import Ollama
    return Ollama(base_url=config.OLLAMA_HOST, model=config.OLLAMA_MODEL, timeout=config.OLLAMA_TIMEOUT)

def _chain(llm):
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    return PromptTemplate.from_template(TEMPLATE) | llm | StrOutputParser()

def make_history(pairs):
    """LangChain Community chat memory built from the saved (role, text) pairs."""
    try:
        from langchain_community.chat_message_histories import ChatMessageHistory
        h = ChatMessageHistory()
        for role, text in (pairs or [])[-6:]:
            (h.add_user_message if role == "user" else h.add_ai_message)(text)
        return [("user" if msg.type == "human" else "assistant", msg.content) for msg in h.messages]
    except Exception:
        return list(pairs or [])[-6:]

# ---------------------------------------------------------------- public API
def ollama_online():
    """Quick check (Requests) that the optional local Ollama server is reachable."""
    try:
        import requests
        return requests.get(f"{config.OLLAMA_HOST}/api/tags", timeout=3).status_code == 200
    except Exception:
        return False

def status():
    """Short, user-safe description of which AI engine will answer."""
    if config.GOOGLE_API_KEY: return "gemini", f"Google Gemini ({config.GEMINI_MODEL})"
    if config.OLLAMA_ENABLED:
        return ("ollama", f"Local Ollama ({config.OLLAMA_MODEL})") if ollama_online() else ("none", "Local Ollama is offline")
    return "none", "AI key not set"

def ask(question, m, history=None, notes=None):
    """Return (answer, error, engine). `error` is a short message safe to show to users, or None."""
    question = (question or "").strip()[:1000]
    if not question: return None, "Please type a question first.", None
    if not m: return None, "Add your financial information first so I can explain your figures.", None
    variables = dict(system=SYSTEM, context=build_context(m, notes), history=_history_text(make_history(history)), question=question)
    last_err = "AI explanation is temporarily unavailable."
    attempts = []
    if config.GOOGLE_API_KEY: attempts.append(("Google Gemini", _make_gemini_llm))
    if config.OLLAMA_ENABLED: attempts.append(("Local Ollama", _make_ollama_llm))
    if not attempts:
        return None, "No AI key is configured (add GOOGLE_API_KEY to your .env file).", None
    for name, factory in attempts:
        try:
            text = _chain(factory()).invoke(variables).strip()
            if text: return text, None, name
        except ImportError:
            last_err = "AI packages are not installed. Run: pip install -r requirements.txt"
        except Exception:
            last_err = "AI explanation is temporarily unavailable. Your financial analysis is still available."
    return None, last_err, None

# ---------------------------------------------------------------- rule-based explanations (no AI needed)
def fallback_answer(question, m, notes=None):
    """Answer common questions straight from the calculated figures. Used when the AI is unavailable."""
    if not m: return "Add your income and loans in My Finances first."
    q = (question or "").lower()
    emi, inc = fmt(m["emi"]), fmt(m["inc"])
    if "debt-to-income" in q or "debt to income" in q or "ratio" in q:
        return (f"Your total debt is {fmt(m['debt'])}, which is about {m['dti']:.1f} years of your income ({inc} a month). "
                f"A lower number means your debt is small compared with what you earn. Separately, your EMIs take {m['emi_r']:.0%} of income.")
    if "decrease" in q or "income drop" in q or "income fall" in q or "lose" in q:
        low = m["inc"] * .8; share = m["emi"] / low if low else 0
        return (f"If your income fell by 20% (to about {fmt(low)}), your EMIs of {emi} would take about {share:.0%} of it. "
                f"Try the What-If Simulator to see this with your own numbers. These are estimates, not predictions.")
    if "extra" in q or "additional" in q or "repay" in q:
        return (f"Paying extra each month reduces your balance faster, so less interest builds up. Right now your debt of {fmt(m['debt'])} "
                f"is estimated to clear in {fmt_months(m['months'])} at current payments. See the Debt Repayment Analyzer to compare amounts.")
    if "another loan" in q or "new loan" in q or "take" in q and "loan" in q:
        return (f"Your EMIs already use {m['emi_r']:.0%} of income. A new loan adds to that, and borrowing pressure currently looks "
                f"{m['pressure'].lower()}. Use Loan Affordability to test an exact amount before deciding.")
    if "unaffordable" in q or "afford" in q:
        return (f"Affordability depends on how much of your income is already committed. Your EMIs are {m['emi_r']:.0%} of income and "
                f"{fmt(m['remaining'])} is left each month after spending. A new EMI has to fit inside that remaining amount.")
    if "health" in q or "status" in q or "change" in q:
        return (f"Your overall financial health is {m.get('health', 'n/a')}. It reflects your debt risk ({m['level'].title()}), "
                f"how much of income goes to EMIs ({m['emi_r']:.0%}) and what is left after expenses ({fmt(m['remaining'])}).")
    return (f"Your debt risk is {m['level'].title()}. EMIs take {m['emi_r']:.0%} of your income ({emi}), total debt is {fmt(m['debt'])}, "
            f"and {fmt(m['remaining'])} is left each month after all spending. "
            + {"LOW": "Debt looks manageable on these figures.",
               "MODERATE": "Debt is manageable, but another loan could add pressure.",
               "HIGH": "Your debt payments take a large part of your income, so reviewing expenses or repayment options may help."}[m["level"]])
