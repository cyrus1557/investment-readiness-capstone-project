"""Front door of the Predictive Minds app: page settings, styling, sidebar and the list of pages."""
import streamlit as st

from common import LOGO_ICON, sidebar
from styles import apply_styles

st.set_page_config(
    page_title="Predictive Minds · Investor likelihood and options",
    page_icon=str(LOGO_ICON) if LOGO_ICON.exists() else "💡",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_styles()

# Order matters: home, individuals and institutions first (the sidebar's quick buttons use them)
pages = [
    st.Page("views/home.py", title="Home", icon=":material/home:", default=True),
    st.Page("views/individuals.py", title="For individuals", icon=":material/explore:"),
    st.Page("views/institutions.py", title="For institutions", icon=":material/account_balance:"),
    st.Page("views/explore.py", title="Explore the data", icon=":material/query_stats:"),
    st.Page("views/glossary.py", title="Money words explained", icon=":material/menu_book:"),
    st.Page("views/ask_ai.py", title="Ask the AI", icon=":material/chat:"),
    st.Page("views/model.py", title="Model and fairness", icon=":material/insights:"),
    st.Page("views/about.py", title="About and limits", icon=":material/info:"),
]
current = st.navigation(pages, position="hidden")   # we draw our own menu in the sidebar
sidebar(pages)
current.run()
