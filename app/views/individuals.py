"""For individuals: 3 short steps, then options that people like you use (no score), AI help and what-if."""
import logging

import streamlit as st

from common import (INCOME_RANGE_TEXT, LIMITS, ai_answer, clear_individual_boxes, default_answers, example_answers,
                    footer, get_bundle, income_outside_survey, llm_available, range_error)
from investor_app import EXAMPLE_PEOPLE, recommend
from llm_layer import SYSTEM_RULES, build_individual_prompt, build_question_prompt
from styles import field_error, hero, note, recommend_card, step_header, view_switcher

logger = logging.getLogger(__name__)
bundle = get_bundle()
choices = bundle["form_choices"]
product_table = bundle["recommender"]["product_reference"]

QUIZ = {
    "q1": ("1. You put KSh 100 in a savings account that pays 10% interest a year. After one year, "
           "with no withdrawals, how much is in the account?",
           ["Less than KSh 110", "Exactly KSh 110", "More than KSh 110", "I don't know"], "Exactly KSh 110"),
    "q2": ("2. Prices go up by 10% this year, and your savings earn 5% interest. After one year, can your "
           "savings buy more, the same, or less than today?",
           ["More", "The same", "Less", "I don't know"], "Less"),
    "q3": ("3. Which is usually safer?",
           ["Putting all your money in one investment", "Spreading your money across several investments",
            "I don't know"], "Spreading your money across several investments"),
}
STEP_FIELDS = {
    1: ["age", "county", "urban_rural", "household_size", "marital_status"],
    2: ["education", "livelihood", "monthly_income", "prefer_not", "has_id", "mobile_money"],
    3: list(QUIZ),
}
REASON_TAGS = {"Common among similar people": "Popular with people like you", "Next step": "Next step",
               "Starter option": "Good place to start"}

# Answers are kept in "ind_saved", which Streamlit never clears. The boxes on screen use keys "w_<field>",
# which Streamlit deletes when a step is not shown, so each step copies its answers back from ind_saved.
st.session_state.setdefault("ind_step", 1)
st.session_state.setdefault("ind_saved", default_answers(bundle))
st.session_state.setdefault("ind_errors", {})
saved = st.session_state["ind_saved"]


def restore(step):
    for field in STEP_FIELDS[step]:
        if f"w_{field}" not in st.session_state:
            st.session_state[f"w_{field}"] = saved.get(field)


def remember(step):
    for field in STEP_FIELDS[step]:
        saved[field] = st.session_state.get(f"w_{field}")


def go_to(step):
    st.session_state["ind_step"] = step
    st.session_state["ind_errors"] = {}
    st.session_state.pop("ind_view", None)      # results always open on "Your options"


def load_example(name):
    # Fill every answer with an example person and jump straight to the results
    saved.clear()
    saved.update(example_answers(bundle, name))
    clear_individual_boxes()
    st.session_state["example_name"] = name
    go_to(4)


def start_again():
    saved.clear()
    saved.update(default_answers(bundle))
    for key in ["example_name", "ind_qa", "ind_ai_text", "ind_ai_for"]:
        st.session_state.pop(key, None)
    clear_individual_boxes()
    go_to(1)


def show_error(field):
    message = st.session_state["ind_errors"].get(field)
    if message:
        field_error(message)


def answers_for_model():
    # The 11 answers in the form the engine expects
    return {
        "age": saved["age"], "urban_rural": saved["urban_rural"], "county": saved["county"],
        "education": saved["education"], "marital_status": saved["marital_status"],
        "household_size": saved["household_size"], "livelihood": saved["livelihood"],
        "monthly_income": None if saved.get("prefer_not") else saved.get("monthly_income"),
        "has_id": saved["has_id"], "mobile_money": saved["mobile_money"],
        "literacy_score": sum(saved.get(key) == correct for key, (_, _, correct) in QUIZ.items()),
    }


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------
hero("For individuals", "Find options that suit people like you",
     "Answer three short steps. We compare your answers with thousands of Kenyans in the 2024 FinAccess "
     "survey and show the saving and investment options people like you use. You never get a score.")

st.markdown("**Or try an example person:**")
example_cols = st.columns(len(EXAMPLE_PEOPLE))
for col, name in zip(example_cols, EXAMPLE_PEOPLE):
    col.button(name, on_click=load_example, args=(name,), use_container_width=True)

step = st.session_state["ind_step"]
if step <= 3:
    st.progress(step / 3, text=f"Step {step} of 3")

# Step 1: about you
if step == 1:
    restore(1)
    step_header("Step 1 · About you", "These help us find people in the survey with similar circumstances.")
    with st.form("step_1"):
        c1, c2 = st.columns(2)
        with c1:
            st.number_input("Age", value=None, step=1, placeholder="e.g. 30", key="w_age")
            show_error("age")
            st.selectbox("County", choices["county"], index=None, placeholder="Choose your county", key="w_county")
            show_error("county")
            st.selectbox("Do you live in an urban or rural area?", choices["urban_rural"], index=None,
                         placeholder="Choose one", key="w_urban_rural")
            show_error("urban_rural")
        with c2:
            st.number_input("How many people live in your household?", value=None, step=1,
                            placeholder="e.g. 4", key="w_household_size")
            show_error("household_size")
            st.selectbox("Marital status", choices["marital_status"], index=None, placeholder="Choose one",
                         key="w_marital_status")
            show_error("marital_status")
        next_1 = st.form_submit_button("Continue to money and work →", type="primary", use_container_width=True)
    if next_1:
        remember(1)
        errors = {}
        for field, label in [("age", "age"), ("household_size", "household size")]:
            message = range_error(field, saved[field], label)
            if message:
                errors[field] = message
        for field in ["county", "urban_rural", "marital_status"]:
            if saved[field] is None:
                errors[field] = "Please choose an answer."
        st.session_state["ind_errors"] = errors
        if not errors:
            go_to(2)
        st.rerun()

# Step 2: money and work
elif step == 2:
    restore(2)
    step_header("Step 2 · Money and work", "You can choose not to share your income. These answers are used "
                                           "only to find similar people, never to score you.")
    with st.form("step_2"):
        c1, c2 = st.columns(2)
        with c1:
            st.selectbox("Highest level of education", choices["education"], index=None, placeholder="Choose one",
                         key="w_education")
            show_error("education")
            st.selectbox("Main source of income / type of work", choices["livelihood"], index=None,
                         placeholder="Choose one", key="w_livelihood")
            show_error("livelihood")
            st.number_input("Monthly income (KSh)", value=None, step=1000, placeholder="e.g. 15000",
                            key="w_monthly_income")
            show_error("monthly_income")
            st.checkbox("I prefer not to say my income", key="w_prefer_not")
        with c2:
            st.selectbox("Do you have a national ID or passport?", choices["has_id"], key="w_has_id",
                         format_func=lambda label: "Yes" if label.lower().startswith("has id") else "No")
            st.selectbox("Do you use mobile money?", choices["mobile_money"], key="w_mobile_money")
        back_col, next_col = st.columns(2)
        back_2 = back_col.form_submit_button("← Back", use_container_width=True)
        next_2 = next_col.form_submit_button("Continue to money questions →", type="primary",
                                             use_container_width=True)
    if back_2:
        remember(2)
        go_to(1)
        st.rerun()
    if next_2:
        remember(2)
        errors = {}
        for field in ["education", "livelihood"]:
            if saved[field] is None:
                errors[field] = "Please choose an answer."
        if not saved.get("prefer_not"):
            message = range_error("monthly_income", saved.get("monthly_income"), "monthly income")
            if message:
                errors["monthly_income"] = message + (" Or tick 'I prefer not to say'."
                                                      if saved.get("monthly_income") is None else "")
        st.session_state["ind_errors"] = errors
        if not errors:
            go_to(3)
        st.rerun()

# Step 3: money questions
elif step == 3:
    restore(3)
    step_header("Step 3 · Three quick money questions",
                "These are the same topics the survey asked about. It's not a test: 'I don't know' is fine.")
    with st.form("step_3"):
        for key, (question, options, _) in QUIZ.items():
            st.radio(question, options, index=None, key=f"w_{key}")
            show_error(key)
        back_col, next_col = st.columns(2)
        back_3 = back_col.form_submit_button("← Back", use_container_width=True)
        submit = next_col.form_submit_button("🔎 See my options", type="primary", use_container_width=True)
    if back_3:
        remember(3)
        go_to(2)
        st.rerun()
    if submit:
        remember(3)
        errors = {key: "Please choose an answer." for key in QUIZ if saved.get(key) is None}
        st.session_state["ind_errors"] = errors
        if not errors:
            st.session_state.pop("example_name", None)
            go_to(4)
        st.rerun()

# Step 4: results
else:
    answers = answers_for_model()
    try:
        with st.spinner("Finding people like you..."):
            result = recommend(bundle, answers)
    except Exception:
        logger.exception("Recommendation failed")
        st.error("Sorry, we couldn't find your options. Please check your answers and try again.")
        st.button("Edit my answers", on_click=go_to, args=(1,))
        st.stop()
    suggestions = result["suggestions"]

    # Title, one-line summary and the two actions people want first
    st.subheader("Options that people like you use")
    if st.session_state.get("example_name"):
        st.caption(f"Showing the example: {st.session_state['example_name']}. Press Start again to enter your own answers.")
    summary_col, edit_col, again_col = st.columns([4, 1.2, 1.2], vertical_alignment="center")
    summary_col.markdown(f"Based on the **{bundle['recommender']['N_NEIGHBORS']} people** in the survey most like you · "
                         f"You answered **{answers['literacy_score']} of 3** money questions correctly")
    edit_col.button("✏️ Edit answers", on_click=go_to, args=(1,), use_container_width=True)
    again_col.button("↺ Start again", on_click=start_again, use_container_width=True)

    if income_outside_survey(answers["monthly_income"]):
        note("warn", f"Your income (KSh {answers['monthly_income']:,}) is outside the survey's range.",
             INCOME_RANGE_TEXT)
    if result["mean_distance"] > bundle["recommender"]["MAX_MEAN_DISTANCE"]:
        note("warn", "Few people in the survey have answers close to yours.",
             "So we start with simple options that are useful for almost everyone.")
    elif result["starter_step"]:
        note("info", "Good places to start",
             "Few people with answers like yours use investment products yet, so these are good first steps.")

    # Switcher: one view at a time, so nothing is buried at the bottom
    VIEWS = ["📋 Your options"] + (["✨ Explain simply"] if llm_available() else []) + ["🔀 What if?"] + \
            (["💬 Ask a question"] if llm_available() else [])
    view = view_switcher(VIEWS, "ind_view")

    if view == "📋 Your options":
        for rank, (_, s) in enumerate(suggestions.iterrows(), 1):
            recommend_card(rank, s["display_name"], s["plain_sentence"], REASON_TAGS.get(s["reason"]),
                           gold_tag=s["reason"] == "Next step")
            with st.expander(f"Product details · {s['display_name']}"):
                st.markdown(f"- **Risk:** {s['risk']}\n- **Typical minimum:** {s['typical_minimum']}\n"
                            f"- **Getting your money out:** {s['access']}\n- **Time horizon:** {s['time_horizon']}\n"
                            f"- **Regulator:** {s['regulator']}")
        st.caption("Want more? Use the buttons above for a simple explanation, a what-if or a question.")

    elif view == "✨ Explain simply":
        # Opens straight away: the explanation is written the first time, then kept for these options
        options_key = tuple(suggestions["option"])
        if st.session_state.get("ind_ai_for") != options_key:
            with st.spinner("Writing a simple explanation of your options..."):
                text = ai_answer(build_individual_prompt(suggestions, product_table), SYSTEM_RULES)
            st.session_state["ind_ai_text"] = text or ""
            st.session_state["ind_ai_for"] = options_key
        if st.session_state.get("ind_ai_text"):
            with st.container(border=True):
                st.markdown(st.session_state["ind_ai_text"])
                st.caption("Written by AI from our product table. It can make mistakes.")
        else:
            note("info", "The AI helper is busy right now.",
                 "The cards under Your options explain every option. Try again in a minute.")
            st.button("↻ Try again", on_click=lambda: st.session_state.pop("ind_ai_for", None))

    elif view == "🔀 What if?":
        st.write("Change an answer to see how the options for people like you would change. "
                 "This is not cause and effect.")
        w1, w2, w3 = st.columns(3)
        what_if = dict(answers)
        what_if["education"] = w1.selectbox("Education", choices["education"],
                                            index=choices["education"].index(answers["education"]), key="wi_education")
        current_income = answers["monthly_income"] if answers["monthly_income"] is not None else 15_000
        new_income = w2.number_input("Monthly income (KSh)", min_value=0, max_value=LIMITS["monthly_income"][1],
                                     value=int(current_income), step=5_000, key="wi_income")
        # Keep an income that was not shared as "not shared" unless the user actually changes it
        what_if["monthly_income"] = answers["monthly_income"] if new_income == current_income else new_income
        what_if["literacy_score"] = w3.slider("Money questions correct", 0, 3, int(answers["literacy_score"]),
                                              key="wi_literacy")
        if what_if == answers:
            st.caption("Change one of the answers above to compare.")
        else:
            try:
                what_if_result = recommend(bundle, what_if)
            except Exception:
                logger.exception("What-if failed")
                st.error("We couldn't compare these answers.")
            else:
                now_col, then_col = st.columns(2)
                with now_col:
                    st.markdown("**Your options now**")
                    for rank, (_, s) in enumerate(suggestions.iterrows(), 1):
                        recommend_card(rank, s["display_name"], s["plain_sentence"])
                with then_col:
                    st.markdown("**What if**")
                    for rank, (_, s) in enumerate(what_if_result["suggestions"].iterrows(), 1):
                        recommend_card(rank, s["display_name"], s["plain_sentence"])
                new = set(what_if_result["suggestions"]["display_name"]) - set(suggestions["display_name"])
                if new:
                    st.success("New option(s) that would appear: " + ", ".join(sorted(new)) + ".")
                else:
                    st.info("The same options would be suggested.")

    elif view == "💬 Ask a question":
        st.write("Ask anything about saving or investing, for example about one of your options.")
        with st.form("ask_form", clear_on_submit=True):
            question = st.text_input("Your question", placeholder="e.g. What is a SACCO?", max_chars=300,
                                     help="Don't include your name, phone number or other personal details.")
            asked = st.form_submit_button("Ask", type="primary")
        if asked and question.strip():
            with st.spinner("Thinking..."):
                reply = ai_answer(build_question_prompt(suggestions, product_table, question), SYSTEM_RULES)
            if reply:
                st.session_state.setdefault("ind_qa", []).insert(0, (question.strip(), reply))
            else:
                note("info", "The AI helper is busy right now.", "Please try again in a minute.")
        for q, a in st.session_state.get("ind_qa", [])[:5]:      # newest first
            with st.container(border=True):
                st.markdown(f"**You asked:** {q}")
                st.markdown(a)
        st.page_link("views/ask_ai.py", label="Have more questions? Open Ask the AI", icon=":material/chat:")

footer("individuals")
