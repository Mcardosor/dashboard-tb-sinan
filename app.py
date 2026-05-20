"""
app.py — Tuberculose no Brasil | SINAN NET
──────────────────────────────────────────
Dashboard completo: dark theme, hero, 8 KPI cards, 6 abas, Folium.
Revisão Raquel: 100 mil, reorder KPIs, pirâmide óbitos, desfecho HIV, indicadores.
"""

import copy
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_OK = True
except ImportError:
    FOLIUM_OK = False

from src.constantes import (
    SPEC_PATH, COLUNAS_ANALISE, PLOTLY_CFG, POP_ESTADO, POP_BRASIL,
    UF_SIGLAS, TB_SEQ_INCIDENCIA, TB_SEQ_MORTAL,
    anos_disponiveis, parquet_path,
    ANO_ATUAL, ANO_INICIO, HIST_INDICADORES,
    NORMALIZAR_DESFECHO, AGRAVOS, POPULACOES,
    H_SMALL, H_MEDIUM, H_LARGE,
    grafico_vazio, kpi_card_html, _delta_badge, pct,
    tb_layout, tb_color_map,
)
from src.dados import (
    carregar_dados, carregar_geojson,
    selecionar_colunas, gerar_html_pygwalker,
    enriquecer_df, load_historico,
)
from src import graficos
from src import mapa_interativo

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIG & CSS
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Dashboard TB | SINAN",
    page_icon="🫁",
    layout="wide",
)

st.markdown("""
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
    flex: 1 1 auto !important;     /* preenche a linha inteira */
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
      gap: 2px !important;
      padding: 4px !important;
      flex-wrap: wrap !important;
      overflow-x: auto !important;
    }
    .stTabs [data-baseweb="tab"] {
      font-size: 11px !important;
      padding: 6px 8px !important;
      flex: 1 1 auto !important;
      text-align: center !important;
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
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR — FILTROS
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🫁 TB · SINAN")

    anos = anos_disponiveis()
    ano_sel = st.selectbox("📅 Ano de notificação", options=anos, index=0)
    path_sel = parquet_path(ano_sel)
    if not path_sel.exists():
        st.error(
            f"Dados de {ano_sel} não encontrados.\n\n"
            f"Execute:\n```\npython scripts/conectar_banco.py {ano_sel}\n"
            f"python scripts/preparar_dados.py {ano_sel}\n```"
        )
        st.stop()

    df_completo = carregar_dados(str(path_sel))
    st.divider()

    with st.expander("📍 Localização", expanded=True):
        ufs_disp = sorted(df_completo["estado_notificacao"].dropna().unique())
        todos_uf = st.checkbox("Todos os estados", value=True, key="todos_uf")
        uf_sel   = ufs_disp if todos_uf else st.multiselect(
            "Estados", ufs_disp, default=ufs_disp, label_visibility="collapsed"
        )

    with st.expander("👤 Perfil do Paciente", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.caption("Sexo")
            sexo_m = st.checkbox("Masculino", value=True, key="sm")
            sexo_f = st.checkbox("Feminino",  value=True, key="sf")
        with col2:
            st.caption("Forma Clínica")
            forma_pulm  = st.checkbox("Pulmonar",      value=True, key="fp")
            forma_extra = st.checkbox("Extrapulmonar", value=True, key="fe")
            forma_ambos = st.checkbox("Pulm.+Extra",   value=True, key="fa")
        if "raca_cor" in df_completo.columns:
            racas    = sorted(df_completo["raca_cor"].dropna().unique())
            raca_sel = st.multiselect("Raça/Cor", racas, default=racas)
        else:
            racas = []; raca_sel = []

    with st.expander("🏥 Perfil Clínico", expanded=False):
        if "tipo_entrada" in df_completo.columns:
            entradas    = sorted(df_completo["tipo_entrada"].dropna().unique())
            entrada_sel = st.multiselect("Tipo de Entrada", entradas, default=entradas)
        else:
            entradas = []; entrada_sel = []
        if "status_hiv" in df_completo.columns:
            st.caption("HIV")
            hiv_pos_cb = st.checkbox("Positivo",      value=True, key="hpos")
            hiv_neg_cb = st.checkbox("Negativo",      value=True, key="hneg")
            hiv_and_cb = st.checkbox("Em andamento",  value=True, key="hand")
            hiv_nr_cb  = st.checkbox("Não realizado", value=True, key="hnr")
            hiv_ign_cb = st.checkbox("Ignorado",      value=True, key="hign")
            tem_hiv = True
        else:
            tem_hiv = False

    with st.expander("⚠️ Populações Vulneráveis", expanded=False):
        st.caption("Incluir apenas pacientes que sejam:")
        filt_liber = st.checkbox("Privado de liberdade",  value=False, key="liber")
        filt_rua   = st.checkbox("Em situação de rua",    value=False, key="rua")
        filt_saude = st.checkbox("Profissional de saúde", value=False, key="saude")
        filt_imig  = st.checkbox("Imigrante",             value=False, key="imig")
        st.caption("_(deixe desmarcado para não filtrar)_")

    with st.expander("💊 Comorbidades", expanded=False):
        st.caption("Incluir apenas pacientes com:")
        filt_aids   = st.checkbox("AIDS/HIV",          value=False, key="aids")
        filt_alcool = st.checkbox("Alcoolismo",         value=False, key="alc")
        filt_diab   = st.checkbox("Diabetes",           value=False, key="diab")
        filt_drogas = st.checkbox("Drogas ilícitas",    value=False, key="drog")
        filt_tabaco = st.checkbox("Tabagismo",          value=False, key="tab")
        st.caption("_(deixe desmarcado para não filtrar)_")

    if st.button("🔄 Limpar filtros", use_container_width=True):
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  APLICAR FILTROS
# ══════════════════════════════════════════════════════════════════════════════
df = df_completo.copy()

if uf_sel != sorted(df_completo["estado_notificacao"].dropna().unique()):
    df = df[df["estado_notificacao"].isin(uf_sel)]

sexo_vals = ([s for s, v in [("Masculino", sexo_m), ("Feminino", sexo_f)] if v]
             or ["Masculino", "Feminino"])
if "sexo" in df.columns:
    df = df[df["sexo"].isin(sexo_vals)]

forma_vals = ([f for f, v in [
    ("Pulmonar", forma_pulm), ("Extrapulmonar", forma_extra),
    ("Pulmonar + Extrapulmonar", forma_ambos)] if v]
    or ["Pulmonar", "Extrapulmonar", "Pulmonar + Extrapulmonar"])
if "forma" in df.columns:
    df = df[df["forma"].isin(forma_vals) | df["forma"].isna()]

if racas and raca_sel and len(raca_sel) < len(racas):
    df = df[df["raca_cor"].isin(raca_sel)]

if entradas and entrada_sel and len(entrada_sel) < len(entradas) and "tipo_entrada" in df.columns:
    df = df[df["tipo_entrada"].isin(entrada_sel)]

if tem_hiv:
    hiv_vals = ([h for h, v in [
        ("Positivo", hiv_pos_cb), ("Negativo", hiv_neg_cb),
        ("Em andamento", hiv_and_cb), ("Não realizado", hiv_nr_cb), ("Ignorado", hiv_ign_cb)] if v]
        or list(df["status_hiv"].dropna().unique()))
    df = df[df["status_hiv"].isin(hiv_vals)]

for flag, col in [(filt_liber, "populacao_privada_liberdade"),
                  (filt_rua,   "populacao_situacao_rua"),
                  (filt_saude, "profissional_saude"),
                  (filt_imig,  "populacao_imigrante")]:
    if flag and col in df.columns:
        df = df[df[col].astype(str).str.lower() == "sim"]

for flag, col in [(filt_aids, "agravo_aids"), (filt_alcool, "agravo_alcoolismo"),
                  (filt_diab, "agravo_diabetes"), (filt_drogas, "agravo_drogas_ilicitas"),
                  (filt_tabaco, "agravo_tabagismo")]:
    if flag and col in df.columns:
        df = df[df[col].astype(str).str.lower() == "sim"]

df = enriquecer_df(df)

total_base = len(df_completo)
total_filt = len(df)
pct_filt   = round(total_filt / total_base * 100, 1) if total_base else 0
st.sidebar.divider()
st.sidebar.metric("Registros filtrados", f"{total_filt:,}".replace(",", "."),
                  f"de {total_base:,} ({pct_filt}%)".replace(",", "."))
st.sidebar.caption("Fonte: SINAN NET · Ministério da Saúde")

if total_filt == 0:
    st.warning("Nenhum registro encontrado com os filtros selecionados.")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
#  HERO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="hero">
  <h1 class="hero-title">
    <span class="hero-emoji">🫁</span>
    <span>Tuberculose no Brasil</span>
  </h1>
  <p class="hero-subtitle">
    Painel de vigilância epidemiológica baseado em notificações do SINAN —
    perfil dos casos, indicadores clínicos, distribuição geográfica e tendências
    temporais ({ANO_INICIO}–{ANO_ATUAL}).
  </p>
  <div class="hero-badges">
    <span class="hero-badge accent"><span class="dot"></span>Ano {ano_sel}</span>
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

# ══════════════════════════════════════════════════════════════════════════════
#  ABAS
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🗺️ Distribuição Geográfica",
    "👥 Perfil dos Pacientes",
    "🏥 Clínico & Diagnóstico",
    "⚠️ Comorbidades & Vulnerabilidades",
    "📈 Tendência Histórica",
    "🔬 Análise Livre",
])

# ── ABA 1: MAPA ───────────────────────────────────────────────────────────────
with tab1:
    col_mapa, col_uf = st.columns([2, 1])
    _metric = st.session_state.get("metric_mapa", "casos")

    casos_uf  = df.groupby("uf_sigla").size().reset_index(name="casos")
    enc_s     = enc_norm.copy()
    enc_s.index = df.index
    obitos_uf = (df.assign(_enc=enc_s)[df.assign(_enc=enc_s)["_enc"] == "Obito por TB"]
                 .groupby("uf_sigla").size().reset_index(name="obitos")
                 if "uf_sigla" in df.columns else pd.DataFrame(columns=["uf_sigla","obitos"]))
    casos_uf  = casos_uf.merge(obitos_uf, on="uf_sigla", how="left")
    casos_uf["obitos"]      = casos_uf["obitos"].fillna(0).astype(int)
    casos_uf["populacao"]   = casos_uf["uf_sigla"].map(POP_ESTADO)
    casos_uf["incidencia"]  = (casos_uf["casos"]  / casos_uf["populacao"] * 100_000).round(1)
    casos_uf["mortalidade"] = (casos_uf["obitos"] / casos_uf["populacao"] * 100_000).round(1)

    # Raquel ponto 1: padronizar "por 100 mil hab." em vez de "100k"
    _cfg = {
        "casos":       ("casos",       "Total de Casos por Estado",
                        "Total de Casos",                   "YlOrRd", "YlOrRd"),
        "incidencia":  ("incidencia",  "Coeficiente de Incidência por 100 mil hab. — Brasil",
                        "Incidência por 100 mil hab.",      "YlOrRd", "YlOrRd"),
        "mortalidade": ("mortalidade", "Coeficiente de Mortalidade por 100 mil hab. — Brasil",
                        "Mortalidade por 100 mil hab.",     "OrRd",   "OrRd"),
    }
    _col_mapa, _titulo_mapa, _leg_mapa, _pal_folium, _pal_plotly = _cfg.get(_metric, _cfg["casos"])

    with col_mapa:
        st.subheader(_titulo_mapa)
        if FOLIUM_OK:
            try:
                geojson = carregar_geojson()
                gj = copy.deepcopy(geojson)
                for feat in gj["features"]:
                    sigla = feat["properties"].get("sigla", "")
                    row = casos_uf[casos_uf["uf_sigla"] == sigla]
                    if not row.empty:
                        r = row.iloc[0]
                        feat["properties"]["casos"]       = int(r["casos"])
                        feat["properties"]["incidencia"]  = float(r["incidencia"])
                        feat["properties"]["mortalidade"] = float(r["mortalidade"])
                    else:
                        feat["properties"]["casos"] = 0
                        feat["properties"]["incidencia"] = 0.0
                        feat["properties"]["mortalidade"] = 0.0
                m = folium.Map(location=[-14, -52], zoom_start=4,
                               tiles="CartoDB dark_matter", prefer_canvas=True)
                folium.Choropleth(
                    geo_data=gj, data=casos_uf,
                    columns=["uf_sigla", _col_mapa],
                    key_on="feature.properties.sigla",
                    fill_color=_pal_folium, fill_opacity=0.85,
                    line_color="#30363d", line_opacity=0.8,
                    legend_name=_leg_mapa,
                    nan_fill_color="#21262d", nan_fill_opacity=0.4,
                    highlight=True,
                ).add_to(m)
                folium.GeoJson(
                    gj, name="tooltip",
                    style_function=lambda _: {"fillOpacity": 0, "color": "transparent", "weight": 0},
                    highlight_function=lambda _: {"fillOpacity": 0.15, "fillColor": "#fff",
                                                  "weight": 2, "color": "#fff"},
                    tooltip=folium.GeoJsonTooltip(
                        fields=["name", "incidencia", "mortalidade", "casos"],
                        aliases=["Estado:", "Incid./100 mil hab.:", "Mort./100 mil hab.:", "Total de casos:"],
                        localize=True, sticky=True, labels=True,
                        style=("background-color:#161b22;color:#f0f6fc;"
                               "font-family:monospace;font-size:12px;"
                               "border:1px solid #30363d;border-radius:6px;padding:6px;"),
                    ),
                ).add_to(m)
                st_folium(m, use_container_width=True, height=520, returned_objects=[])
            except Exception as e:
                st.warning(f"Mapa Folium indisponível: {e}")
                try:
                    geojson = carregar_geojson()
                    st.plotly_chart(graficos.fig_mapa(df, geojson),
                                    use_container_width=True, config=PLOTLY_CFG)
                except Exception:
                    st.info("GeoJSON não encontrado. Execute: python scripts/baixar_geojson.py")
        else:
            try:
                geojson = carregar_geojson()
                st.plotly_chart(graficos.fig_mapa(df, geojson),
                                use_container_width=True, config=PLOTLY_CFG)
            except Exception:
                st.info("GeoJSON não encontrado. Execute: python scripts/baixar_geojson.py")

    with col_uf:
        st.subheader(_leg_mapa + " por Estado")
        por_uf = casos_uf.sort_values(_col_mapa, ascending=True)
        if not por_uf.empty:
            fig_uf = px.bar(por_uf, x=_col_mapa, y="uf_sigla", orientation="h",
                            color=_col_mapa, color_continuous_scale=_pal_plotly,
                            labels={_col_mapa: _leg_mapa, "uf_sigla": ""})
            tb_layout(fig_uf, altura=H_LARGE)
            fig_uf.update_layout(showlegend=False, coloraxis_showscale=False,
                                 xaxis=dict(title=_leg_mapa), yaxis=dict(title=""))
            fig_uf.update_traces(marker_line_color="#0d1117", marker_line_width=1,
                                 hovertemplate=f"<b>%{{y}}</b><br>{_leg_mapa}: %{{x}}<extra></extra>")
            st.plotly_chart(fig_uf, use_container_width=True, config=PLOTLY_CFG)

# ── ABA 2: PERFIL — pirâmide de casos + pirâmide de óbitos (Raquel ponto 5) ──
_INVAL = ["nan", "None", "undefined", "Nao informado", "Não informado", "Ignorado", ""]

with tab2:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Por Sexo")
        if "sexo" in df.columns:
            d = df["sexo"].value_counts().reset_index()
            d.columns = ["Sexo", "Casos"]
            d = d[~d["Sexo"].isin(_INVAL)]
            graficos.safe_pie(d, "Sexo", "Casos", height=H_SMALL)
        else:
            grafico_vazio()
    with c2:
        st.subheader("Forma Clínica")
        if "forma" in df.columns:
            d = df["forma"].value_counts().reset_index()
            d.columns = ["Forma", "Casos"]
            d = d[~d["Forma"].isin(_INVAL)]
            graficos.safe_pie(d, "Forma", "Casos", height=H_SMALL)
        else:
            grafico_vazio()

    _, c3mid, _ = st.columns([1, 2, 1])
    with c3mid:
        st.subheader("Tipo de Entrada")
        if "tipo_entrada" in df.columns:
            d = df["tipo_entrada"].value_counts().reset_index()
            d.columns = ["Tipo", "Casos"]
            d = d[~d["Tipo"].isin(_INVAL)]
            graficos.safe_pie(d, "Tipo", "Casos", height=H_SMALL)
        else:
            grafico_vazio()

    st.divider()
    c4, c5 = st.columns(2)
    with c4:
        st.subheader("Por Raça/Cor")
        if "raca_cor" in df.columns:
            d = df["raca_cor"].value_counts().reset_index()
            d.columns = ["Raça", "Casos"]
            d = d[~d["Raça"].isin(["nan", "Ignorado", "Nao informado"])]
            graficos.safe_bar_v(d, "Raça", "Casos", height=H_MEDIUM)
        else:
            grafico_vazio()
    with c5:
        st.subheader("Situação de Encerramento")
        col_enc = "situacao_enc_norm" if "situacao_enc_norm" in df.columns else "situacao_encerramento"
        if col_enc in df.columns:
            d = df[col_enc].value_counts().reset_index()
            d.columns = ["Situação", "Casos"]
            d = d[~d["Situação"].isin(_INVAL)]
            graficos.safe_bar_h(d.sort_values("Casos", ascending=False), "Casos", "Situação", height=H_MEDIUM)
        else:
            grafico_vazio()

    st.divider()

    # Raquel ponto 5: duas pirâmides — casos e óbitos
    p1, p2 = st.columns(2)
    with p1:
        st.subheader("Pirâmide Etária — Casos de TB")
        st.caption("Distribuição dos casos notificados por faixa etária e sexo")
        if "idade_anos" in df.columns and "sexo" in df.columns:
            st.plotly_chart(graficos.fig_piramide(df), use_container_width=True, config=PLOTLY_CFG)
        else:
            grafico_vazio()
    with p2:
        st.subheader("Pirâmide Etária — Óbitos por TB")
        st.caption("Distribuição dos óbitos por TB por faixa etária e sexo")
        fig_ob = graficos.fig_piramide_obitos(df)
        if fig_ob:
            st.plotly_chart(fig_ob, use_container_width=True, config=PLOTLY_CFG)
        else:
            st.info("Dados insuficientes de óbitos para a pirâmide.")

# ── ABA 3: CLÍNICO — Raquel ponto 6: Desfecho por status HIV ─────────────────
with tab3:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Status HIV")
        if "status_hiv" in df.columns:
            d = df["status_hiv"].value_counts().reset_index()
            d.columns = ["HIV", "Casos"]
            d = d[~d["HIV"].isin(_INVAL)]
            graficos.safe_pie(d, "HIV", "Casos", height=H_SMALL)
        else:
            grafico_vazio()
    with c2:
        st.subheader("Baciloscopia — 1ª amostra")
        if "baciloscopia_primeira_amostra" in df.columns:
            d = df["baciloscopia_primeira_amostra"].value_counts().reset_index()
            d.columns = ["Resultado", "Casos"]
            d = d[~d["Resultado"].isin(_INVAL)]
            graficos.safe_pie(d, "Resultado", "Casos", height=H_SMALL)
        else:
            grafico_vazio()

    _, c3mid2, _ = st.columns([1, 2, 1])
    with c3mid2:
        st.subheader("Teste Molecular Rápido (TMR-TB)")
        if "teste_molecular" in df.columns:
            d = df["teste_molecular"].value_counts().reset_index()
            d.columns = ["Resultado", "Casos"]
            d = d[~d["Resultado"].isin(_INVAL)]
            graficos.safe_pie(d, "Resultado", "Casos", height=H_SMALL)
        else:
            grafico_vazio()

    st.divider()

    # Raquel ponto 6: Desfecho por status HIV
    st.subheader("Desfecho do Tratamento por Status HIV")
    st.caption("Distribuição percentual dos desfechos dentro de cada grupo de status HIV. "
               "Pacientes HIV+ tendem a apresentar mais óbitos e abandonos.")
    graficos.fig_desfecho_por_hiv(df)

    st.divider()
    st.subheader("Coinfecção TB-HIV por Estado")
    st.caption("Percentual de casos com HIV positivo sobre o total de casos notificados no estado")
    graficos.fig_coinfeccao_hiv_uf(df)

# ── ABA 4: COMORBIDADES ───────────────────────────────────────────────────────
with tab4:
    col_comor, col_vuln = st.columns([3, 2])
    with col_comor:
        st.subheader("Comorbidades Associadas")
        st.caption("Percentual dos casos notificados com cada comorbidade registrada")
        graficos.fig_comorbidades(df, total)
    with col_vuln:
        st.subheader("Populações Vulneráveis")
        st.markdown("<br>", unsafe_allow_html=True)
        vuln = {
            "Privado de Liberdade":  (df.get("populacao_privada_liberdade", pd.Series(dtype=str)).astype(str).str.lower() == "sim").sum(),
            "Em Situação de Rua":    (df.get("populacao_situacao_rua",      pd.Series(dtype=str)).astype(str).str.lower() == "sim").sum(),
            "Profissional de Saúde": (df.get("profissional_saude",          pd.Series(dtype=str)).astype(str).str.lower() == "sim").sum(),
            "Imigrante":             (df.get("populacao_imigrante",         pd.Series(dtype=str)).astype(str).str.lower() == "sim").sum(),
        }
        for label, val in vuln.items():
            st.metric(label, f"{val:,}".replace(",", "."), pct(val, total))
            st.markdown("<div style='margin-bottom:6px'></div>", unsafe_allow_html=True)

    st.divider()
    st.subheader("Comorbidades por Estado *(% sobre total de casos no estado)*")
    graficos.fig_comorbidades_uf(df)

# ── ABA 5: TENDÊNCIA ─────────────────────────────────────────────────────────
with tab5:
    df_hist  = load_historico()
    ANOS_HIST = list(range(ANO_INICIO, ano_sel))

    if df_hist is None or not ANOS_HIST:
        st.warning(
            "Dados históricos não encontrados — apenas 1 ano disponível.\n\n"
            "Execute `python scripts/conectar_banco.py 2001 2024` para popular o histórico."
        )
        # Fallback: distribuição mensal do ano atual
        if "mes_num" in df.columns:
            st.subheader(f"Número de casos por mês — {ano_sel}")
            st.caption(f"Total de notificações de TB por mês de notificação — ano {ano_sel}")
            mes = (df.dropna(subset=["mes_num"])
                   .groupby("mes_num").size().reset_index(name="casos"))
            mes["mes_label"] = mes["mes_num"].map(graficos.MESES_PT)
            mes = mes.sort_values("mes_num")
            media_m = mes["casos"].mean()
            fig_mes = px.bar(mes, x="mes_label", y="casos",
                             labels={"mes_label": "Mês", "casos": "Nº de casos notificados"})
            fig_mes.add_hline(y=media_m, line_dash="dot", line_color="#58a6ff",
                              annotation_text=f"Média mensal: {media_m:,.0f}".replace(",", "."),
                              annotation_font=dict(color="#58a6ff", size=11))
            tb_layout(fig_mes, altura=H_LARGE)
            fig_mes.update_traces(marker_color="#d29922",
                                  marker_line_color="#0d1117", marker_line_width=1,
                                  hovertemplate="<b>%{x}</b><br>Nº de casos: %{y:,}<extra></extra>")
            st.plotly_chart(fig_mes, use_container_width=True, config=PLOTLY_CFG)
    else:
        # KPIs de tendência
        df_mensal = df_hist["mensal"]
        hist_anos = df_mensal[df_mensal["nu_ano"].astype(str).isin([str(a) for a in ANOS_HIST])]
        media_anual_hist = hist_anos.groupby("nu_ano")["casos"].sum().mean() if not hist_anos.empty else 0
        variacao_geral   = ((total - media_anual_hist) / media_anual_hist * 100) if media_anual_hist else 0
        tend_icon  = "⬆️" if variacao_geral > 5 else ("⬇️" if variacao_geral < -5 else "➡️")
        tend_label = "Para Mais" if variacao_geral > 5 else ("Para Menos" if variacao_geral < -5 else "Estável")

        ka, kb, kc = st.columns(3)
        ka.metric("Tendência vs histórico", f"{tend_icon} {tend_label}",
                  f"{variacao_geral:+.1f}% vs {ANO_INICIO}–{ano_sel-1}")
        kb.metric(f"Total {ano_sel}", f"{int(total):,}".replace(",", "."), "casos notificados")
        kc.metric("Média anual histórica", f"{int(media_anual_hist):,}".replace(",", "."),
                  f"casos/ano | {ANO_INICIO}–{ano_sel-1}")

        st.divider()

        # Raquel ponto 3: título explícito com unidade
        st.subheader(f"Número médio de casos notificados por mês — {ano_sel} vs Média {ANO_INICIO}–{ano_sel-1}")
        st.caption(f"Barras = notificações mensais de {ano_sel} (filtradas). "
                   f"Linha pontilhada = média mensal histórica {ANO_INICIO}–{ano_sel-1} (base total).")
        graficos.fig_tendencia_mensal(df, df_hist, ano_sel, ANOS_HIST)

        st.divider()
        st.subheader(f"Evolução Anual do Total de Casos — {ANO_INICIO}–{ANO_ATUAL}")
        st.caption("Total de notificações de TB por ano. Barra vermelha = ano selecionado.")
        graficos.fig_tendencia_anual(df_hist, ano_sel)

        st.divider()
        st.subheader(f"Variação por Estado — {ano_sel} vs Média {ANO_INICIO}–{ano_sel-1}")
        st.caption("Variação percentual em relação à média histórica. "
                   "Vermelho = Para Mais | Verde = Para Menos | Amarelo = Estável (±5%).")
        graficos.fig_tendencia_uf(df, df_hist, ano_sel, ANOS_HIST)

        # Raquel ponto 4: indicadores históricos com multiselect
        if HIST_INDICADORES.exists():
            st.divider()
            st.subheader(f"Evolução Histórica de Indicadores Clínicos — {ANO_INICIO}–{ANO_ATUAL}")
            st.caption("Selecione os indicadores para comparar a evolução ao longo dos anos.")
            try:
                df_ind = pd.read_csv(str(HIST_INDICADORES))
                opcoes_multisel = [
                    "Coeficiente de incidência (por 100 mil)",
                    "Coeficiente de mortalidade (por 100 mil)",
                    "Taxa de cura (%)",
                    "Taxa de abandono (%)",
                    "Coinfecção HIV (%)",
                    "Forma pulmonar (%)",
                    "Testagem para HIV (%)",
                    "TDO (%)",
                    "Óbito por TB (%)",
                    "Casos novos (%)",
                ]
                sel_ind = st.multiselect(
                    "Selecione os indicadores:",
                    options=opcoes_multisel,
                    default=["Coinfecção HIV (%)", "Taxa de cura (%)", "Taxa de abandono (%)"],
                )
                if sel_ind:
                    graficos.fig_indicadores_historicos(df_ind, sel_ind, ano_sel)
            except Exception as e:
                st.warning(f"Erro ao carregar indicadores históricos: {e}")

# ── ABA 6: ANÁLISE LIVRE ──────────────────────────────────────────────────────────────────────────────
with tab6:
    st.subheader("Análise Livre")
    st.caption("Monte seus próprios gráficos arrastando e soltando os campos.")
    df_analise = selecionar_colunas(df, COLUNAS_ANALISE)
    st.info(
        f"**{len(df_analise):,}** registros  |  "
        f"**{len(df_analise.columns)}** variáveis disponíveis",
        icon="📊",
    )
    spec = SPEC_PATH if Path(SPEC_PATH).exists() else None
    html = gerar_html_pygwalker(df_analise, spec_path=spec)
    components.html(html, height=1000, scrolling=True)
