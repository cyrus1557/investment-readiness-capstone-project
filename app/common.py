"""Shared pieces used by every page: model bundle, logos, sidebar, input checks, AI explanations, footer."""
import logging
import re
from pathlib import Path

import pandas as pd
import streamlit as st

from investor_app import EXAMPLE_PEOPLE, SAMPLE_PATH, load_bundle, standardise_answer
from llm_layer import SYSTEM_RULES, LLMUnavailable, ask_llm, build_general_question_prompt

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

        # Quick start: closed by default, opens and closes when clicked
        with st.expander("⚡ Quick start", expanded=False):
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
# Ask a question: a small button that floats on every page and opens a chat window
# ---------------------------------------------------------------------------
# The shape of a pop-up window. It is sent from inside the window, so it only affects that window
# (a window is only ever open one at a time) and does not depend on newer CSS.
DIALOG_SHAPES = {
    # A narrow window for a question about something on the page
    "chat": """<style>
    div[role="dialog"] { width: 520px !important; max-width: 92vw !important; max-height: 78vh !important;
        margin-left: auto !important; margin-right: auto !important; }
    </style>""",
    # A medium window in the middle of the screen, narrow enough to leave the sidebar showing
    "window": """<style>
    div[role="dialog"] { width: 600px !important; max-width: 92vw !important; max-height: 80vh !important;
        margin-left: auto !important; margin-right: auto !important; }
    </style>""",
}


def dialog_shape(kind):
    # kind: "chat" (small panel, bottom right) or "window" (medium, middle of the screen)
    st.markdown(DIALOG_SHAPES[kind], unsafe_allow_html=True)
# Short button label -> the full question that is sent
STARTERS = {
    "What is a money market fund?": "What is a money market fund?",
    "SACCO or chama?": "How is a SACCO different from a chama?",
    "Why does inflation matter?": "Why does inflation matter for my savings?",
    "What are Treasury bills?": "What are Treasury bills?",
}
MAX_QUESTIONS = 15   # per visit, to protect the free AI limits


def _stash_question():
    # Runs when the Ask button is pressed, before the box is cleared
    typed = (st.session_state.get("ask_box") or "").strip()
    if typed:
        st.session_state["ask_pending"] = typed


def ask_panel():
    # The whole question-and-answer chat, shown inside the floating window
    products = get_bundle()["recommender"]["product_reference"]
    st.session_state.setdefault("chat_history", [])
    history = st.session_state["chat_history"]
    st.caption("Ask about saving and investing in simple words. Please don't type your name, phone number or ID.")

    picked = None
    if not history:
        for row in (list(STARTERS)[:2], list(STARTERS)[2:]):
            for col, label in zip(st.columns(2), row):
                if col.button(label, key=f"starter_{label}", use_container_width=True):
                    picked = STARTERS[label]

    question = st.session_state.pop("ask_pending", None) or picked
    if history or question:
        # A box with its own height, so long answers scroll inside it and the question box stays in view
        with st.container(height=330, border=False):
            for asked, answer in history[-6:]:
                with st.chat_message("user"):
                    st.write(asked)
                with st.chat_message("assistant"):
                    st.markdown(answer)
            if question:
                if len(history) >= MAX_QUESTIONS:
                    st.info("You've reached the question limit for this visit. Use Quick start → Start again "
                            "in the sidebar to reset.")
                else:
                    with st.chat_message("user"):
                        st.write(question)
                    with st.chat_message("assistant"):
                        with st.spinner("Thinking..."):
                            answer = ai_answer(build_general_question_prompt(products, question, history),
                                               SYSTEM_RULES)
                        if answer:
                            st.markdown(answer)
                            history.append((question, answer))
                        else:
                            st.write("The AI helper is busy right now. Please try again in a minute, or look "
                                     "the word up in Money words explained.")

    with st.form("ask_dialog_form", clear_on_submit=True, border=False):
        box, send = st.columns([4, 1], vertical_alignment="bottom")
        box.text_input("Your question", key="ask_box", max_chars=300, label_visibility="collapsed",
                       placeholder="Type your question here")
        send.form_submit_button("Ask", type="primary", use_container_width=True, on_click=_stash_question)
    if history:
        st.button("Clear the conversation", key="ask_clear",
                  on_click=lambda: st.session_state.update(chat_history=[]))


def _open_ask():
    st.session_state["ask_open"] = True


def _close_ask():
    st.session_state["ask_open"] = False


def ask_button():
    """
    The floating helper in the bottom-right corner: a button that becomes a small chat panel.
    It is a normal container held in the corner by styles.py, not a Streamlit pop-up window,
    because a pop-up window is always placed in the middle of the screen.
    """
    if not llm_available():
        return
    if not st.session_state.get("ask_open"):
        with st.container(key="ask_fab"):
            st.button("💬  Ask a question", key="ask_fab_btn", on_click=_open_ask,
                      help="Questions about saving and investing")
        return
    with st.container(key="ask_panel"):
        title, close = st.columns([5, 1], vertical_alignment="center")
        title.markdown("#### Ask a question")
        close.button("✕", key="ask_close", on_click=_close_ask, help="Close")
        ask_panel()


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
