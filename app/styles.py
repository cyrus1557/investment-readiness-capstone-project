
"""Shared visual styling and reusable UI components for the Streamlit app."""

import html
import streamlit as st


# =========================================================
# 1. COLOUR PALETTE — FOREST & SAGE
# =========================================================

COLORS = {
    "background": "#F5F5F0",
    "surface": "#FFFFFF",
    "sidebar": "#EDF1EB",

    "primary": "#355C50",
    "primary_dark": "#203A3A",
    "secondary": "#668477",
    "accent": "#B69A6A",

    "text": "#293C37",
    "muted": "#71817A",
    "border": "#DFE6DF",

    "soft_sage": "#E8EFE8",
    "soft_green": "#DCE7DE",
    "soft_gold": "#F3EEE3",
    "soft_neutral": "#F0F1EB",
}


# =========================================================
# 2. GLOBAL APPLICATION STYLES
# =========================================================

def apply_styles():
    """Apply consistent styling across all Streamlit pages."""

    st.markdown(
        f"""
        <style>

        /* -----------------------------------------------
           GENERAL APPLICATION
        ------------------------------------------------ */

        .stApp {{
            background: {COLORS['background']};
            color: {COLORS['text']};
        }}

        .block-container {{
            max-width: 1240px;
            padding-top: 2rem;
            padding-bottom: 3.5rem;
        }}

        h1, h2, h3, h4 {{
            color: {COLORS['text']};
            letter-spacing: -0.025em;
        }}

        p, li {{
            line-height: 1.65;
        }}

        /* -----------------------------------------------
           SIDEBAR
        ------------------------------------------------ */

        [data-testid="stSidebar"] {{
            background: {COLORS['sidebar']};
            border-right: 1px solid {COLORS['border']};
        }}

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {{
            color: {COLORS['primary_dark']};
        }}

        /* -----------------------------------------------
           FORMS AND CONTAINERS
        ------------------------------------------------ */

        div[data-testid="stForm"],
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 16px;
            box-shadow: 0 4px 16px rgba(32, 58, 58, 0.035);
        }}

        /* -----------------------------------------------
           BUTTONS
        ------------------------------------------------ */

        .stButton > button,
        .stDownloadButton > button {{
            border-radius: 9px;
            font-weight: 600;
            padding: 0.55rem 1.15rem;
            transition: all 0.2s ease;
        }}

        .stButton > button[kind="primary"],
        .stDownloadButton > button[kind="primary"] {{
            background: {COLORS['primary']};
            border: 1px solid {COLORS['primary']};
            color: white;
        }}

        .stButton > button[kind="primary"]:hover,
        .stDownloadButton > button[kind="primary"]:hover {{
            background: {COLORS['primary_dark']};
            border-color: {COLORS['primary_dark']};
            color: white;
        }}

        /* -----------------------------------------------
           INPUT FIELDS
        ------------------------------------------------ */

        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea,
        .stSelectbox div[data-baseweb="select"] {{
            border-radius: 9px;
        }}

        /* -----------------------------------------------
           METRICS
        ------------------------------------------------ */

        div[data-testid="stMetric"] {{
            background: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 14px;
            padding: 1rem;
            box-shadow: 0 4px 14px rgba(32, 58, 58, 0.035);
        }}

        div[data-testid="stMetricLabel"] {{
            color: {COLORS['muted']};
        }}

        div[data-testid="stMetricValue"] {{
            color: {COLORS['primary_dark']};
            font-weight: 700;
        }}

        /* -----------------------------------------------
           HERO SECTION
        ------------------------------------------------ */

        .hero {{
            background: linear-gradient(
                120deg,
                #203A3A 0%,
                #355C50 65%,
                #668477 100%
            );
            color: white;
            padding: 2.3rem 2.5rem;
            border-radius: 20px;
            margin-bottom: 1.6rem;
            box-shadow: 0 10px 28px rgba(32, 58, 58, 0.12);
        }}

        .hero h1 {{
            color: #FFFFFF;
            font-size: 2.25rem;
            font-weight: 700;
            margin: 0 0 0.65rem 0;
        }}

        .hero p {{
            color: #E4ECE6;
            font-size: 1.05rem;
            max-width: 780px;
            margin: 0;
            line-height: 1.7;
        }}

        .eyebrow {{
            text-transform: uppercase;
            letter-spacing: 0.13em;
            font-size: 0.74rem;
            font-weight: 700;
            color: #D1DFD4;
            margin-bottom: 0.7rem;
        }}

        /* -----------------------------------------------
           INFORMATION CARDS
        ------------------------------------------------ */

        .info-card {{
            background: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 15px;
            padding: 1.4rem;
            height: 100%;
            box-shadow: 0 4px 16px rgba(32, 58, 58, 0.035);
        }}

        .info-card h3 {{
            color: {COLORS['primary_dark']};
            font-size: 1.12rem;
            margin: 0.65rem 0 0.45rem;
        }}

        .info-card p {{
            color: {COLORS['muted']};
            font-size: 0.94rem;
            margin-bottom: 0;
        }}

        /* -----------------------------------------------
           STEP LABELS
        ------------------------------------------------ */

        .step-chip {{
            display: inline-block;
            background: {COLORS['soft_sage']};
            color: {COLORS['primary_dark']};
            padding: 0.35rem 0.75rem;
            border-radius: 7px;
            font-weight: 650;
            font-size: 0.82rem;
            margin-bottom: 0.6rem;
        }}

        /* -----------------------------------------------
           SECTION INTRODUCTIONS
        ------------------------------------------------ */

        .section-intro {{
            color: {COLORS['muted']};
            margin-top: -0.3rem;
            margin-bottom: 1.2rem;
            line-height: 1.65;
        }}

        /* -----------------------------------------------
           RECOMMENDATION CARDS
        ------------------------------------------------ */

        .recommend-card {{
            background: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-left: 5px solid {COLORS['secondary']};
            border-radius: 13px;
            padding: 1.2rem 1.3rem;
            margin: 0.8rem 0;
            box-shadow: 0 4px 15px rgba(32, 58, 58, 0.035);
        }}

        .recommend-rank {{
            display: inline-grid;
            place-items: center;
            width: 29px;
            height: 29px;
            border-radius: 50%;
            color: white;
            background: {COLORS['primary']};
            font-weight: 700;
            margin-right: 0.5rem;
        }}

        /* -----------------------------------------------
           MUTED TEXT
        ------------------------------------------------ */

        .muted {{
            color: {COLORS['muted']};
        }}

        /* -----------------------------------------------
           PROCESS STRIP
        ------------------------------------------------ */

        .process {{
            display: flex;
            gap: 0.85rem;
            flex-wrap: wrap;
            margin: 1rem 0 1.4rem;
        }}

        .process-item {{
            flex: 1;
            min-width: 190px;
            background: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 13px;
            padding: 1.15rem;
        }}

        .process-number {{
            display: inline-grid;
            place-items: center;
            width: 28px;
            height: 28px;
            color: white;
            background: {COLORS['secondary']};
            border-radius: 50%;
            font-weight: 700;
            margin-right: 0.5rem;
        }}

        /* -----------------------------------------------
           DIVIDERS
        ------------------------------------------------ */

        hr {{
            border-color: {COLORS['border']};
        }}

        /* -----------------------------------------------
           MOBILE RESPONSIVENESS
        ------------------------------------------------ */

        @media (max-width: 700px) {{

            .block-container {{
                padding-top: 1rem;
                padding-bottom: 2rem;
            }}

            .hero {{
                padding: 1.5rem;
                border-radius: 15px;
            }}

            .hero h1 {{
                font-size: 1.7rem;
            }}

            .hero p {{
                font-size: 0.95rem;
            }}

            .process-item {{
                min-width: 100%;
            }}

        }}

        </style>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# 3. HERO COMPONENT
# =========================================================

def hero(eyebrow, title, body):
    """Display a professional page introduction."""

    st.markdown(
        f"""
        <div class="hero">
            <div class="eyebrow">{html.escape(str(eyebrow))}</div>
            <h1>{html.escape(str(title))}</h1>
            <p>{html.escape(str(body))}</p>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# 4. INFORMATION CARD COMPONENT
# =========================================================

def card(icon, title, body):
    """Display a reusable information card."""

    st.markdown(
        f"""
        <div class="info-card">
            <div style="font-size: 1.7rem;">
                {html.escape(str(icon))}
            </div>
            <h3>{html.escape(str(title))}</h3>
            <p>{html.escape(str(body))}</p>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# 5. PROCESS STRIP COMPONENT
# =========================================================

def process_strip(items):
    """Display numbered process steps.

    Expected format:
    [
        ("Step title", "Step description"),
        ("Step title", "Step description")
    ]
    """

    blocks = []

    for number, (title, body) in enumerate(items, start=1):

        blocks.append(
            f"""
            <div class="process-item">
                <span class="process-number">{number}</span>
                <strong>{html.escape(str(title))}</strong>
                <br>
                <span class="muted">{html.escape(str(body))}</span>
            </div>
            """
        )

    st.markdown(
        f'<div class="process">{"".join(blocks)}</div>',
        unsafe_allow_html=True
    )
