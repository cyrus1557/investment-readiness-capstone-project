"""Shared visual styling and reusable UI components for the Streamlit app."""
import html
import streamlit as st

COLORS = {
    "background": "#F7F5F2", "surface": "#FFFFFF", "primary": "#4F46E5",
    "primary_dark": "#3730A3", "secondary": "#0F766E", "accent": "#E76F51",
    "text": "#273142", "muted": "#64748B", "border": "#E2E8F0",
    "soft_indigo": "#EEF2FF", "soft_teal": "#ECFDF5", "soft_coral": "#FFF1ED",
}

def apply_styles():
    st.markdown(f"""
    <style>
    .stApp {{ background: {COLORS['background']}; color: {COLORS['text']}; }}
    .block-container {{ padding-top: 2rem; padding-bottom: 3.5rem; max-width: 1240px; }}
    h1, h2, h3 {{ color: {COLORS['text']}; letter-spacing: -0.025em; }}
    [data-testid="stSidebar"] {{ background: #FBFAF8; border-right: 1px solid {COLORS['border']}; }}
    div[data-testid="stForm"], div[data-testid="stVerticalBlockBorderWrapper"] {{
        background: {COLORS['surface']}; border: 1px solid {COLORS['border']};
        border-radius: 18px; box-shadow: 0 10px 28px rgba(39,49,66,.06);
    }}
    .stButton > button, .stDownloadButton > button {{ border-radius: 11px; font-weight: 650; }}
    .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {{
        background: {COLORS['primary']}; border-color: {COLORS['primary']}; color: white;
    }}
    .stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover {{
        background: {COLORS['primary_dark']}; border-color: {COLORS['primary_dark']};
    }}
    div[data-testid="stMetric"] {{ background: white; border: 1px solid {COLORS['border']};
        border-radius: 14px; padding: .9rem 1rem; box-shadow: 0 6px 18px rgba(39,49,66,.04); }}
    .hero {{ background: linear-gradient(135deg,#312E81 0%,#4F46E5 58%,#0F766E 100%);
        color:white; padding:2.2rem 2.4rem; border-radius:24px; box-shadow:0 18px 45px rgba(49,46,129,.22); margin-bottom:1.3rem; }}
    .hero h1 {{ color:white; margin:0 0 .55rem 0; font-size:2.35rem; }}
    .hero p {{ color:#EEF2FF; font-size:1.08rem; max-width:760px; margin:0; }}
    .eyebrow {{ text-transform:uppercase; letter-spacing:.12em; font-size:.76rem; font-weight:750; color:#C7D2FE; margin-bottom:.55rem; }}
    .info-card {{ background:white; border:1px solid {COLORS['border']}; border-radius:18px; padding:1.35rem;
        height:100%; box-shadow:0 8px 24px rgba(39,49,66,.05); }}
    .info-card h3 {{ margin-top:.25rem; }}
    .info-card p {{ color:{COLORS['muted']}; }}
    .step-chip {{ display:inline-block; background:{COLORS['soft_indigo']}; color:{COLORS['primary_dark']};
        padding:.35rem .7rem; border-radius:999px; font-weight:700; font-size:.82rem; margin-bottom:.5rem; }}
    .section-intro {{ color:{COLORS['muted']}; margin-top:-.3rem; margin-bottom:1rem; }}
    .recommend-card {{ background:white; border:1px solid {COLORS['border']}; border-left:6px solid {COLORS['secondary']};
        border-radius:16px; padding:1.15rem 1.25rem; margin:.7rem 0; box-shadow:0 8px 22px rgba(39,49,66,.05); }}
    .recommend-rank {{ display:inline-grid; place-items:center; width:30px; height:30px; border-radius:50%;
        color:white; background:{COLORS['primary']}; font-weight:800; margin-right:.5rem; }}
    .muted {{ color:{COLORS['muted']}; }}
    .process {{ display:flex; gap:.75rem; flex-wrap:wrap; margin:.9rem 0 1.3rem; }}
    .process-item {{ flex:1; min-width:190px; background:white; border:1px solid {COLORS['border']}; border-radius:14px; padding:1rem; }}
    .process-number {{ color:white; background:{COLORS['accent']}; border-radius:50%; width:27px; height:27px;
        display:inline-grid; place-items:center; font-weight:800; margin-right:.4rem; }}
    @media (max-width:700px) {{ .hero {{ padding:1.45rem; }} .hero h1 {{ font-size:1.75rem; }} .block-container {{ padding-top:1rem; }} }}
    </style>
    """, unsafe_allow_html=True)

def hero(eyebrow, title, body):
    st.markdown(f'<div class="hero"><div class="eyebrow">{html.escape(eyebrow)}</div><h1>{html.escape(title)}</h1><p>{html.escape(body)}</p></div>', unsafe_allow_html=True)

def card(icon, title, body):
    st.markdown(f'<div class="info-card"><div style="font-size:1.7rem">{icon}</div><h3>{html.escape(title)}</h3><p>{html.escape(body)}</p></div>', unsafe_allow_html=True)

def process_strip(items):
    blocks = ''.join(f'<div class="process-item"><span class="process-number">{i}</span><strong>{html.escape(t)}</strong><br><span class="muted">{html.escape(b)}</span></div>' for i,(t,b) in enumerate(items,1))
    st.markdown(f'<div class="process">{blocks}</div>', unsafe_allow_html=True)
