"""
styles.py
─────────
CSS global do dashboard TB SINAN.
Injetar com: st.markdown(get_css(), unsafe_allow_html=True)
"""

import streamlit as st

_CSS = """
<style>
  [data-testid="stAppViewContainer"] { background-color: #0e1117; }
  [data-testid="stSidebar"]          { background-color: #161b22; }
  [data-testid="stSidebar"] *        { color: #e6edf3 !important; }
  h1, h2, h3                         { color: #f0f6fc; }
  p, span, label                     { color: #c9d1d9; }
  [data-testid="stCaption"]          { color: #8b949e; }
  hr                                 { border-color: #30363d; }
  .leaflet-control-attribution        { display: none !important; }

  /* ── KPI Cards ───────────────────────────────────────── */
  .kpi-card {
    --accent: #58a6ff;
    border-radius: 14px;
    border: 1px solid #30363d;
    background: linear-gradient(160deg, #1c2128 0%, #161b22 100%);
    box-shadow: 0 4px 16px rgba(0,0,0,.35);
    overflow: hidden;
    position: relative;
    transition: transform .12s ease, box-shadow .12s ease, border-color .12s ease;
    margin-bottom: 4px;
  }
  .kpi-card.kpi-selected {
    border: 1.5px solid var(--accent);
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 25%, transparent),
                0 8px 28px rgba(0,0,0,.45);
    background: linear-gradient(160deg,
        color-mix(in srgb, var(--accent) 10%, #1c2128) 0%, #161b22 100%);
  }
  .kpi-inner {
    display: flex; align-items: center; gap: 11px;
    padding: 13px 13px; position: relative; z-index:1;
  }
  .kpi-bar {
    width: 4px; height: 46px; border-radius: 999px;
    background: var(--accent); flex: 0 0 auto;
  }
  .kpi-body { flex: 1; min-width: 0; }
  .kpi-label {
    font-size: 10px; font-weight: 700; color: #8b949e;
    text-transform: uppercase; letter-spacing: .6px;
    margin-bottom: 2px; white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis;
  }
  .kpi-value {
    font-size: 22px; font-weight: 900; color: #f0f6fc;
    letter-spacing: -.4px; line-height: 1.1;
  }
  .kpi-delta        { display:block; font-size: 11px; font-weight: 700; margin-top: 3px; }
  .kpi-delta.good   { color: #7ee787; }
  .kpi-delta.bad    { color: #f85149; }
  .kpi-delta.flat   { color: #8b949e; }
  .kpi-icon {
    width: 34px; height: 34px; border-radius: 999px;
    background: rgba(255,255,255,.05);
    border: 1px solid rgba(255,255,255,.08);
    display: flex; align-items: center;
    justify-content: center; flex: 0 0 auto;
    font-size: 15px;
  }

  /* ── Hero ────────────────────────────────────────────── */
  .hero {
    position: relative; padding: 28px 32px 24px 32px;
    margin: -10px 0 22px 0; border-radius: 18px;
    background: linear-gradient(135deg,
        rgba(248, 129, 102, .12) 0%,
        rgba(88, 166, 255, .08) 45%,
        rgba(22, 27, 34, 0) 100%),
        linear-gradient(180deg, #161b22 0%, #0e1117 100%);
    border: 1px solid #30363d;
    box-shadow: 0 4px 24px rgba(0,0,0,.35); overflow: hidden;
  }
  .hero::before {
    content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #f78166 0%, #58a6ff 50%, #7ee787 100%);
  }
  .hero-title {
    font-size: 32px; font-weight: 900; color: #f0f6fc;
    letter-spacing: -.8px; line-height: 1.15; margin: 0 0 6px 0;
    display: flex; align-items: center; gap: 12px;
  }
  .hero-emoji { font-size: 36px; filter: drop-shadow(0 2px 8px rgba(247,129,102,.35)); }
  .hero-subtitle {
    font-size: 14px; color: #8b949e; margin: 0 0 16px 0;
    font-weight: 500; max-width: 720px; line-height: 1.5;
  }
  .hero-badges { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px; }
  .hero-badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 11px; border-radius: 999px; font-size: 11px;
    font-weight: 700; letter-spacing: .3px;
    background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.08);
    color: #c9d1d9; text-transform: uppercase;
  }
  .hero-badge.accent  { background: rgba(88,166,255,.12); border-color: rgba(88,166,255,.35); color: #79c0ff; }
  .hero-badge.success { background: rgba(126,231,135,.10); border-color: rgba(126,231,135,.30); color: #7ee787; }
  .hero-badge .dot    { width: 6px; height: 6px; border-radius: 50%; background: currentColor; opacity: .8; }

  /* ── Layout ──────────────────────────────────────────── */
  .block-container { padding-top: 2rem !important; padding-bottom: 3rem !important; max-width: 1400px; }
  hr, [data-testid="stDivider"] {
    margin: 2rem 0 1.5rem 0 !important; border: none !important; height: 1px !important;
    background: linear-gradient(90deg, transparent 0%, #30363d 20%, #30363d 80%, transparent 100%) !important;
  }
  h2 { font-size: 20px !important; font-weight: 700 !important; color: #f0f6fc !important;
       margin-top: .25rem !important; margin-bottom: 1rem !important; padding-bottom: .5rem !important; letter-spacing: -.3px !important; }
  h3 { font-size: 16px !important; font-weight: 600 !important; color: #e6edf3 !important;
       margin-top: .5rem !important; margin-bottom: .75rem !important; letter-spacing: -.2px !important; }

  /* ── Tabs ────────────────────────────────────────────── */
  .stTabs { margin-top: 1rem; }
  .stTabs [data-baseweb="tab-list"] {
    gap: 4px; background: rgba(22,27,34,.5); padding: 6px;
    border-radius: 12px; border: 1px solid #30363d;
    flex-wrap: wrap !important;
    overflow-x: auto;
  }
  .stTabs [data-baseweb="tab"] {
    padding: 8px 14px !important; border-radius: 8px !important;
    font-weight: 600 !important; font-size: 13px !important;
    color: #8b949e;
    white-space: nowrap;
    flex: 1 1 auto !important;
    text-align: center !important;
    cursor: pointer !important;
    border: 1px solid transparent !important;
    transition: background .15s ease, border-color .15s ease,
                color .15s ease, transform .1s ease !important;
  }
  .stTabs [data-baseweb="tab"]:hover {
    background: rgba(255,255,255,.07) !important;
    border-color: #30363d !important;
    color: #c9d1d9 !important;
    transform: translateY(-1px);
  }
  .stTabs [aria-selected="true"] {
    background: rgba(247,129,102,.15) !important;
    border-color: rgba(247,129,102,.35) !important;
    color: #f0f6fc !important;
    border-bottom-color: transparent !important;
    box-shadow: 0 2px 8px rgba(247,129,102,.15) !important;
  }
  .stTabs [data-baseweb="tab-panel"] { padding-top: 1.25rem; }

  /* ── Expanders ────────────────────────────────────────── */
  [data-testid="stExpander"] {
    border: 1px solid #30363d !important; border-radius: 12px !important;
    background: #161b22 !important; margin-top: 1rem;
  }
  [data-testid="stSidebar"] [data-testid="stExpander"] {
    background: transparent !important; border: 1px solid #30363d !important; margin-bottom: .5rem;
  }

  /* ── Folium ──────────────────────────────────────────── */
  iframe[title="streamlit_folium.st_folium"] {
    border-radius: 12px; border: 1px solid #30363d; overflow: hidden;
  }

  /* ── Responsividade — Tablet (≤1024px) ──────────────────── */
  @media (max-width: 1024px) {
    .hero-title    { font-size: 26px !important; }
    .hero-subtitle { font-size: 13px; }
    .block-container {
      padding-left: 1rem !important;
      padding-right: 1rem !important;
    }
  }

  /* ── Responsividade — Mobile (≤768px) ───────────────────── */
  @media (max-width: 768px) {
    .hero          { padding: 18px 16px 16px 16px !important; }
    .hero-title    { font-size: 20px !important; }
    .hero-emoji    { font-size: 24px !important; }
    .hero-subtitle { font-size: 12px; margin-bottom: 10px; }
    .hero-badge    { font-size: 10px !important; padding: 3px 8px !important; }

    [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
    [data-testid="column"] {
      min-width: calc(50% - 0.5rem) !important;
      flex: 0 0 calc(50% - 0.5rem) !important;
    }
    .kpi-value { font-size: 18px !important; }
    .kpi-label { font-size: 9px !important; }
    .kpi-icon  { width: 28px !important; height: 28px !important; font-size: 13px !important; }

    .stTabs [data-baseweb="tab-list"] {
      gap: 2px !important; padding: 4px !important;
      flex-wrap: wrap !important; overflow-x: auto !important;
    }
    .stTabs [data-baseweb="tab"] {
      font-size: 11px !important; padding: 6px 8px !important;
      flex: 1 1 auto !important; text-align: center !important;
    }
    .block-container {
      padding-left: 0.5rem !important;
      padding-right: 0.5rem !important;
    }
  }

  /* ── Responsividade — Mobile pequeno (≤480px) ────────────── */
  @media (max-width: 480px) {
    [data-testid="column"] {
      min-width: 100% !important;
      flex: 0 0 100% !important;
    }
    .hero-title  { font-size: 17px !important; }
    .hero-badges { flex-wrap: wrap; gap: 4px; }
    .hero-badge  { font-size: 9px !important; }
    .stTabs [data-baseweb="tab"] {
      font-size: 10px !important;
      padding: 5px 6px !important;
    }
  }
</style>
"""

# CSS minimalista para páginas secundárias (sem KPI cards e hero)
_CSS_PAGE = """
<style>
  [data-testid="stAppViewContainer"] { background-color: #0e1117; }
  [data-testid="stSidebar"]          { background-color: #161b22; }
  [data-testid="stSidebar"] *        { color: #e6edf3 !important; }
  h1, h2, h3                         { color: #f0f6fc; }
  p, span, label                     { color: #c9d1d9; }
  [data-testid="stCaption"]          { color: #8b949e; }
  .block-container { padding-top: 2rem !important; max-width: 1400px; }
</style>
"""


def inject_css() -> None:
    """Injeta o CSS completo do dashboard (usar no app.py principal)."""
    st.markdown(_CSS, unsafe_allow_html=True)


def inject_css_page() -> None:
    """Injeta CSS minimalista para páginas secundárias (usar em pages/)."""
    st.markdown(_CSS_PAGE, unsafe_allow_html=True)
