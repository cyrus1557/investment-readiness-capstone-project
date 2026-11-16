"""Ask the AI: simple questions about saving and investing, answered from our product table."""
import streamlit as st

from common import ai_answer, footer, get_bundle, llm_available
from llm_layer import SYSTEM_RULES, build_general_question_prompt
from styles import hero, note

bundle = get_bundle()
products = bundle["recommender"]["product_reference"]
STARTERS = ["What is a money market fund?", "How is a SACCO different from a chama?",
            "Why does inflation matter for my savings?", "What are Treasury bills?"]
MAX_QUESTIONS = 15   # per visit, to protect the free AI limits

hero("Ask the AI", "Questions about saving and investing",
     "Ask in simple words. The AI answers from our product table and never gives you a score or personal advice.")

if not llm_available():
    note("info", "The AI helper isn't switched on yet.",
         "Meanwhile, Money words explained covers the main products and money words.")
    st.page_link("views/glossary.py", label="Open Money words explained", icon=":material/menu_book:")
    footer("ask_ai")
    st.stop()

st.session_state.setdefault("chat_history", [])
history = st.session_state["chat_history"]
note("warn", "Keep it private.", "Don't type your name, phone number, ID or account numbers.")

st.caption("Try one of these:")
starter_cols = st.columns(len(STARTERS))
picked = None
for col, text in zip(starter_cols, STARTERS):
    if col.button(text, use_container_width=True):
        picked = text

for question, answer in history:
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        st.markdown(answer)

typed = st.chat_input("Ask a question about saving or investing", max_chars=300)
question = typed or picked
if question:
    if len(history) >= MAX_QUESTIONS:
        st.info("You've reached the question limit for this visit. Press Start again in the sidebar to reset.")
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

st.caption("Answers are written by AI and can make mistakes. Check with a licensed provider before acting.")
footer("ask_ai")
