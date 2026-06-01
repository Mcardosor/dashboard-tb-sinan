"""
mapa_interativo.py — Mapas PyDeck com drill-down Brasil → Estado → Município.

PyDeck usa st.pydeck_chart() que é componente NATIVO do Streamlit.
Sem iframe, sem CDN dependente, sem token Mapbox.
Tiles: CARTO_DARK (funciona sem token).
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
import pydeck as pdk
import streamlit as st
from shapely.geometry import shape, mapping
from shapely.ops import orient

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


# ── Colorscale YlOrRd → RGBA ──────────────────────────────────────────────────
def _ylord_rgba(t: float, alpha: int = 210) -> list[int]:
    """Interpola YlOrRd de 0→1 e retorna [R,G,B,A]."""
    stops = [
        (0.00, (255, 255, 229)),
        (0.25, (253, 204, 138)),
        (0.50, (240, 100,  50)),
        (0.75, (209,  24,  24)),
        (1.00, (103,   0,  13)),
    ]
    for i in range(len(stops) - 1):
        t0, c0 = stops[i]
        t1, c1 = stops[i + 1]
        if t <= t1:
            f = (t - t0) / (t1 - t0)
            r = int(c0[0] + f * (c1[0] - c0[0]))
            g = int(c0[1] + f * (c1[1] - c0[1]))
            b = int(c0[2] + f * (c1[2] - c0[2]))
            return [r, g, b, alpha]
    return [103, 0, 13, alpha]


def _blues_rgba(t: float, alpha: int = 210) -> list[int]:
    """Interpola Blues de 0→1 e retorna [R,G,B,A]."""
    stops = [
        (0.00, (239, 243, 255)),
        (0.33, (107, 174, 214)),
        (0.66, ( 33, 113, 181)),
        (1.00, (  8,  48, 107)),
    ]
    for i in range(len(stops) - 1):
        t0, c0 = stops[i]
        t1, c1 = stops[i + 1]
        if t <= t1:
            f = (t - t0) / (t1 - t0)
            r = int(c0[0] + f * (c1[0] - c0[0]))
            g = int(c0[1] + f * (c1[1] - c0[1]))
            b = int(c0[2] + f * (c1[2] - c0[2]))
            return [r, g, b, alpha]
    return [8, 48, 107, alpha]


_DARK_FILL = [28, 33, 40, 120]  # #1c2128 para z=0


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


def _fix_winding(feature: dict) -> dict:
    """Normaliza winding order dos polígonos para CCW (padrão GeoJSON/deck.gl)."""
    try:
        geom = shape(feature["geometry"])
        if not geom.is_valid:
            geom = geom.buffer(0)
        geom = orient(geom, sign=1.0)  # exterior CCW, buracos CW
        feature = dict(feature)
        feature["geometry"] = mapping(geom)
    except Exception:
        pass
    return feature


# ── Mapa Brasil ───────────────────────────────────────────────────────────────
def deck_brasil(casos_uf: pd.DataFrame, metrica: str = "casos") -> pdk.Deck:
    """
    Retorna pdk.Deck com coroplético dos estados.
    Usar com st.pydeck_chart(deck, on_select='rerun').
    """
    col = {"casos": "casos", "incidencia": "incidencia", "mortalidade": "mortalidade"}.get(metrica, "casos")
    data: dict[str, float] = {}
    if not casos_uf.empty and col in casos_uf.columns:
        data = dict(zip(casos_uf["uf_sigla"].astype(str), casos_uf[col].astype(float)))
    max_val = max(data.values(), default=1.0)

    geojson = _geo_estados()
    # Adiciona fill_color e tooltip em cada feature
    features = []
    for feat in geojson.get("features", []):
        f = _fix_winding(json.loads(json.dumps(feat)))
        uf  = f["properties"].get("uf", "")
        val = data.get(uf, 0.0)
        t   = val / max_val if max_val > 0 else 0.0
        f["properties"]["fill_color"] = _ylord_rgba(t) if val > 0 else _DARK_FILL
        f["properties"]["tooltip"]    = f"{uf}\n{col.capitalize()}: {val:,.0f}"
        features.append(f)

    geo_data = {"type": "FeatureCollection", "features": features}

    layer = pdk.Layer(
        "GeoJsonLayer",
        data=geo_data,
        get_fill_color="properties.fill_color",
        get_line_color=[255, 255, 255, 80],
        line_width_min_pixels=1,
        pickable=True,
        auto_highlight=True,
        highlight_color=[255, 255, 255, 60],
        get_tooltip="properties.tooltip",
    )

    return pdk.Deck(
        layers=[layer],
        initial_view_state=pdk.ViewState(
            latitude=-14.0, longitude=-51.0,
            zoom=3.5, pitch=0, bearing=0,
        ),
        map_style=pdk.map_styles.CARTO_DARK,
        tooltip={"text": "{properties.tooltip}"},
    )


# ── Mapa Estado ───────────────────────────────────────────────────────────────
def deck_estado(df: pd.DataFrame, uf: str) -> pdk.Deck | None:
    """
    Retorna pdk.Deck com coroplético dos municípios do estado.
    """
    geojson = _geo_municipios(uf)
    if geojson is None or not geojson.get("features"):
        return None

    # Agrega casos por município
    mask = df["estado_notificacao"].astype(str).map(UF_SIGLAS) == uf
    agg = (
        df.loc[mask, "municipio_notificacao"]
        .astype(str).value_counts().reset_index()
        .rename(columns={"municipio_notificacao": "municipio", "count": "casos"})
    )
    agg["municipio_norm"] = agg["municipio"].map(_norm)
    casos_map: dict[str, int] = dict(zip(agg["municipio_norm"], agg["casos"]))

    max_val = max(casos_map.values(), default=1)

    # Bounding box para ViewState
    lats, lons = [], []
    features = []
    for feat in geojson.get("features", []):
        f = _fix_winding(json.loads(json.dumps(feat)))
        props = f["properties"]
        nm_norm = props.get("NM_MUN_NORM", _norm(props.get("NM_MUN", "")))
        val = casos_map.get(nm_norm, 0)
        t   = val / max_val if max_val > 0 else 0.0
        f["properties"]["fill_color"] = _blues_rgba(t) if val > 0 else _DARK_FILL
        f["properties"]["casos"]      = val
        f["properties"]["tooltip"]    = f"{props.get('NM_MUN', '')}\nCasos: {val:,}"
        features.append(f)

        # coleta coords para bbox
        try:
            coords = feat["geometry"]["coordinates"]
            tp = feat["geometry"]["type"]
            if tp == "Polygon":
                for pt in coords[0]:
                    lons.append(pt[0]); lats.append(pt[1])
            elif tp == "MultiPolygon":
                for poly in coords:
                    for pt in poly[0]:
                        lons.append(pt[0]); lats.append(pt[1])
        except Exception:
            pass

    geo_data = {"type": "FeatureCollection", "features": features}

    lat_c = (min(lats) + max(lats)) / 2 if lats else -14.0
    lon_c = (min(lons) + max(lons)) / 2 if lons else -51.0
    import math
    max_diff = max(max(lats) - min(lats), max(lons) - min(lons)) if lats else 10
    zoom = max(4.5, min(9.0, math.log2(360.0 / max(max_diff, 0.1)) + 1.0))

    layer = pdk.Layer(
        "GeoJsonLayer",
        data=geo_data,
        get_fill_color="properties.fill_color",
        get_line_color=[255, 255, 255, 60],
        line_width_min_pixels=1,
        pickable=True,
        auto_highlight=True,
        highlight_color=[255, 255, 255, 60],
    )

    return pdk.Deck(
        layers=[layer],
        initial_view_state=pdk.ViewState(
            latitude=lat_c, longitude=lon_c,
            zoom=zoom, pitch=0, bearing=0,
        ),
        map_style=pdk.map_styles.CARTO_DARK,
        tooltip={"text": "{properties.tooltip}"},
    )


# ── Extrai UF do evento pydeck ────────────────────────────────────────────────
_UF_SET = set(UF_SIGLAS.values())

def extrair_uf_pydeck(event) -> str | None:
    """Extrai sigla UF do evento on_select do st.pydeck_chart."""
    try:
        if not event or not event.selection:
            return None
        objects = event.selection.objects
        if not objects:
            return None
        for layer_objects in objects.values():
            if layer_objects:
                props = layer_objects[0].get("properties", {})
                tooltip = props.get("tooltip", "")
                uf = str(tooltip).split("\n")[0].strip()
                if uf in _UF_SET:
                    return uf
    except Exception:
        pass
    return None


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


def mapa_estado(df: pd.DataFrame, uf: str) -> folium.Map | None:
    """Mapa Folium dos municípios de um estado — para uso na página dedicada."""
    geojson = _geo_municipios(uf)
    if geojson is None or not geojson.get("features"):
        return None

    mask = df["estado_notificacao"].astype(str).map(UF_SIGLAS) == uf
    agg = (df.loc[mask, "municipio_notificacao"].astype(str)
             .value_counts().reset_index()
             .rename(columns={"municipio_notificacao": "municipio", "count": "casos"}))
    agg["municipio_norm"] = agg["municipio"].map(_norm)
    casos_map = dict(zip(agg["municipio_norm"], agg["casos"]))

    data: dict[str, int] = {}
    for feat in geojson["features"]:
        props = feat["properties"]
        nm    = props.get("NM_MUN_NORM", _norm(props.get("NM_MUN", "")))
        data[str(props["CD_MUN"])] = casos_map.get(nm, 0)

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
            "smoothFactor": 0,          # sem simplificação → elimina gaps
            "lineJoin":    "round",
            "lineCap":     "round",
        }

    folium.GeoJson(
        geojson,
        style_function=_style,
        highlight_function=lambda x: {"fillOpacity": 1.0, "weight": 2.0, "color": "#ffffff", "smoothFactor": 0},
        tooltip=folium.GeoJsonTooltip(
            fields=["NM_MUN"], aliases=[""], labels=False, sticky=True,
            style="background:#1c2128;color:#f0f6fc;font-size:12px;padding:3px 8px;border-radius:5px;border:none;",
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
