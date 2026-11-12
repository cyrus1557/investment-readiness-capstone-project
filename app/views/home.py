"""Landing page: explain the two user journeys clearly."""
import streamlit as st
from common import DATA_NOTE, DISCLAIMER, feedback_box
from styles import apply_styles, card, hero

apply_styles()
hero("Predictive Minds · Moringa School", "Investor likelihood and financial options", "Explore financial options used by similar Kenyan adults, or help an institution prioritise customer profiles by investor likelihood.")

st.markdown("### Choose your journey")
c1, c2 = st.columns(2, gap="large")
with c1:
    card("🧭", "I am an individual", "Answer a short three-step questionnaire and explore saving and investment options used by people with similar profiles. You will not receive a personal score.")
    if st.button("Explore options used by people like me →", type="primary", use_container_width=True):
        st.switch_page("views/individuals.py")
with c2:
    card("🏛️", "I represent an institution", "Upload a customer CSV, validate records, review High, Medium and Low investor-likelihood bands, explanations and fairness monitoring.")
    if st.button("Analyse customer profiles →", use_container_width=True):
        st.switch_page("views/institutions.py")

st.markdown("### How the prototype is designed")
a,b,c = st.columns(3)
with a: card("🔐", "Privacy-aware", "Sex is excluded from scoring and similarity matching. Institutions should upload non-identifying customer references only.")
with b: card("🔎", "Explainable", "Institutional likelihood results include plain-language reasons derived from model contributions.")
with c: card("⚖️", "Responsible", "Recommendations are educational, model outputs are not readiness scores, and what-if comparisons are not causal claims.")

st.caption(DATA_NOTE)
st.caption(DISCLAIMER)
feedback_box("home")
