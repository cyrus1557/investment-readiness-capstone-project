"""Shared pieces used by every page: model bundle, logos, sidebar, input checks, AI explanations, footer."""
import logging
import re
from pathlib import Path

import pandas as pd
import streamlit as st

from investor_app import EXAMPLE_PEOPLE, SAMPLE_PATH, load_bundle, standardise_answer
from llm_layer import LLMUnavailable, ask_llm

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
LOGO_ICON = ROOT / "images" / "logo_icon.png"
LOGO_SIDEBAR = ROOT / "images" / "logo_sidebar.png"
LOGO_FULL = ROOT / "images" / "logo_full.png"

REPO_URL = "https://github.com/cyrus1557/investment-readiness-capstone-project"
LINKS = {
    "GitHub repository": REPO_URL,
    "Project notebook": f"{REPO_URL}/blob/main/index.ipynb",
    "FinAccess 2024 report (CBK)": "https://www.centralbank.go.ke/wp-content/uploads/2024/12/"
                                   "2024-FINACCESS-HOUSEHOLD-SURVEY-MAIN-REPORT.pdf",
    "Report a problem": f"{REPO_URL}/issues/new",
}

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


def read_customer_csv(source):
    # Keep the answer "None" (no formal education) as text; only empty cells count as blank
    return pd.read_csv(source, keep_default_na=False, na_values=[""])


# ---------------------------------------------------------------------------
# Individual journey state (shared by the individuals page and the sidebar buttons)
# ---------------------------------------------------------------------------
def default_answers(bundle):
    return {"prefer_not": False, "mobile_money": "Yes", "has_id": standardise_answer(bundle, "has_id", "Yes")}


def example_answers(bundle, name):
    # All answers for one example person, in the same form the individuals page saves them
    person = EXAMPLE_PEOPLE[name]
    answers = {field: standardise_answer(bundle, field, person[field])
               for field in ["urban_rural", "county", "education", "marital_status", "livelihood",
                             "has_id", "mobile_money"]}
    answers.update({"age": person["age"], "household_size": person["household_size"],
                    "monthly_income": person["monthly_income"], "prefer_not": False})
    answers.update(dict(zip(["q1", "q2", "q3"], person["quiz"])))
    return answers


def clear_individual_boxes():
    # Remove what the form boxes hold, so they refill from the saved answers
    for key in [k for k in st.session_state if str(k).startswith(("w_", "wi_"))]:
        del st.session_state[key]


def reset_all():
    # Start again: clear every answer, result and uploaded list
    for key in [k for k in st.session_state if str(k).startswith(("w_", "wi_", "ind_", "inst_", "chat_"))]:
        del st.session_state[key]
    st.session_state.pop("example_name", None)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
def sidebar(pages):
    # pages: home, individuals, institutions, then the rest of the menu (built in app.py)
    home, individuals, institutions = pages[0], pages[1], pages[2]
    with st.sidebar:
        if LOGO_SIDEBAR.exists():
            st.image(str(LOGO_SIDEBAR), width=230)
        else:
            st.markdown("### Predictive Minds")

        st.markdown('<p class="sidebar-label">Menu</p>', unsafe_allow_html=True)
        for page in pages:
            st.page_link(page)

        st.markdown('<p class="sidebar-label">Quick start</p>', unsafe_allow_html=True)
        if st.button("▶  Try an example person", key="sb_example", use_container_width=True):
            name = next(iter(EXAMPLE_PEOPLE))
            clear_individual_boxes()
            st.session_state["ind_saved"] = example_answers(get_bundle(), name)
            st.session_state["ind_step"] = 4
            st.session_state["ind_errors"] = {}
            st.session_state["example_name"] = name
            st.switch_page(individuals)
        if st.button("📊  Try sample data", key="sb_sample", use_container_width=True):
            try:
                st.session_state["inst_raw"] = read_customer_csv(SAMPLE_PATH)
                st.session_state["inst_source"] = "sample data (150 people from the survey's test set)"
            except Exception:
                logger.exception("Sample file failed to load")
            st.switch_page(institutions)
        if st.button("↺  Start again", key="sb_reset", use_container_width=True):
            reset_all()
            st.switch_page(home)

        st.markdown(
            '<div class="sidebar-card"><b>About the model</b><br>'
            'Calibrated XGBoost<br>Test PR-AUC 0.233 (8.6× random)<br>'
            '20,870 adults · FinAccess 2024<br>Sex is never used</div>',
            unsafe_allow_html=True,
        )
        links = "".join(f'<a href="{url}" target="_blank" rel="noopener">↗ {name}</a>' for name, url in LINKS.items())
        st.markdown(f'<p class="sidebar-label">Links</p><div class="sidebar-links">{links}</div>',
                    unsafe_allow_html=True)


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
# Footer: data note, disclaimer and feedback
# ---------------------------------------------------------------------------
EMAIL = re.compile(r"\S+@\S+\.\S+")
LONG_NUMBER = re.compile(r"\+?\d[\d\s\-]{5,}\d")   # 7+ digits: phone, ID or account numbers


def remove_personal_details(text):
    # Comments are saved in the app logs, so emails and long numbers are blanked out first
    return LONG_NUMBER.sub("[removed]", EMAIL.sub("[removed]", text)).strip()


def feedback_box(page):
    st.divider()
    st.markdown("**Was this page useful?**")
    rating = st.feedback("thumbs", key=f"{page}_rating")
    verdict = {0: "thumbs down", 1: "thumbs up"}.get(rating, "no rating")
    if rating is not None and st.session_state.get(f"{page}_logged") != rating:
        print(f"FEEDBACK | page={page} | {verdict}", flush=True)
        st.session_state[f"{page}_logged"] = rating

    with st.form(f"{page}_feedback_form", clear_on_submit=True):
        comment = st.text_area("Anything we should improve? (optional)", max_chars=500, height=90,
                               placeholder="Tell us what worked or what was confusing.",
                               help="Please don't include names, phone numbers, ID or account numbers.")
        sent = st.form_submit_button("Send feedback")
    if sent:
        if comment.strip():
            print(f"FEEDBACK | page={page} | {verdict} | comment={remove_personal_details(comment)!r}", flush=True)
            st.success("Thank you. Your feedback helps us improve the app.")
        else:
            st.info("Write a comment first, or just use the thumbs above.")
    elif rating is not None:
        st.success("Thank you. Your feedback helps us improve the app.")


def footer(page):
    st.caption(DATA_NOTE)
    st.caption(DISCLAIMER)
    feedback_box(page)
