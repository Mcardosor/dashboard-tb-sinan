"""
mapa_interativo.py — Mapas interativos do dashboard TB SINAN.

Plotly Choroplethmapbox: mapa do Brasil por estado (aba principal).
Folium: mapa drill-down por estado/município (modal e página dedicada).
Tiles: CARTO dark matter (sem token necessário).
"""

import gzip
import json
import re
import unicodedata
from pathlib import Path

import branca.colormap as cm
import folium
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.constantes import UF_SIGLAS, POP_ESTADO

_GEO = Path("dados_dashboard") / "_geo_cache"


# ── GeoJSON cache ─────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def _geo_estados() -> dict:
    p = _GEO / "br_ufs.geojson.gz"
    if not p.exists():
        return {"type": "FeatureCollection", "features": []}
    with gzip.open(p, "rt", encoding="utf-8") as f:
        return json.load(f)


@st.cache_resource(show_spinner=False)
def _geo_ras_df() -> dict | None:
    """GeoJSON das Regiões Administrativas do DF (OpenStreetMap via Overpass)."""
    p = Path("dados_dashboard") / "df_regioes_administrativas.geojson"
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


@st.cache_resource(show_spinner=False)
def _geo_municipios(uf: str) -> dict | None:
    p = _GEO / "municipios" / f"uf={uf}" / "mun_simpl.geojson.gz"
    if not p.exists():
        return None
    with gzip.open(p, "rt", encoding="utf-8") as f:
        return json.load(f)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _norm(s: str) -> str:
    return (
        unicodedata.normalize("NFD", str(s))
        .encode("ascii", "ignore")
        .decode()
        .lower()
        .strip()
    )


_UF_PARA_NOME: dict[str, str] = {v: k for k, v in UF_SIGLAS.items()}

def uf_para_nome(uf: str) -> str:
    return _UF_PARA_NOME.get(uf, uf)



def fig_brasil(casos_uf: pd.DataFrame, metrica: str = "casos", selected_uf: str | None = None) -> go.Figure:
    """
    Mapa coroplético do Brasil por estado — Choroplethmapbox + carto-darkmatter.
    Confirmado funcionando no Streamlit. Usado na aba principal do dashboard.
    selected_uf: sigla do estado a destacar com borda (ex: "CE").
    """
    geojson = _geo_estados()
    if casos_uf.empty:
        return go.Figure()

    col = {"casos": "casos", "incidencia": "incidencia", "mortalidade": "mortalidade"}.get(metrica, "casos")
    leg = {"casos": "Casos", "incidencia": "Incid./100 mil hab.", "mortalidade": "Mort./100 mil hab."}.get(metrica, "Casos")
    max_val = float(casos_uf[col].max()) if len(casos_uf) > 0 else 1.0

    hover_cols = [c for c in ["casos", "incidencia", "mortalidade"] if c in casos_uf.columns]
    fig = go.Figure(go.Choroplethmapbox(
        geojson=geojson,
        locations=casos_uf["uf_sigla"].tolist(),
        z=casos_uf[col].tolist(),
        featureidkey="properties.uf",
        colorscale="YlOrRd",
        zmin=0, zmax=max_val,
        text=casos_uf["uf_sigla"].tolist(),
        customdata=casos_uf[hover_cols].values.tolist(),
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Casos: <b>%{customdata[0]:,.0f}</b><br>"
            "Incidência: <b>%{customdata[1]:.1f}</b> / 100 mil hab.<br>"
            "Mortalidade: <b>%{customdata[2]:.1f}</b> / 100 mil hab."
            "<extra></extra>"
        ),
        colorbar=dict(title=leg, thickness=14, len=0.7, tickfont=dict(size=11)),
        marker_line_color="rgba(255,255,255,0.3)",
        marker_line_width=0.8,
        marker_opacity=0.85,
    ))

    # Destaque do estado selecionado pelo dropdown
    if selected_uf:
        fig.add_trace(go.Choroplethmapbox(
            geojson=geojson,
            locations=[selected_uf],
            z=[0],
            featureidkey="properties.uf",
            colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
            showscale=False,
            marker_line_color="#00d4ff",
            marker_line_width=3,
            hoverinfo="skip",
            name="",
        ))

    fig.update_layout(
        mapbox=dict(style="carto-darkmatter", center={"lat": -14.24, "lon": -51.93}, zoom=3.2),
        margin=dict(r=0, t=0, l=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(bgcolor="#1c2128", font_color="#f0f6fc", font_size=13),
        height=500,
        clickmode="event+select",
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# FOLIUM — usado na página dedicada (pages/), sem bug do st.tabs + Chrome
# ══════════════════════════════════════════════════════════════════════════════

_CARTO_DARK = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
_CARTO_ATTR = (
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    ' &copy; <a href="https://carto.com/attributions">CARTO</a>'
)


def _cmap_brasil(max_val: float) -> cm.LinearColormap:
    return cm.LinearColormap(
        colors=["#FFF5F0", "#FDCBB7", "#FC8A6A", "#F14432", "#C0151A", "#67000D"],
        vmin=0, vmax=max(float(max_val), 1.0), caption="",
    )


def _cmap_estado(max_val: float) -> cm.LinearColormap:
    """Colormap YlOrRd em escala logarítmica — distribui bem dados com outliers."""
    import math
    # Usa log para o vmax → mesma paleta do Brasil mas distribuída em log
    log_max = math.log1p(max(float(max_val), 1.0))
    return cm.LinearColormap(
        colors=["#FFFFCC", "#FED976", "#FEB24C", "#FD8D3C", "#FC4E2A", "#E31A1C", "#B10026"],
        vmin=0, vmax=log_max, caption="",
    )


def _cor_municipio(val: int, cmap: cm.LinearColormap, max_val: float) -> str:
    """Aplica escala log ao valor antes de mapear a cor — spread uniforme."""
    import math
    if val <= 0:
        return "#d9cfc4"   # bege claro neutro para municípios sem notificações
    t = math.log1p(val)
    return cmap(t)


def _bbox_geojson(geojson: dict) -> tuple[list, list]:
    lats, lons = [], []
    def _collect(coords, depth):
        if depth == 0:
            lons.append(float(coords[0])); lats.append(float(coords[1]))
        else:
            for c in coords: _collect(c, depth - 1)
    depth_map = {"Point":0,"MultiPoint":1,"LineString":1,"MultiLineString":2,"Polygon":2,"MultiPolygon":3}
    for feat in geojson.get("features", []):
        geom = feat.get("geometry") or {}
        try: _collect(geom.get("coordinates", []), depth_map.get(geom.get("type",""), 2))
        except Exception: pass
    if not lats:
        return [-34.0, -74.0], [6.0, -28.0]
    return [min(lats), min(lons)], [max(lats), max(lons)]


def mapa_brasil(casos_uf: pd.DataFrame, metrica: str = "casos") -> folium.Map:
    """Mapa Folium do Brasil — para uso na página dedicada com st_folium."""
    geojson = _geo_estados()
    col = {"casos": "casos", "incidencia": "incidencia", "mortalidade": "mortalidade"}.get(metrica, "casos")
    data: dict[str, float] = {}
    if not casos_uf.empty and col in casos_uf.columns:
        data = dict(zip(casos_uf["uf_sigla"].astype(str), casos_uf[col].astype(float)))
    max_val = max(data.values(), default=1.0)
    cmap = _cmap_brasil(max_val)

    m = folium.Map(location=[-14.0, -51.0], zoom_start=4, tiles=None, prefer_canvas=True)
    folium.TileLayer(tiles=_CARTO_DARK, attr=_CARTO_ATTR, subdomains="abcd", max_zoom=18).add_to(m)

    def _style(feature):
        uf  = feature["properties"].get("uf", "")
        val = data.get(uf, 0.0)
        return {"fillColor": cmap(val) if val > 0 else "#1c2128",
                "fillOpacity": 0.85 if val > 0 else 0.5,
                "color": "#ffffff", "weight": 0.6, "opacity": 0.4}

    folium.GeoJson(
        geojson,
        style_function=_style,
        highlight_function=lambda x: {"fillOpacity": 1.0, "weight": 2.0, "color": "#ffffff"},
        tooltip=folium.GeoJsonTooltip(
            fields=["uf"], aliases=[""], labels=False, sticky=True,
            style="background:#1c2128;color:#f0f6fc;font-weight:bold;font-size:13px;padding:4px 10px;border-radius:6px;border:none;",
        ),
    ).add_to(m)
    return m


def _mapa_df(df: pd.DataFrame) -> folium.Map | None:
    """
    Mapa especial para o Distrito Federal:
    desenha as 35 Regiões Administrativas (OSM) mas mostra os dados
    do DF como um todo no tooltip — já que o SINAN não distingue RAs.
    """
    geojson = _geo_ras_df()
    if geojson is None or not geojson.get("features"):
        return None

    mask = df["estado_notificacao"].astype(str).map(UF_SIGLAS) == "DF"
    total_df  = int(mask.sum())
    df_uf     = df.loc[mask].copy()
    for col in df_uf.select_dtypes("category").columns:
        df_uf[col] = df_uf[col].astype(str)

    enc_col = "situacao_enc_norm" if "situacao_enc_norm" in df_uf.columns else "situacao_encerramento"

    def _pct(series, valor):
        total = len(series)
        return round(series.eq(valor).sum() / total * 100, 1) if total > 0 else 0.0

    cura_df     = _pct(df_uf[enc_col].astype(str), "Cura") if enc_col in df_uf.columns else 0.0
    abandono_df = _pct(df_uf[enc_col].astype(str), "Abandono") if enc_col in df_uf.columns else 0.0
    obitos_df   = _pct(df_uf[enc_col].astype(str), "Obito por TB") if enc_col in df_uf.columns else 0.0
    hiv_df      = _pct(df_uf["status_hiv"].astype(str), "Positivo") if "status_hiv" in df_uf.columns else 0.0

    # Mesma cor para todas as RAs — dados do DF inteiro
    import math
    cmap_df   = _cmap_estado(total_df)
    cor_unica = cmap_df(math.log1p(total_df))

    # Injeta propriedades nos features
    for feat in geojson["features"]:
        props = feat["properties"]
        props["CASOS"]    = f"{total_df:,}"
        props["CURA"]     = f"{cura_df:.1f}%"
        props["ABANDONO"] = f"{abandono_df:.1f}%"
        props["OBITOS"]   = f"{obitos_df:.1f}%"
        props["HIV"]      = f"{hiv_df:.1f}%"
    sw, ne = _bbox_geojson(geojson)
    center = [(sw[0] + ne[0]) / 2, (sw[1] + ne[1]) / 2]

    m = folium.Map(location=center, zoom_start=9, tiles=None, prefer_canvas=True)
    folium.TileLayer(tiles=_CARTO_DARK, attr=_CARTO_ATTR, subdomains="abcd", max_zoom=18).add_to(m)

    folium.GeoJson(
        geojson,
        style_function=lambda x: {
            "fillColor":    cor_unica,
            "fillOpacity":  0.80,
            "color":        "#ffffff",
            "weight":       0.8,
            "opacity":      0.6,
            "smoothFactor": 0,
        },
        highlight_function=lambda x: {"fillOpacity": 1.0, "weight": 2.0, "color": "#ffffff", "smoothFactor": 0},
        tooltip=folium.GeoJsonTooltip(
            fields=["RA_NOME", "CASOS", "CURA", "ABANDONO", "OBITOS", "HIV"],
            aliases=["📍 Região Adm.", "📊 Casos (DF)", "✅ Cura", "⚠️ Abandono", "💀 Óbitos TB", "🔴 HIV+"],
            labels=True, sticky=True,
            style="background:#1c2128;color:#f0f6fc;font-size:12px;padding:8px 12px;border-radius:6px;border:none;line-height:1.8;",
        ),
    ).add_to(m)
    m.fit_bounds([sw, ne])
    return m



def mapa_estado(df: pd.DataFrame, uf: str) -> folium.Map | None:
    """Mapa Folium dos municípios de um estado — para uso na página dedicada."""
    # Caso especial: DF usa Regiões Administrativas do OSM
    if uf == "DF":
        return _mapa_df(df)

    geojson = _geo_municipios(uf)
    if geojson is None or not geojson.get("features"):
        return None

    mask = df["estado_notificacao"].astype(str).map(UF_SIGLAS) == uf
    # converte categoricals para str para evitar erros de fillna/groupby
    df_uf = df.loc[mask].copy()
    for col in df_uf.select_dtypes("category").columns:
        df_uf[col] = df_uf[col].astype(str)

    # Agrega indicadores clínicos por município
    enc_col = "situacao_enc_norm" if "situacao_enc_norm" in df_uf.columns else "situacao_encerramento"

    def _pct(series, valor):
        total = len(series)
        return round(series.eq(valor).sum() / total * 100, 1) if total > 0 else 0.0

    agg = df_uf.groupby("municipio_notificacao", observed=True).size().reset_index(name="casos")
    agg["municipio_norm"] = agg["municipio_notificacao"].map(_norm)

    if enc_col in df_uf.columns:
        enc_grp = df_uf.groupby("municipio_notificacao", observed=True)[enc_col].agg(
            cura     = lambda x: _pct(x, "Cura"),
            abandono = lambda x: _pct(x, "Abandono"),
            obitos   = lambda x: _pct(x, "Obito por TB"),
        ).reset_index()
        agg = agg.merge(enc_grp, on="municipio_notificacao", how="left")
    else:
        agg["cura"] = agg["abandono"] = agg["obitos"] = 0.0

    if "status_hiv" in df_uf.columns:
        hiv_grp = df_uf.groupby("municipio_notificacao", observed=True)["status_hiv"].agg(
            hiv_pos=lambda x: _pct(x, "Positivo")
        ).reset_index()
        agg = agg.merge(hiv_grp, on="municipio_notificacao", how="left")
    else:
        agg["hiv_pos"] = 0.0

    agg[["cura", "abandono", "obitos", "hiv_pos"]] = (
        agg[["cura", "abandono", "obitos", "hiv_pos"]].fillna(0.0)
    )
    casos_map    = dict(zip(agg["municipio_norm"], agg["casos"]))
    cura_map     = dict(zip(agg["municipio_norm"], agg["cura"]))
    abandono_map = dict(zip(agg["municipio_norm"], agg["abandono"]))
    obitos_map   = dict(zip(agg["municipio_norm"], agg["obitos"]))
    hiv_map      = dict(zip(agg["municipio_norm"], agg["hiv_pos"]))

    # Injeta indicadores nos properties do GeoJSON para o tooltip
    data: dict[str, int] = {}
    for feat in geojson["features"]:
        props = feat["properties"]
        nm  = props.get("NM_MUN_NORM", _norm(props.get("NM_MUN", "")))
        cd  = str(props["CD_MUN"])
        val = casos_map.get(nm, 0)
        data[cd] = val
        props["CASOS"]    = f"{val:,}"
        props["CURA"]     = f"{cura_map.get(nm, 0):.1f}%"
        props["ABANDONO"] = f"{abandono_map.get(nm, 0):.1f}%"
        props["OBITOS"]   = f"{obitos_map.get(nm, 0):.1f}%"
        props["HIV"]      = f"{hiv_map.get(nm, 0):.1f}%"

    max_val = max(data.values(), default=1)
    cmap = _cmap_estado(max_val)

    sw, ne = _bbox_geojson(geojson)
    center = [(sw[0] + ne[0]) / 2, (sw[1] + ne[1]) / 2]

    m = folium.Map(location=center, zoom_start=6, tiles=None, prefer_canvas=True)
    folium.TileLayer(tiles=_CARTO_DARK, attr=_CARTO_ATTR, subdomains="abcd", max_zoom=18).add_to(m)

    def _style(feature):
        cd  = str(feature["properties"].get("CD_MUN", ""))
        val = data.get(cd, 0)
        cor = _cor_municipio(val, cmap, max_val)
        return {
            "fillColor":   cor,
            "fillOpacity": 0.93,
            "color":       "#5a4a3a",
            "weight":      1.0,
            "opacity":     0.8,
            "smoothFactor": 0,
            "lineJoin":    "round",
            "lineCap":     "round",
        }

    folium.GeoJson(
        geojson,
        style_function=_style,
        highlight_function=lambda x: {"fillOpacity": 1.0, "weight": 2.0, "color": "#ffffff", "smoothFactor": 0},
        tooltip=folium.GeoJsonTooltip(
            fields=["NM_MUN", "CASOS", "CURA", "ABANDONO", "OBITOS", "HIV"],
            aliases=["📍 Município", "📊 Casos", "✅ Cura", "⚠️ Abandono", "💀 Óbitos TB", "🔴 HIV+"],
            labels=True,
            sticky=True,
            style=(
                "background:#1c2128;color:#f0f6fc;font-size:12px;"
                "padding:8px 12px;border-radius:6px;border:none;line-height:1.8;"
            ),
        ),
    ).add_to(m)
    m.fit_bounds([sw, ne])
    return m


def render_html(m: folium.Map, height: int = 500) -> str:
    """HTML pronto para components.html (fallback se necessário)."""
    fig = folium.Figure(width="100%", height=f"{height}px")
    m.add_to(fig)
    return fig.render()


def extrair_uf_clicado(result: dict | None) -> str | None:
    """Extrai sigla UF do resultado do st_folium."""
    if not result:
        return None
    tooltip = result.get("last_object_clicked_tooltip") or ""
    match = re.search(r"\b([A-Z]{2})\b", str(tooltip))
    if match:
        uf = match.group(1)
        if uf in _UF_SET:
            return uf
    return None
