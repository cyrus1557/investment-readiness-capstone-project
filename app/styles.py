"""Shared look of the app: colours, page styling and small reusable pieces (banner, cards, badges, notes)."""
import base64
import html
from pathlib import Path

import streamlit as st

# Predictive Minds colours (Option 2: navy and gold, with the logo's charcoal blue text)
COLORS = {
    "primary_dark": "#0B2545",  # sidebar, headings, banner (navy)
    "primary": "#1D4E89",       # main buttons, High band (strong blue)
    "primary_soft": "#E6EEF7",
    "gold": "#D4A017",          # accents, Medium band
    "gold_soft": "#FBF3D9",
    "background": "#F7F5F0",    # warm off-white page
    "card": "#FFFFFF",          # white cards
    "text": "#0A1F3C",          # charcoal blue body text
    "muted": "#5B6472",
    "border": "#E4E2DA",
    "low": "#94A3B8",           # Low band
    "danger": "#B42318",
}
BAND_COLORS = {"High": COLORS["primary"], "Medium": COLORS["gold"], "Low": COLORS["low"]}
BAND_SOFT = {"High": COLORS["primary_soft"], "Medium": COLORS["gold_soft"], "Low": "#EEF1F5"}


def apply_styles():
    # Page-wide styling, added once in app.py so every page gets it
    c = COLORS
    st.markdown(f"""
    <style>
    .stApp {{ background: {c['background']}; color: {c['text']}; }}
    .block-container {{ padding-top: 4.2rem; padding-bottom: 3rem; max-width: 1200px; }}
    h1, h2, h3 {{ color: {c['primary_dark']}; letter-spacing: -0.02em; }}

    [data-testid="stSidebar"] {{ background: {c['primary_dark']}; }}
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] li,
    [data-testid="stSidebar"] a, [data-testid="stSidebar"] label {{ color: #F8FAF9; }}
    [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {{ background: rgba(255,255,255,.08); }}

    div[data-testid="stForm"] {{ background: {c['card']}; border: 1px solid {c['border']};
        border-radius: 16px; padding: 1.2rem 1.3rem; }}
    div[data-testid="stMetric"] {{ background: {c['card']}; border: 1px solid {c['border']};
        border-radius: 14px; padding: .8rem 1rem; }}
    div[data-testid="stMetricValue"] {{ color: {c['primary_dark']}; }}
    .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{
        border-radius: 10px; font-weight: 600; }}

    .hero {{ background: {c['primary_dark']}; border-bottom: 4px solid {c['gold']}; color: white;
        padding: 1.8rem 2rem; border-radius: 18px; margin-bottom: 1.2rem; }}
    .hero-row {{ display: flex; align-items: center; gap: 1.6rem; flex-wrap: wrap; }}
    .hero-logo {{ height: 92px; width: auto; }}
    .hero-text {{ flex: 1; min-width: 260px; }}
    .hero h1 {{ color: white; margin: 0 0 .4rem 0; font-size: 2.1rem; }}
    .hero p {{ color: #E6EEF7; font-size: 1.05rem; max-width: 780px; margin: 0; }}
    .eyebrow {{ text-transform: uppercase; letter-spacing: .07em; font-size: 1.05rem; font-weight: 800;
        line-height: 1.3; color: {c['gold']}; margin-bottom: .5rem; }}

    .pm-card {{ background: {c['card']}; border: 1px solid {c['border']}; border-radius: 16px;
        padding: 1.2rem 1.3rem; height: 100%; }}
    .pm-card.journey {{ min-height: 215px; }}
    .pm-card h3 {{ margin: .2rem 0 .4rem 0; font-size: 1.15rem; }}
    .glossary-card {{ background: {c['card']}; border: 1px solid {c['border']}; border-radius: 14px;
        padding: 1rem 1.2rem; margin-bottom: .8rem; }}
    .glossary-card h4 {{ margin: 0 0 .3rem 0; color: {c['primary_dark']}; }}
    .glossary-card p {{ margin: .2rem 0; }}
    .pm-card p {{ color: {c['muted']}; margin: 0; }}
    .pm-icon {{ display: inline-grid; place-items: center; width: 38px; height: 38px; border-radius: 10px;
        background: {c['gold_soft']}; font-size: 1.2rem; }}

    .process {{ display: flex; gap: .7rem; flex-wrap: wrap; margin: .6rem 0 1.2rem; }}
    .process-item {{ flex: 1; min-width: 180px; background: {c['card']}; border: 1px solid {c['border']};
        border-radius: 14px; padding: .9rem 1rem; }}
    .process-number {{ color: {c['primary_dark']}; background: {c['gold']}; border-radius: 50%; width: 26px;
        height: 26px; display: inline-grid; place-items: center; font-weight: 800; margin-right: .4rem; }}
    .muted {{ color: {c['muted']}; }}

    .step-chip {{ display: inline-block; background: {c['primary_soft']}; color: {c['primary_dark']};
        padding: .3rem .75rem; border-radius: 999px; font-weight: 700; font-size: .82rem; margin-bottom: .4rem; }}
    .section-intro {{ color: {c['muted']}; margin-top: -.2rem; margin-bottom: .9rem; }}
    .field-error {{ color: {c['danger']}; font-size: .86rem; margin: -.5rem 0 .6rem 0; }}

    .recommend-card {{ background: {c['card']}; border: 1px solid {c['border']}; border-left: 6px solid {c['primary']};
        border-radius: 0 14px 14px 0; padding: 1rem 1.2rem; margin: .6rem 0; }}
    .recommend-card p {{ margin: .35rem 0 0 0; }}
    .recommend-rank {{ display: inline-grid; place-items: center; width: 28px; height: 28px; border-radius: 50%;
        color: {c['primary_dark']}; background: {c['gold']}; font-weight: 800; margin-right: .5rem; }}
    .tag {{ display: inline-block; font-size: .75rem; font-weight: 700; padding: .15rem .55rem;
        border-radius: 999px; margin-left: .4rem; background: {c['primary_soft']}; color: {c['primary_dark']}; }}
    .tag-gold {{ background: {c['gold_soft']}; color: #6B4E00; }}

    .band {{ display: inline-block; font-weight: 800; padding: .2rem .7rem; border-radius: 999px; }}
    .note {{ border-radius: 0 12px 12px 0; padding: .85rem 1.1rem; margin: .6rem 0 1rem 0; }}
    .note-warn {{ background: {c['gold_soft']}; border-left: 5px solid {c['gold']}; }}
    .note-info {{ background: {c['primary_soft']}; border-left: 5px solid {c['primary']}; }}
    .note strong {{ color: {c['text']}; }}

    .sidebar-card {{ background: rgba(255,255,255,.07); border: 1px solid rgba(255,255,255,.14);
        border-radius: 12px; padding: .8rem .9rem; font-size: .84rem; line-height: 1.5; margin-top: .6rem; }}
    .sidebar-card b {{ color: {c['gold']}; }}
    .sidebar-label {{ text-transform: uppercase; letter-spacing: .1em; font-size: .7rem; font-weight: 700;
        color: #A9BCD6 !important; margin: .9rem 0 .2rem 0; }}
    [data-testid="stSidebar"] .stButton > button {{ background: rgba(255,255,255,.08); color: #F8FAF9;
        border: 1px solid rgba(255,255,255,.22); justify-content: flex-start; font-weight: 500; }}
    [data-testid="stSidebar"] .stButton > button > div,
    [data-testid="stSidebar"] .stButton > button [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] .stButton > button p {{ justify-content: flex-start; text-align: left; width: 100%; }}
    [data-testid="stSidebar"] .stButton > button:hover {{ border-color: {c['gold']}; color: {c['gold']}; }}
    .sidebar-links a {{ display: block; color: #F8FAF9 !important; text-decoration: none; font-size: .86rem;
        padding: .22rem 0; }}
    .sidebar-links a:hover {{ color: {c['gold']} !important; }}

    div[class*="st-key-switch_"] {{ background: {c['card']}; border: 1px solid {c['border']}; border-radius: 14px;
        padding: .45rem .5rem; margin: .4rem 0 1rem 0; }}
    div[class*="st-key-switch_"] button {{ min-height: 3.1rem; font-size: 1rem; border-radius: 10px; }}
    div[class*="st-key-switch_"] button[kind="secondary"] {{ background: transparent; border-color: transparent; }}
    div[class*="st-key-switch_"] button[kind="secondary"]:hover {{ background: {c['primary_soft']}; }}

    /* "Ask a question": floats above Streamlit's own badge in the bottom-right corner */
    .st-key-ask_fab {{ position: fixed; right: 1.1rem; bottom: 4.6rem; z-index: 1000;
        width: auto !important; min-width: 0 !important; }}
    .st-key-ask_fab .stButton > button {{ background: {c['gold']}; color: {c['primary_dark']}; border: none;
        border-radius: 999px; padding: .55rem 1.15rem; font-weight: 700;
        box-shadow: 0 6px 18px rgba(11,37,69,.28); }}
    .st-key-ask_fab .stButton > button:hover {{ background: #E8B22A; color: {c['primary_dark']}; }}

    /* The chat panel it turns into: held in the same corner, just above Streamlit's badge */
    .st-key-ask_panel {{ position: fixed; right: 1.1rem; bottom: 4.6rem; z-index: 1001;
        width: 400px !important; max-width: 94vw !important; max-height: 74vh; overflow-y: auto;
        background: {c['card']}; border: 1px solid {c['border']}; border-radius: 16px;
        box-shadow: 0 14px 40px rgba(11,37,69,.28); padding: .9rem 1rem 1rem 1rem !important; }}
    .st-key-ask_panel h4 {{ margin: 0; color: {c['primary_dark']}; font-size: 1.05rem; }}
    .st-key-ask_panel .stButton > button {{ border-radius: 10px; }}
    .st-key-ask_close > button {{ padding: .1rem .5rem; }}

    @media (max-width: 700px) {{
        .hero {{ padding: 1.3rem; }} .hero h1 {{ font-size: 1.6rem; }} .block-container {{ padding-top: 1rem; }}
        .eyebrow {{ font-size: .92rem; }}
        /* The sidebar covered the whole phone screen, so keep it to about two thirds */
        [data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child {{
            width: 62vw !important; min-width: 62vw !important; max-width: 62vw !important; }}
        .st-key-ask_fab {{ right: .7rem; bottom: 4.2rem; }}
        .st-key-ask_panel {{ right: .5rem; left: .5rem; width: auto !important; bottom: 4.2rem;
            max-height: 78vh; }}
        .st-key-ask_fab .stButton > button {{ padding: .5rem .95rem; font-size: .9rem; }}
    }}
    </style>
    """, unsafe_allow_html=True)


def _e(text):
    # Make text safe to place inside HTML
    return html.escape(str(text))


def _image_data(path):
    # A local image as text that can sit inside HTML (so the logo can go inside the banner)
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
    # kind: "warn" (gold) or "info" (blue)
    st.markdown(f'<div class="note note-{kind}"><strong>{_e(title)}</strong><br>{_e(body)}</div>',
                unsafe_allow_html=True)


def band_badge(band):
    return (f'<span class="band" style="background:{BAND_SOFT[band]};color:{COLORS["text"]};'
            f'border:1.5px solid {BAND_COLORS[band]}">{_e(band)}</span>')


def recommend_card(rank, title, sentence, tag=None, gold_tag=False):
    tag_html = f'<span class="tag{" tag-gold" if gold_tag else ""}">{_e(tag)}</span>' if tag else ""
    st.markdown(f'<div class="recommend-card"><span class="recommend-rank">{rank}</span><strong>{_e(title)}</strong>'
                f'{tag_html}<p>{_e(sentence)}</p></div>', unsafe_allow_html=True)


def _set_view(key, label):
    st.session_state[key] = label


def view_switcher(views, key):
    """
    A full-width row of equal buttons that switches between views (like tabs, but it stays on the
    chosen view when other buttons on the page are clicked). Returns the chosen view.
    """
    if st.session_state.get(key) not in views:
        st.session_state[key] = views[0]
    with st.container(key=f"switch_{key}"):
        for col, label in zip(st.columns(len(views), gap="small"), views):
            col.button(label, key=f"{key}__{label}", use_container_width=True, on_click=_set_view, args=(key, label),
                       type="primary" if st.session_state[key] == label else "secondary")
    return st.session_state[key]
