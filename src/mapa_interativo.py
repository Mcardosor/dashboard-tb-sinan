"""
mapa_interativo.py
──────────────────
Mapa Plotly com drill-down clicável: Brasil → Estado → Município.

Por que Plotly e não Folium:
  - Renderização 100% no browser (JavaScript), zero bloqueio do servidor Python
  - @st.cache_resource compartilha GeoJSON entre TODAS as sessões (carregado 1x)
  - on_select="rerun" nativo no Streamlit ≥1.35 captura cliques sem callbacks
  - Escala para milhares de usuários simultâneos sem travamento

Arquitetura de cache:
  _geo_estados()      → @st.cache_resource  (1 objeto, vive enquanto o servidor rodar)
  _geo_municipios()   → @st.cache_resource  (1 por UF, carregado sob demanda)
  _agg_estados()      → @st.cache_data      (1 por hash do df)
  _agg_municipios()   → @st.cache_data      (1 por hash do df + UF)
"""

import gzip
import json
import unicodedata
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.constantes import UF_SIGLAS, POP_ESTADO, BG, HOVER_LABEL, ESCALA_MAPA

# ── Caminhos ───────────────────────────────────────────────────────────────────
_GEO = Path("dados_dashboard") / "_geo_cache"


# ── Helpers ────────────────────────────────────────────────────────────────────
def _norm(s: str) -> str:
    """Remove acentos e padroniza para join com nomes do SINAN."""
    return (
        unicodedata.normalize("NFD", str(s))
        .encode("ascii", "ignore")
        .decode()
        .lower()
        .strip()
    )


# ── Carregamento com cache de recurso ─────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def _geo_estados() -> dict:
    """GeoJSON dos 27 estados — carregado uma única vez por todos os usuários."""
    p = _GEO / "br_ufs.geojson.gz"
    if not p.exists():
        return {"type": "FeatureCollection", "features": []}
    with gzip.open(p, "rt", encoding="utf-8") as f:
        return json.load(f)


@st.cache_resource(show_spinner=False)
def _geo_municipios(uf: str) -> dict | None:
    """GeoJSON dos municípios do estado — carregado por demanda, compartilhado."""
    p = _GEO / "municipios" / f"uf={uf}" / "mun_simpl.geojson.gz"
    if not p.exists():
        return None
    with gzip.open(p, "rt", encoding="utf-8") as f:
        return json.load(f)


# ── Agregações com cache de dados ─────────────────────────────────────────────
@st.cache_data(
    show_spinner=False,
    hash_funcs={pd.DataFrame: lambda df: (df.shape, df.columns.tolist())},
)
def _agg_estados(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega casos e incidência por UF para o mapa do Brasil."""
    agg = (
        df["estado_notificacao"].astype(str)
        .map(UF_SIGLAS)
        .dropna()
        .value_counts()
        .reset_index()
        .rename(columns={"estado_notificacao": "uf", "count": "casos"})
    )
    pop_map = POP_ESTADO
    agg["incid_100k"] = (
        agg.apply(
            lambda r: round(r["casos"] / pop_map.get(r["uf"], 1) * 100_000, 1),
            axis=1,
        )
    )
    return agg


@st.cache_data(
    show_spinner=False,
    hash_funcs={pd.DataFrame: lambda df: (df.shape, df.columns.tolist())},
)
def _agg_municipios(df: pd.DataFrame, uf: str) -> pd.DataFrame:
    """Agrega casos por município para o drill-down estadual."""
    mask = df["estado_notificacao"].astype(str).map(UF_SIGLAS) == uf
    sub = df.loc[mask, "municipio_notificacao"].astype(str)
    agg = (
        sub.value_counts()
        .reset_index()
        .rename(columns={"municipio_notificacao": "municipio", "count": "casos"})
    )
    agg["municipio_norm"] = agg["municipio"].map(_norm)
    return agg


# ── Bounding box do GeoJSON ────────────────────────────────────────────────────
def _bbox(geojson: dict, pad: float = 0.6) -> tuple[list, list]:
    """
    Calcula lataxis_range e lonaxis_range a partir das coordenadas do GeoJSON.
    Muito mais confiável que fitbounds='locations' para mapas subnacionais.
    Retorna (lataxis_range, lonaxis_range).
    """
    lats: list[float] = []
    lons: list[float] = []

    def _collect(coords, depth: int) -> None:
        if depth == 0:
            lons.append(float(coords[0]))
            lats.append(float(coords[1]))
        else:
            for c in coords:
                _collect(c, depth - 1)

    type_depth = {
        "Point": 0, "MultiPoint": 1,
        "LineString": 1, "MultiLineString": 2,
        "Polygon": 2, "MultiPolygon": 3,
    }

    for feat in geojson.get("features", []):
        geom = feat.get("geometry") or {}
        depth = type_depth.get(geom.get("type", ""), 2)
        try:
            _collect(geom.get("coordinates", []), depth)
        except Exception:
            pass

    if not lats:
        return [-34.0, 6.0], [-74.0, -28.0]

    return (
        [min(lats) - pad, max(lats) + pad],
        [min(lons) - pad, max(lons) + pad],
    )


# ── Configuração de geo transparente ─────────────────────────────────────────
_GEO_LAYOUT = dict(
    bgcolor="rgba(0,0,0,0)",
    showland=False,
    showcoastlines=False,
    showframe=False,
    showocean=False,
    showlakes=False,
    showrivers=False,
    showcountries=False,
    showsubunits=False,
)

_LAYOUT_BASE = dict(
    margin=dict(r=0, t=0, l=0, b=0),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    hoverlabel=HOVER_LABEL,
    dragmode=False,
)

_COLORBAR = dict(title="Casos", thickness=14, len=0.7, tickfont=dict(size=11))


def _dark_scale(max_val: float) -> list:
    """
    Colorscale que usa fundo escuro para z=0 e a escala normal para z>0.
    Municípios sem dados ficam invisíveis no tema escuro; os com dados se destacam.
    """
    if max_val <= 0:
        return [[0.0, "#1c2128"], [1.0, "#1c2128"]]
    cut = min(1.0 / max_val, 0.015)
    return [
        [0.0,  "#1c2128"],
        [cut,  "#FFF5F0"],
        [0.15, "#FDCBB7"],
        [0.35, "#FC8A6A"],
        [0.55, "#F14432"],
        [0.75, "#C0151A"],
        [1.0,  "#67000D"],
    ]


# ── Figuras Plotly ─────────────────────────────────────────────────────────────
def fig_brasil(df: pd.DataFrame) -> go.Figure:
    """
    Mapa coroplético do Brasil por estado.
    Clique num estado → evento on_select retorna o campo 'uf'.
    """
    geojson = _geo_estados()
    agg = _agg_estados(df)

    if agg.empty:
        return go.Figure()

    max_val = float(agg["casos"].max())
    scale = _dark_scale(max_val)

    fig = go.Figure(go.Choropleth(
        geojson=geojson,
        locations=agg["uf"].tolist(),
        z=agg["casos"].tolist(),
        featureidkey="properties.uf",
        colorscale=scale,
        zmin=0,
        zmax=max_val,
        text=agg["uf"].tolist(),
        customdata=agg[["incid_100k"]].values.tolist(),
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Notificações: <b>%{z:,}</b><br>"
            "Incidência: <b>%{customdata[0]:.1f}</b> / 100k hab"
            "<extra></extra>"
        ),
        colorbar=_COLORBAR,
        marker_line_color="rgba(255,255,255,0.2)",
        marker_line_width=0.7,
        selected_marker=dict(opacity=1.0),
        unselected_marker=dict(opacity=0.65),
    ))
    fig.update_layout(
        geo=_GEO_LAYOUT,
        **_LAYOUT_BASE,
        height=500,
        clickmode="event+select",
    )
    fig.update_geos(fitbounds="locations")
    return fig


def fig_estado(df: pd.DataFrame, uf: str) -> go.Figure:
    """
    Mapa coroplético dos municípios de um estado.
    Municípios sem notificações ficam escuros (transparentes no tema dark).
    Usa bounding box calculado do GeoJSON para zoom correto.
    """
    geojson = _geo_municipios(uf)
    if geojson is None or not geojson.get("features"):
        return go.Figure()

    agg = _agg_municipios(df, uf)
    casos_map: dict[str, int] = dict(zip(agg["municipio_norm"], agg["casos"]))

    rows = []
    for feat in geojson["features"]:
        props = feat["properties"]
        nm_norm = props.get("NM_MUN_NORM", _norm(props.get("NM_MUN", "")))
        rows.append({
            "cd_mun": props["CD_MUN"],
            "nome":   props["NM_MUN"],
            "casos":  casos_map.get(nm_norm, 0),
        })

    df_mun = pd.DataFrame(rows)
    max_val = float(df_mun["casos"].max())
    scale = _dark_scale(max_val)

    # Calcula bounding box para zoom correto
    lat_range, lon_range = _bbox(geojson)

    fig = go.Figure(go.Choropleth(
        geojson=geojson,
        locations=df_mun["cd_mun"].tolist(),
        z=df_mun["casos"].tolist(),
        featureidkey="properties.CD_MUN",
        colorscale=scale,
        zmin=0,
        zmax=max_val if max_val > 0 else 1.0,
        text=df_mun["nome"].tolist(),
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Notificações: <b>%{z:,}</b>"
            "<extra></extra>"
        ),
        colorbar=_COLORBAR,
        marker_line_color="rgba(255,255,255,0.18)",
        marker_line_width=0.4,
    ))
    fig.update_layout(
        geo={
            **_GEO_LAYOUT,
            "lataxis_range": lat_range,
            "lonaxis_range": lon_range,
        },
        **_LAYOUT_BASE,
        height=520,
    )
    return fig


# ── Utilitário de estado inverso ───────────────────────────────────────────────
_UF_PARA_NOME: dict[str, str] = {v: k for k, v in UF_SIGLAS.items()}


def uf_para_nome(uf: str) -> str:
    """Converte sigla UF para nome completo do estado."""
    return _UF_PARA_NOME.get(uf, uf)
