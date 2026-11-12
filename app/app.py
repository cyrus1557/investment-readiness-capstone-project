"""Streamlit entry point for the Investor Likelihood and Recommendation System."""
import streamlit as st
from styles import apply_styles

st.set_page_config(page_title="Investor Likelihood and Recommendations", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
apply_styles()

pages = [
    st.Page("views/home.py", title="Home", icon="🏠", default=True),
    st.Page("views/individuals.py", title="For individuals", icon="🧭"),
    st.Page("views/institutions.py", title="For institutions", icon="🏛️"),
    st.Page("views/about.py", title="About and limits", icon="ℹ️"),
]
st.navigation(pages).run()
