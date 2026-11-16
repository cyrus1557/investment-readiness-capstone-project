"""Ask the AI: questions about saving and investing, answered from general knowledge with trusted links."""
import streamlit as st

from common import DATA_NOTE, ai_answer, feedback_box, get_bundle, llm_available
from llm_layer import SYSTEM_RULES, build_general_question_prompt
from styles import hero, note

bundle = get_bundle()
products = bundle["recommender"]["product_reference"]
# Short button label -> the full question that is sent
STARTERS = {
    "What is a money market fund?": "What is a money market fund?",
    "SACCO or chama?": "How is a SACCO different from a chama?",
    "Why does inflation matter?": "Why does inflation matter for my savings?",
    "What are Treasury bills?": "What are Treasury bills?",
}
MAX_QUESTIONS = 15   # per visit, to protect the free AI limits

hero("Ask the AI", "Questions about saving and investing",
     "Ask in simple words. You get a short answer with links to trusted Kenyan sources to read more. "
     "It never gives you a score or personal advice.")

if not llm_available():
    note("info", "The AI helper isn't switched on yet.",
         "Meanwhile, Money words explained covers the main products and money words.")
    st.page_link("views/glossary.py", label="Open Money words explained", icon=":material/menu_book:")
    st.stop()

st.session_state.setdefault("chat_history", [])
history = st.session_state["chat_history"]
note("warn", "Keep it private.", "Don't type your name, phone number, ID or account numbers.")

st.caption("Try one of these:")
picked = None
for row in (list(STARTERS)[:2], list(STARTERS)[2:]):
    for col, label in zip(st.columns(2), row):
        if col.button(label, use_container_width=True):
            picked = STARTERS[label]

for question, answer in history:
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        st.markdown(answer)

typed = st.chat_input("Ask a question about saving or investing", max_chars=300)
question = typed or picked
if question:
    if len(history) >= MAX_QUESTIONS:
        st.info("You've reached the question limit for this visit. Open Quick start → Start again in the sidebar "
                "to reset.")
    else:
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                answer = ai_answer(build_general_question_prompt(products, question, history), SYSTEM_RULES)
            if answer:
                st.markdown(answer)
                history.append((question, answer))
            else:
                st.write("The AI helper is busy right now. Please try again in a minute, or look the word up "
                         "in Money words explained.")

if history and st.button("Clear the conversation"):
    st.session_state["chat_history"] = []
    st.rerun()

# Footer without the "for learning only" line: each AI answer carries its own disclaimer
st.caption(DATA_NOTE)
feedback_box("ask_ai")
st.write("")   # a little space so the question box at the bottom doesn't cover the feedback
st.write("")
