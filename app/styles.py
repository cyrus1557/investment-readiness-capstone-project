"""Shared look of the app: colours, page styling and small reusable pieces (banner, cards, badges, notes)."""
import base64
import html
from pathlib import Path

import streamlit as st

# Predictive Minds colours (Option A: Shamba green and gold, plus the logo's soft white and charcoal blue)
COLORS = {
    "green_dark": "#14532D",   # sidebar, headings, banner
    "green": "#15803D",        # main buttons, High band
    "gold": "#D4A017",         # accents, Medium band
    "gold_soft": "#FBF3D9",
    "green_soft": "#E7F3EA",
    "background": "#FAF7F0",   # cream page
    "card": "#F8FAF9",         # soft white cards
    "text": "#0A1F3C",         # charcoal blue body text
    "muted": "#5B6472",
    "border": "#E4E2DA",
    "low": "#94A3B8",          # Low band
    "danger": "#B42318",
}
BAND_COLORS = {"High": COLORS["green"], "Medium": COLORS["gold"], "Low": COLORS["low"]}
BAND_SOFT = {"High": COLORS["green_soft"], "Medium": COLORS["gold_soft"], "Low": "#EEF1F5"}


def apply_styles():
    # Page-wide styling, added once in app.py so every page gets it
    c = COLORS
    st.markdown(f"""
    <style>
    .stApp {{ background: {c['background']}; color: {c['text']}; }}
    .block-container {{ padding-top: 4.2rem; padding-bottom: 3rem; max-width: 1200px; }}
    h1, h2, h3 {{ color: {c['green_dark']}; letter-spacing: -0.02em; }}

    [data-testid="stSidebar"] {{ background: {c['green_dark']}; }}
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] li,
    [data-testid="stSidebar"] a, [data-testid="stSidebar"] label {{ color: #F8FAF9; }}
    [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {{ background: rgba(255,255,255,.08); }}

    div[data-testid="stForm"] {{ background: {c['card']}; border: 1px solid {c['border']};
        border-radius: 16px; padding: 1.2rem 1.3rem; }}
    div[data-testid="stMetric"] {{ background: {c['card']}; border: 1px solid {c['border']};
        border-radius: 14px; padding: .8rem 1rem; }}
    div[data-testid="stMetricValue"] {{ color: {c['green_dark']}; }}
    .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{
        border-radius: 10px; font-weight: 600; }}

    .hero {{ background: {c['green_dark']}; border-bottom: 4px solid {c['gold']}; color: white;
        padding: 1.8rem 2rem; border-radius: 18px; margin-bottom: 1.2rem; }}
    .hero-row {{ display: flex; align-items: center; gap: 1.6rem; flex-wrap: wrap; }}
    .hero-logo {{ height: 92px; width: auto; }}
    .hero-text {{ flex: 1; min-width: 260px; }}
    .hero h1 {{ color: white; margin: 0 0 .4rem 0; font-size: 2.1rem; }}
    .hero p {{ color: #E7F3EA; font-size: 1.05rem; max-width: 780px; margin: 0; }}
    .eyebrow {{ text-transform: uppercase; letter-spacing: .12em; font-size: .75rem; font-weight: 700;
        color: {c['gold']}; margin-bottom: .45rem; }}

    .pm-card {{ background: {c['card']}; border: 1px solid {c['border']}; border-radius: 16px;
        padding: 1.2rem 1.3rem; height: 100%; }}
    .pm-card.journey {{ min-height: 215px; }}
    .pm-card h3 {{ margin: .2rem 0 .4rem 0; font-size: 1.15rem; }}
    .glossary-card {{ background: {c['card']}; border: 1px solid {c['border']}; border-radius: 14px;
        padding: 1rem 1.2rem; margin-bottom: .8rem; }}
    .glossary-card h4 {{ margin: 0 0 .3rem 0; color: {c['green_dark']}; }}
    .glossary-card p {{ margin: .2rem 0; }}
    .pm-card p {{ color: {c['muted']}; margin: 0; }}
    .pm-icon {{ display: inline-grid; place-items: center; width: 38px; height: 38px; border-radius: 10px;
        background: {c['gold_soft']}; font-size: 1.2rem; }}

    .process {{ display: flex; gap: .7rem; flex-wrap: wrap; margin: .6rem 0 1.2rem; }}
    .process-item {{ flex: 1; min-width: 180px; background: {c['card']}; border: 1px solid {c['border']};
        border-radius: 14px; padding: .9rem 1rem; }}
    .process-number {{ color: {c['green_dark']}; background: {c['gold']}; border-radius: 50%; width: 26px;
        height: 26px; display: inline-grid; place-items: center; font-weight: 800; margin-right: .4rem; }}
    .muted {{ color: {c['muted']}; }}

    .step-chip {{ display: inline-block; background: {c['green_soft']}; color: {c['green_dark']};
        padding: .3rem .75rem; border-radius: 999px; font-weight: 700; font-size: .82rem; margin-bottom: .4rem; }}
    .section-intro {{ color: {c['muted']}; margin-top: -.2rem; margin-bottom: .9rem; }}
    .field-error {{ color: {c['danger']}; font-size: .86rem; margin: -.5rem 0 .6rem 0; }}

    .recommend-card {{ background: {c['card']}; border: 1px solid {c['border']}; border-left: 6px solid {c['green']};
        border-radius: 0 14px 14px 0; padding: 1rem 1.2rem; margin: .6rem 0; }}
    .recommend-card p {{ margin: .35rem 0 0 0; }}
    .recommend-rank {{ display: inline-grid; place-items: center; width: 28px; height: 28px; border-radius: 50%;
        color: {c['green_dark']}; background: {c['gold']}; font-weight: 800; margin-right: .5rem; }}
    .tag {{ display: inline-block; font-size: .75rem; font-weight: 700; padding: .15rem .55rem;
        border-radius: 999px; margin-left: .4rem; background: {c['green_soft']}; color: {c['green_dark']}; }}
    .tag-gold {{ background: {c['gold_soft']}; color: #6B4E00; }}

    .band {{ display: inline-block; font-weight: 800; padding: .2rem .7rem; border-radius: 999px; }}
    .note {{ border-radius: 0 12px 12px 0; padding: .85rem 1.1rem; margin: .6rem 0 1rem 0; }}
    .note-warn {{ background: {c['gold_soft']}; border-left: 5px solid {c['gold']}; }}
    .note-info {{ background: {c['green_soft']}; border-left: 5px solid {c['green']}; }}
    .note strong {{ color: {c['text']}; }}

    .sidebar-card {{ background: rgba(255,255,255,.07); border: 1px solid rgba(255,255,255,.14);
        border-radius: 12px; padding: .8rem .9rem; font-size: .84rem; line-height: 1.5; margin-top: .6rem; }}
    .sidebar-card b {{ color: {c['gold']}; }}
    .sidebar-label {{ text-transform: uppercase; letter-spacing: .1em; font-size: .7rem; font-weight: 700;
        color: #B9D3C0 !important; margin: .9rem 0 .2rem 0; }}
    [data-testid="stSidebar"] .stButton > button {{ background: rgba(255,255,255,.08); color: #F8FAF9;
        border: 1px solid rgba(255,255,255,.22); justify-content: flex-start; font-weight: 500; }}
    [data-testid="stSidebar"] .stButton > button:hover {{ border-color: {c['gold']}; color: {c['gold']}; }}
    .sidebar-links a {{ display: block; color: #F8FAF9 !important; text-decoration: none; font-size: .86rem;
        padding: .22rem 0; }}
    .sidebar-links a:hover {{ color: {c['gold']} !important; }}

    @media (max-width: 700px) {{
        .hero {{ padding: 1.3rem; }} .hero h1 {{ font-size: 1.6rem; }} .block-container {{ padding-top: 1rem; }}
    }}
    </style>
    """, unsafe_allow_html=True)


def _e(text):
    # Make text safe to place inside HTML
    return html.escape(str(text))


def _image_data(path):
    # A local image as text that can sit inside HTML (so the logo can go inside the green banner)
    try:
        return "data:image/png;base64," + base64.b64encode(Path(path).read_bytes()).decode()
    except OSError:
        return None


def hero(eyebrow, title, body, logo=None):
    logo_src = _image_data(logo) if logo else None
    logo_html = f'<img class="hero-logo" src="{logo_src}" alt="Predictive Minds logo">' if logo_src else ""
    st.markdown(f'<div class="hero"><div class="hero-row">{logo_html}<div class="hero-text">'
                f'<div class="eyebrow">{_e(eyebrow)}</div><h1>{_e(title)}</h1><p>{_e(body)}</p>'
                f'</div></div></div>', unsafe_allow_html=True)


def card(icon, title, body, journey=False):
    st.markdown(f'<div class="pm-card{" journey" if journey else ""}"><span class="pm-icon">{icon}</span>'
                f'<h3>{_e(title)}</h3><p>{_e(body)}</p></div>', unsafe_allow_html=True)


def glossary_card(title, lines):
    # lines: list of (label, text); label may be "" for a plain sentence
    body = "".join(f'<p><strong>{_e(label)}:</strong> {_e(text)}</p>' if label else f'<p>{_e(text)}</p>'
                   for label, text in lines)
    st.markdown(f'<div class="glossary-card"><h4>{_e(title)}</h4>{body}</div>', unsafe_allow_html=True)


def process_strip(items):
    blocks = "".join(f'<div class="process-item"><span class="process-number">{i}</span><strong>{_e(t)}</strong>'
                     f'<br><span class="muted">{_e(b)}</span></div>' for i, (t, b) in enumerate(items, 1))
    st.markdown(f'<div class="process">{blocks}</div>', unsafe_allow_html=True)


def step_header(label, intro):
    st.markdown(f'<span class="step-chip">{_e(label)}</span><p class="section-intro">{_e(intro)}</p>',
                unsafe_allow_html=True)


def field_error(message):
    # Small red message shown right under the box that needs fixing
    st.markdown(f'<div class="field-error">⚠ {_e(message)}</div>', unsafe_allow_html=True)


def note(kind, title, body):
    # kind: "warn" (gold) or "info" (green)
    st.markdown(f'<div class="note note-{kind}"><strong>{_e(title)}</strong><br>{_e(body)}</div>',
                unsafe_allow_html=True)


def band_badge(band):
    return (f'<span class="band" style="background:{BAND_SOFT[band]};color:{COLORS["text"]};'
            f'border:1.5px solid {BAND_COLORS[band]}">{_e(band)}</span>')


def recommend_card(rank, title, sentence, tag=None, gold_tag=False):
    tag_html = f'<span class="tag{" tag-gold" if gold_tag else ""}">{_e(tag)}</span>' if tag else ""
    st.markdown(f'<div class="recommend-card"><span class="recommend-rank">{rank}</span><strong>{_e(title)}</strong>'
                f'{tag_html}<p>{_e(sentence)}</p></div>', unsafe_allow_html=True)
