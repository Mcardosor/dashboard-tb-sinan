"""Distribuição Geográfica — Mapa coroplético + ranking por estado."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.express as px
from streamlit_folium import st_folium

from src.styles import inject_css_page
from src.session import get_df, get_context
from src.constantes import UF_SIGLAS, H_LARGE, PLOTLY_CFG
from src.graficos import tb_layout
from src.dados import agregar_por_uf
from src import graficos, mapa_interativo

st.set_page_config(page_title="Distribuição Geográfica | TB SINAN", page_icon="🗺️", layout="wide")
inject_css_page()

df  = get_df()
ctx = get_context()
enc_norm = ctx["enc_norm"]

# ── Session state ─────────────────────────────────────────────────────────────
if "metric_mapa" not in st.session_state:
    st.session_state.metric_mapa = "casos"
if "mapa_key_counter" not in st.session_state:
    st.session_state.mapa_key_counter = 0

st.title("🗺️ Distribuição Geográfica")


# ── Modal de municípios ───────────────────────────────────────────────────────
@st.dialog("Distribuição por Município", width="large")
def _modal_municipios(uf: str) -> None:
    nome  = mapa_interativo.uf_para_nome(uf)
    mask  = df["estado_notificacao"].astype(str).map(UF_SIGLAS) == uf
    total_uf = int(mask.sum())
    st.markdown(f"**{nome} ({uf})** · {total_uf:,} notificações")

    m_est = mapa_interativo.mapa_estado(df, uf)
    if m_est is not None:
        st_folium(m_est, height=480, use_container_width=True,
                  key=f"dialog_{uf}", returned_objects=[])
    else:
        st.warning(f"GeoJSON de {uf} não encontrado.")

    if mask.any():
        st.divider()
        total_mun = df.loc[mask, "municipio_notificacao"].astype(str).nunique()
        top_n = st.select_slider(
            "Exibir top municípios:",
            options=[10, 15, 20], value=15,
            key=f"top_n_{uf}",
        )
        top_mun = (
            df.loc[mask, "municipio_notificacao"].astype(str)
            .value_counts().head(top_n).reset_index()
            .rename(columns={"municipio_notificacao": "municipio", "count": "casos"})
            .sort_values("casos", ascending=True)
        )
        st.caption(f"Exibindo top {top_n} de {total_mun} municípios com notificações")
        max_casos  = int(top_mun["casos"].max())
        margem_dir = max(60, len(f"{max_casos:,}") * 9)
        fig_mun = px.bar(top_mun, x="casos", y="municipio", orientation="h",
                         color="casos", color_continuous_scale="YlOrRd",
                         labels={"casos": "Casos", "municipio": ""}, text="casos")
        fig_mun.update_layout(
            height=max(320, top_n * 26), showlegend=False, coloraxis_showscale=False,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#c9d1d9", margin=dict(l=0, r=margem_dir, t=10, b=0),
            xaxis=dict(type="log", title="Casos (escala log)"),
        )
        fig_mun.update_traces(
            marker_line_color="#0d1117", marker_line_width=1,
            texttemplate="%{text:,}", textposition="outside", cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>Casos: %{x:,}<extra></extra>",
        )
        st.plotly_chart(fig_mun, use_container_width=True)

        with st.expander(f"📋 Ver todos os {total_mun} municípios"):
            tabela = (
                df.loc[mask, "municipio_notificacao"].astype(str)
                .value_counts().reset_index()
                .rename(columns={"municipio_notificacao": "Município", "count": "Casos"})
            )
            tabela.index = range(1, len(tabela) + 1)
            st.dataframe(tabela, use_container_width=True, height=300)


# ── Mapa ──────────────────────────────────────────────────────────────────────
_metric = st.session_state.get("metric_mapa", "casos")
casos_uf = agregar_por_uf(df, enc_norm)

_cfg = {
    "casos":       ("casos",      "Total de Casos por Estado",                           "Total de Casos",             "YlOrRd"),
    "incidencia":  ("incidencia", "Coeficiente de Incidência por 100 mil hab. — Brasil", "Incidência por 100 mil hab.", "YlOrRd"),
    "mortalidade": ("mortalidade","Coeficiente de Mortalidade por 100 mil hab. — Brasil","Mortalidade por 100 mil hab.","OrRd"),
}
_col_mapa, _titulo_mapa, _leg_mapa, _pal_plotly = _cfg.get(_metric, _cfg["casos"])

col_mapa, col_uf = st.columns([2, 1])

with col_mapa:
    st.subheader(_titulo_mapa)
    st.caption("💡 Clique num estado no mapa ou selecione abaixo para ver os municípios.")

    _sel_box = st.session_state.get("sel_estado_tab1", "")
    _highlighted_uf = (
        _sel_box.split(" — ")[0].strip()
        if _sel_box and _sel_box != "— selecione um estado —"
        else None
    )

    fig_mapa = mapa_interativo.fig_brasil(casos_uf, metrica=_metric, selected_uf=_highlighted_uf)
    ev = st.plotly_chart(
        fig_mapa, on_select="rerun",
        key=f"mapa_br_{st.session_state.mapa_key_counter}",
        use_container_width=True,
    )

    def _sel_changed():
        sel = st.session_state.get("sel_estado_tab1", "")
        if sel and sel != "— selecione um estado —":
            st.session_state["_dialog_uf"] = sel.split(" — ")[0].strip()

    _ufs_disp = sorted(casos_uf["uf_sigla"].dropna().unique().tolist())
    _uf_nomes = {u: f"{u} — {mapa_interativo.uf_para_nome(u)}" for u in _ufs_disp}
    st.selectbox(
        "Explorar municípios:",
        ["— selecione um estado —"] + [_uf_nomes[u] for u in _ufs_disp],
        key="sel_estado_tab1",
        label_visibility="collapsed",
        on_change=_sel_changed,
    )

    if ev and ev.selection and ev.selection.points:
        if not st.session_state.get("_dialog_uf"):
            uf_clicado = ev.selection.points[0].get("location")
            if uf_clicado:
                st.session_state["_dialog_uf"] = uf_clicado

    if st.session_state.get("_dialog_uf"):
        _uf = st.session_state.pop("_dialog_uf")
        st.session_state.mapa_key_counter += 1
        _modal_municipios(_uf)

with col_uf:
    st.subheader(_leg_mapa + " por Estado")
    if _metric == "incidencia":
        st.caption("📌 Incidência por 100 mil hab.: permite comparar estados de tamanhos diferentes.")
    elif _metric == "mortalidade":
        st.caption("📌 Mortalidade por 100 mil hab.: estados com valor mais alto precisam de atenção prioritária.")
    else:
        st.caption("📌 Total absoluto de casos notificados no estado.")
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
