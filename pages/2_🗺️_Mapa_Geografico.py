"""
Página dedicada ao mapa geográfico com drill-down Brasil → Estado → Município.
Separada do app principal para evitar o bug do st_folium dentro de st.tabs no Chrome.
"""

import streamlit as st
import pandas as pd
from streamlit_folium import st_folium
import re

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.constantes import UF_SIGLAS, anos_disponiveis
from src.dados import carregar_dados, enriquecer_df, agregar_por_uf
from src.styles import inject_css_page
from src import mapa_interativo

st.set_page_config(
    page_title="Mapa Geográfico | TB SINAN",
    page_icon="🗺️",
    layout="wide",
)

inject_css_page()

# ── Sidebar: filtros de ano ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🗺️ Mapa Geográfico")
    anos = anos_disponiveis()
    ano_sel = st.selectbox("Ano", options=anos, index=0)

anos_key = (ano_sel,)
df_raw = carregar_dados(anos_key)
if df_raw.empty:
    st.error(f"Dados de {ano_sel} não encontrados. Execute `python scripts/preparar_dados.py {ano_sel}`")
    st.stop()

df = enriquecer_df(df_raw)

# ── Session state ─────────────────────────────────────────────────────────────
if "map_selected_uf" not in st.session_state:
    st.session_state.map_selected_uf = None

_selected_uf = st.session_state.map_selected_uf

# ── Agrega por UF ─────────────────────────────────────────────────────────────
casos_uf = agregar_por_uf(df)

# ── Layout ────────────────────────────────────────────────────────────────────
if _selected_uf is None:
    # ══ NÍVEL BRASIL ══════════════════════════════════════════════════════════
    st.title("🗺️ Distribuição Geográfica — Brasil")
    st.caption(f"Tuberculose · {ano_sel} · Clique num estado para ver os municípios")

    m = mapa_interativo.mapa_brasil(casos_uf)
    result = st_folium(
        m,
        height=560,
        use_container_width=True,
        key="folium_brasil",
        returned_objects=["last_object_clicked_tooltip"],
    )

    uf_clicado = mapa_interativo.extrair_uf_clicado(result)
    if uf_clicado:
        st.session_state.map_selected_uf = uf_clicado
        st.rerun()

    # Fallback: selectbox
    st.divider()
    _ufs = sorted(casos_uf["uf_sigla"].dropna().unique().tolist())
    _nomes = {u: f"{u} — {mapa_interativo.uf_para_nome(u)}" for u in _ufs}
    _sel = st.selectbox(
        "Ou selecione um estado:",
        ["— selecione —"] + [_nomes[u] for u in _ufs],
        key="sel_estado_geo",
    )
    if _sel != "— selecione —":
        st.session_state.map_selected_uf = _sel.split(" — ")[0].strip()
        st.rerun()

else:
    # ══ NÍVEL ESTADO ══════════════════════════════════════════════════════════
    nome_estado = mapa_interativo.uf_para_nome(_selected_uf)

    col_btn, col_titulo = st.columns([1, 8])
    with col_btn:
        if st.button("← Brasil", key="voltar_brasil"):
            st.session_state.map_selected_uf = None
            st.rerun()
    with col_titulo:
        st.title(f"🗺️ {nome_estado} ({_selected_uf}) — Municípios")
        st.caption(f"Tuberculose · {ano_sel} · {df[df['estado_notificacao'].astype(str).map(UF_SIGLAS) == _selected_uf].shape[0]:,} notificações")

    m_est = mapa_interativo.mapa_estado(df, _selected_uf)
    if m_est is not None:
        st_folium(
            m_est,
            height=600,
            use_container_width=True,
            key=f"folium_{_selected_uf}",
            returned_objects=[],
        )
    else:
        st.warning(f"GeoJSON de {_selected_uf} não encontrado. Execute: `python scripts/preparar_geo_cache.py`")

    # Top municípios
    st.divider()
    mask = df["estado_notificacao"].astype(str).map(UF_SIGLAS) == _selected_uf
    if mask.any():
        import plotly.express as px
        st.divider()
        total_mun = df.loc[mask, "municipio_notificacao"].astype(str).nunique()
        top_n = st.select_slider(
            "Exibir top municípios:",
            options=[10, 15, 20],
            value=15,
            key="top_n_geo",
        )
        top_mun = (
            df.loc[mask, "municipio_notificacao"].astype(str)
            .value_counts().head(top_n).reset_index()
            .rename(columns={"municipio_notificacao": "municipio", "count": "casos"})
            .sort_values("casos", ascending=True)
        )
        st.subheader(f"Top {top_n} municípios — {nome_estado}")
        st.caption(f"Exibindo top {top_n} de {total_mun} municípios com notificações")
        max_casos = int(top_mun["casos"].max())
        margem_dir = max(60, len(f"{max_casos:,}") * 9)
        fig = px.bar(top_mun, x="casos", y="municipio", orientation="h",
                     color="casos", color_continuous_scale="Blues",
                     labels={"casos": "Casos", "municipio": ""},
                     text="casos")
        fig.update_layout(
            height=max(360, top_n * 26), showlegend=False, coloraxis_showscale=False,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#c9d1d9", yaxis=dict(title=""),
            xaxis=dict(type="log", title="Casos (escala log)"),
            margin=dict(l=0, r=margem_dir, t=10, b=0),
        )
        fig.update_traces(
            marker_line_color="#0d1117", marker_line_width=1,
            texttemplate="%{text:,}", textposition="outside",
            cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>Casos: %{x:,}<extra></extra>",
        )
        st.plotly_chart(fig, use_container_width=True)

        with st.expander(f"📋 Ver todos os {total_mun} municípios"):
            tabela = (
                df.loc[mask, "municipio_notificacao"].astype(str)
                .value_counts().reset_index()
                .rename(columns={"municipio_notificacao": "Município", "count": "Casos"})
            )
            tabela.index = range(1, len(tabela) + 1)
            st.dataframe(tabela, use_container_width=True, height=300)
