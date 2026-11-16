"""Home page: what the app does and the two journeys (individuals and institutions)."""
import streamlit as st

from common import LOGO_SIDEBAR, footer
from styles import card, hero, process_strip

hero("Investor likelihood and options for Kenya",
     "Find the right saving and investment options",
     "Built on the 2024 FinAccess survey of 20,870 Kenyan adults. Individuals see options that people like "
     "them use. Institutions see which customers are most likely to invest, and why.",
     logo=LOGO_SIDEBAR)

st.markdown("### Choose your journey")
left, right = st.columns(2, gap="large")
with left:
    card("🧭", "I am an individual",
         "Answer three short steps and see the saving and investment options that people like you use. "
         "You never get a score.", journey=True)
    st.write("")
    if st.button("Explore my options →", type="primary", use_container_width=True):
        st.switch_page("views/individuals.py")
with right:
    card("🏛️", "I represent an institution",
         "Upload a customer list, or try our sample, and see each person's investor likelihood band, "
         "the main reasons and a ranked list to download.", journey=True)
    st.write("")
    if st.button("Analyse a customer list →", type="primary", use_container_width=True):
        st.switch_page("views/institutions.py")

st.markdown("### The data in numbers")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Kenyan adults in the survey", "20,870")
m2.metric("Who invest today", "2.7%")
m3.metric("Model PR-AUC on new people", "0.233", help="About 8.6 times better than random guessing (0.027).")
m4.metric("Inputs used", "11", help="Sex is never used as an input.")

st.markdown("### How it works")
process_strip([
    ("Answer 11 questions", "Age, county, education, work, income, ID, mobile money and a 3-question money quiz."),
    ("Compare", "We compare the answers with thousands of similar Kenyans in the survey."),
    ("See results", "Individuals see options. Institutions see a likelihood band and reasons."),
    ("Understand", "Plain explanations, a money glossary and optional AI help in simple words."),
])

st.markdown("### Designed responsibly")
a, b, c = st.columns(3)
with a:
    card("🔐", "Privacy-aware", "Sex is never used to score anyone or to find similar people. "
                                "Institutions upload only non-identifying references.")
with b:
    card("🔎", "Explainable", "Every likelihood comes with the main reasons behind it, in plain sentences.")
with c:
    card("⚖️", "Fair and honest", "Likelihood shows resemblance to today's investors, not ability or readiness. "
                                  "Suggestions are for learning, not advice.")

footer("home")
