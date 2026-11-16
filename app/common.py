"""Shared pieces used by every page: model bundle, logos, sidebar, input checks, AI explanations, footer."""
import logging
from pathlib import Path

import streamlit as st

from investor_app import load_bundle
from llm_layer import LLMUnavailable, ask_llm

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
LOGO_ICON = ROOT / "images" / "logo_icon.png"
LOGO_SIDEBAR = ROOT / "images" / "logo_sidebar.png"
LOGO_FULL = ROOT / "images" / "logo_full.png"

DISCLAIMER = ("For learning only, not personal financial advice. "
              "Confirm product terms and provider licensing before acting.")
DATA_NOTE = ("Built on the 2024 FinAccess Household Survey (Central Bank of Kenya, KNBS and FSD Kenya): "
             "20,870 Kenyan adults aged 16 and over.")

# Allowed answers (anything outside gets an error) and the survey's actual income range (outside gets a warning)
LIMITS = {"age": (16, 105), "household_size": (1, 20), "monthly_income": (0, 10_000_000)}
SURVEY_INCOME_RANGE = (100, 200_000)   # lowest and highest monthly income reported in the survey (KSh)

# Plain next step for each likelihood band (institution view)
NEXT_STEP = {
    "High": "Contact first. Introduce investment products (for example a money market fund, Treasury bills "
            "or SACCO shares) and offer a conversation with an adviser.",
    "Medium": "Nurture. Share simple financial education and low-minimum starter options, then follow up.",
    "Low": "Build the basics first: savings, mobile money and a chama or SACCO. Check in again later.",
}


@st.cache_resource(show_spinner="Loading the model...")
def get_bundle():
    # Load the saved models once and reuse them for every visitor
    try:
        return load_bundle()
    except Exception:
        logger.exception("Model bundle failed to load")
        st.error("The model could not be loaded. Please try again later.")
        st.stop()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
def sidebar(pages):
    # Logo, menu, model facts and team (the default menu is hidden in app.py so we can lay it out ourselves)
    with st.sidebar:
        if LOGO_SIDEBAR.exists():
            st.image(str(LOGO_SIDEBAR), width=230)
        else:
            st.markdown("### Predictive Minds")
        st.markdown('<p class="sidebar-label">Menu</p>', unsafe_allow_html=True)
        for page in pages:
            st.page_link(page)
        st.markdown(
            '<div class="sidebar-card"><b>About the model</b><br>'
            'Calibrated XGBoost<br>Test PR-AUC 0.233 (8.6× random)<br>'
            '20,870 adults · FinAccess 2024<br>Sex is never used</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="sidebar-card"><b>Predictive Minds</b><br>'
            'Moringa School Data Science<br>Module 6 capstone</div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Input checks
# ---------------------------------------------------------------------------
def range_error(field, value, label):
    # Error message if a number is missing or outside the allowed range, otherwise None
    low, high = LIMITS[field]
    if value is None:
        return f"Please enter your {label}."
    if not low <= value <= high:
        unit = "KSh " if field == "monthly_income" else ""
        return f"{label.capitalize()} must be between {unit}{low:,} and {unit}{high:,}. You entered {unit}{value:,}."
    return None


def income_outside_survey(income):
    # True if an income was given but is outside what people reported in the survey
    if income is None:
        return False
    low, high = SURVEY_INCOME_RANGE
    return income < low or income > high


INCOME_RANGE_TEXT = (f"People in the survey reported monthly incomes between KSh {SURVEY_INCOME_RANGE[0]:,} and "
                     f"KSh {SURVEY_INCOME_RANGE[1]:,}. Results for incomes outside this range may be less reliable.")


# ---------------------------------------------------------------------------
# AI explanations (keys live only in Streamlit secrets)
# ---------------------------------------------------------------------------
def _secret(name, default=None):
    try:
        return st.secrets.get(name, default)
    except Exception:          # no secrets file at all
        return default


def llm_config():
    return {
        "order": [p.strip() for p in _secret("LLM_ORDER", "groq,gemini").split(",")],
        "groq": {"key": _secret("GROQ_API_KEY"), "model": _secret("GROQ_MODEL", "openai/gpt-oss-120b")},
        "gemini": {"key": _secret("GEMINI_API_KEY"), "model": _secret("GEMINI_MODEL", "gemini-flash-latest")},
    }


def llm_available():
    config = llm_config()
    return any((config.get(name) or {}).get("key") for name in config["order"])


@st.cache_data(ttl=24 * 3600, max_entries=500, show_spinner=False)
def _cached_answer(prompt, system):
    # Same prompt -> same saved answer, so repeat visitors don't use up the free limits
    return ask_llm(prompt, system, llm_config())


def ai_answer(prompt, system):
    # Returns the AI's text, or None if no provider could answer (the page then shows its own sentences)
    try:
        text, provider = _cached_answer(prompt, system)
        logger.warning("LLM answered | provider=%s", provider)
        return text
    except LLMUnavailable:
        logger.warning("LLM unavailable: all providers busy or not set up")
        return None
    except Exception:
        logger.exception("LLM call failed")
        return None


# ---------------------------------------------------------------------------
# Footer: data note, disclaimer and privacy-safe feedback
# ---------------------------------------------------------------------------
def feedback_box(page):
    # Thumbs only (no free text, so no personal details reach the logs). Logged once per click.
    st.divider()
    st.markdown("**Was this page useful?**")
    rating = st.feedback("thumbs", key=f"{page}_rating")
    if rating is not None:
        if st.session_state.get(f"{page}_logged") != rating:
            print(f"FEEDBACK | page={page} | {'thumbs up' if rating == 1 else 'thumbs down'}", flush=True)
            st.session_state[f"{page}_logged"] = rating
        st.success("Thank you. Your feedback helps us improve the app.")


def footer(page):
    st.caption(DATA_NOTE)
    st.caption(DISCLAIMER)
    feedback_box(page)
