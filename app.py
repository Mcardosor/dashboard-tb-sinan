"""
app.py — Tuberculose no Brasil | SINAN NET
──────────────────────────────────────────
Página principal: Hero, KPI cards, sidebar de filtros.
As abas de análise estão em pages/.
"""

import streamlit as st
import pandas as pd

from src.constantes import (
    POP_ESTADO, POP_BRASIL,
    ANO_ATUAL, ANO_INICIO,
    NORMALIZAR_DESFECHO,
    kpi_card_html, _delta_badge,
)
from src.graficos import tb_layout
from src.ui_sidebar import render_sidebar
from src.styles import inject_css  # noqa: E402

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIG & CSS
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Dashboard TB | SINAN",
    page_icon="🩺",
    layout="wide",
)

inject_css()

# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR — FILTROS
# ══════════════════════════════════════════════════════════════════════════════
df, df_completo, anos_sel, ano_sel, total_filt, total_base = render_sidebar()
pct_filt = round(total_filt / total_base * 100, 1) if total_base else 0

# ══════════════════════════════════════════════════════════════════════════════
#  HERO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="hero">
  <h1 class="hero-title">
    <span class="hero-emoji">🩺</span>
    <span>Tuberculose no Brasil</span>
  </h1>
  <p class="hero-subtitle">
    Painel de vigilância epidemiológica baseado em notificações do SINAN —
    perfil dos casos, indicadores clínicos, distribuição geográfica e tendências
    temporais ({ANO_INICIO}–{ANO_ATUAL}).
  </p>
  <div class="hero-badges">
    <span class="hero-badge accent"><span class="dot"></span>{f"Anos {min(anos_sel)}–{max(anos_sel)}" if len(anos_sel) > 1 else f"Ano {anos_sel[0]}"}</span>
    <span class="hero-badge"><span class="dot"></span>SINAN NET · Dicionário v5.0</span>
    <span class="hero-badge success"><span class="dot"></span>{total_filt:,} registros ({pct_filt}% da base)</span>
    <span class="hero-badge"><span class="dot"></span>Série histórica: {ANO_INICIO}–{ANO_ATUAL}</span>
  </div>
</div>
""".replace(",", "."), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  KPIs — cálculo
# ══════════════════════════════════════════════════════════════════════════════
enc_norm = (df["situacao_enc_norm"] if "situacao_enc_norm" in df.columns
            else df.get("situacao_encerramento", pd.Series(dtype=str)).astype(str)
                   .map(lambda x: NORMALIZAR_DESFECHO.get(x, x)))

total      = len(df)
cura       = (enc_norm == "Cura").sum()
obito_tb   = (enc_norm == "Obito por TB").sum()
abandono   = (enc_norm == "Abandono").sum()
hiv_pos    = (df["status_hiv"] == "Positivo").sum() if "status_hiv" in df.columns else 0
municipios = df["municipio_notificacao"].nunique() if "municipio_notificacao" in df.columns else 0

ufs_sel      = df["uf_sigla"].unique() if "uf_sigla" in df.columns else []
pop_filtrada = sum(POP_ESTADO.get(uf, 0) for uf in ufs_sel) or POP_BRASIL
incidencia   = round(total    / pop_filtrada * 100_000, 1)
mortalidade  = round(obito_tb / pop_filtrada * 100_000, 1)

if "metric_mapa" not in st.session_state:
    st.session_state.metric_mapa = "casos"
if "selected_uf" not in st.session_state:
    st.session_state.selected_uf = None
if "mapa_key_counter" not in st.session_state:
    st.session_state.mapa_key_counter = 0

# ── KPI cards — ordem Raquel: incid | mort | óbitos | HIV / cura | abandono | total | municípios
_cards = [
    # Linha 1: indicadores de magnitude e mortalidade
    ("incidencia",  "Incidência por 100 mil hab.",
     f"{incidencia:.1f}".replace(".", ","),   None, None, False, "📈", "#58a6ff", "incidencia"),
    ("mortalidade", "Mortalidade por 100 mil hab.",
     f"{mortalidade:.1f}".replace(".", ","),  None, None, False, "💀", "#f85149", "mortalidade"),
    ("obito",       "Óbitos por TB",
     f"{obito_tb:,}".replace(",", "."),       None, None, False, "⚠️", "#ffd700", None),
    ("hiv",         "Coinfecção HIV",
     f"{hiv_pos:,}".replace(",", "."),        None, None, False, "🔬", "#d2a8ff", None),
    # Linha 2: desfechos + total
    ("cura",        "Curas registradas",
     f"{cura:,}".replace(",", "."),           None, None, True,  "✅", "#7ee787", None),
    ("abandono",    "Abandonos",
     f"{abandono:,}".replace(",", "."),       None, None, False, "🚪", "#8b949e", None),
    ("total",       "Total de casos",
     f"{total:,}".replace(",", "."),          None, None, False, "🦠", "#ffa657", "casos"),
    ("municipios",  "Municípios prioritários",
     f"{municipios:,}".replace(",", "."),     None, None, False, "🏙️", "#79c0ff", None),
]

for row_cards in [_cards[:4], _cards[4:]]:
    cols = st.columns(4)
    for col, (key, title, valor, prev, cur, bom_subir, icon, accent, mapa_key) in zip(cols, row_cards):
        with col:
            sel   = (st.session_state.metric_mapa == mapa_key) if mapa_key else False
            delta = _delta_badge(cur, prev, good_when_up=bom_subir) if prev is not None else ""
            st.markdown(kpi_card_html(title, valor, delta, icon, accent, sel),
                        unsafe_allow_html=True)
            if mapa_key:
                lbl = "🗺️ No mapa ✓" if sel else "🗺️ Ver no mapa"
                if st.button(lbl, key=f"kpibtn_{key}",
                             type="primary" if sel else "secondary",
                             use_container_width=True):
                    st.session_state.metric_mapa = mapa_key
                    st.rerun()

st.divider()

# ── Salva contexto no session_state para as pages lerem ──────────────────────
st.session_state["df"] = df
st.session_state["ctx"] = {
    "anos_sel":   anos_sel,
    "ano_sel":    ano_sel,
    "total_filt": total_filt,
    "total_base": total_base,
    "enc_norm":   enc_norm,
}

# ══════════════════════════════════════════════════════════════════════════════
#  NAVEGAÇÃO — as abas foram movidas para pages/
# ══════════════════════════════════════════════════════════════════════════════
