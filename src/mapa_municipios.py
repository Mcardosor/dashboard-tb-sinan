"""
mapa_municipios.py
──────────────────
Cria o mapa Folium de municípios para o drill-down por estado.

Fluxo:
  1. Carrega o GeoJSON do estado (salvo por scripts/baixar_geojson_municipios.py)
  2. Carrega o mapeamento código-IBGE → nome do município
  3. Agrega os casos do DataFrame filtrado por município
  4. Retorna um folium.Map com choropleth + tooltip interativo

Dependências: folium, requests (já no requirements.txt)
"""

import json
import unicodedata
from pathlib import Path

import folium
import pandas as pd
import requests
import streamlit as st

# ── Caminhos ───────────────────────────────────────────────────────────────────
PASTA_MUNICIPIOS = Path("dados_dashboard") / "municipios"

# ── Mapeamento UF → código numérico IBGE ──────────────────────────────────────
IBGE_UF_CODES: dict[str, int] = {
    "AC": 12, "AL": 27, "AP": 16, "AM": 13, "BA": 29, "CE": 23,
    "DF": 53, "ES": 32, "GO": 52, "MA": 21, "MT": 51, "MS": 50,
    "MG": 31, "PA": 15, "PB": 25, "PR": 41, "PE": 26, "PI": 22,
    "RJ": 33, "RN": 24, "RS": 43, "RO": 11, "RR": 14, "SC": 42,
    "SP": 35, "SE": 28, "TO": 17,
}

# Coordenadas centrais aproximadas por estado (lat, lon, zoom)
CENTROIDES_UF: dict[str, tuple[float, float, int]] = {
    "AC": (-9.02,  -70.81, 6),  "AL": (-9.57,  -36.78, 7),
    "AP": ( 1.41,  -51.77, 6),  "AM": (-3.47,  -65.10, 5),
    "BA": (-12.96, -41.70, 6),  "CE": (-5.20,  -39.53, 7),
    "DF": (-15.78, -47.93, 9),  "ES": (-19.19, -40.34, 7),
    "GO": (-15.83, -49.84, 6),  "MA": (-5.42,  -45.44, 6),
    "MT": (-12.64, -55.42, 6),  "MS": (-20.51, -54.54, 6),
    "MG": (-18.51, -44.55, 6),  "PA": (-3.79,  -52.48, 5),
    "PB": (-7.28,  -36.72, 7),  "PR": (-24.89, -51.55, 6),
    "PE": (-8.81,  -36.95, 7),  "PI": (-7.72,  -42.73, 6),
    "RJ": (-22.25, -42.66, 7),  "RN": (-5.81,  -36.59, 7),
    "RS": (-30.03, -53.23, 6),  "RO": (-10.83, -63.34, 6),
    "RR": ( 1.99,  -61.33, 6),  "SC": (-27.45, -50.95, 7),
    "SP": (-22.29, -48.44, 6),  "SE": (-10.57, -37.45, 8),
    "TO": (-10.18, -48.33, 6),
}


def _normalizar(texto: str) -> str:
    """Remove acentos e converte para minúsculas para matching robusto."""
    return unicodedata.normalize("NFD", str(texto)).encode("ascii", "ignore").decode().lower().strip()


@st.cache_data(show_spinner=False, ttl=86400)
def _carregar_geojson_municipios(uf: str) -> dict | None:
    """
    Carrega o GeoJSON de municípios do estado.
    Tenta primeiro o arquivo local; se não existir, baixa da API do IBGE.
    """
    path = PASTA_MUNICIPIOS / f"{uf}_geojson.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    # Fallback: baixa direto da API (requer internet)
    cod = IBGE_UF_CODES.get(uf)
    if cod is None:
        return None
    url = (
        f"https://servicodados.ibge.gov.br/api/v3/malhas/estados/{cod}"
        f"?formato=application/vnd.geo+json&resolucao=5"
    )
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        # Salva para próximas chamadas
        PASTA_MUNICIPIOS.mkdir(parents=True, exist_ok=True)
        path.write_text(r.text, encoding="utf-8")
        return r.json()
    except Exception:
        return None


@st.cache_data(show_spinner=False, ttl=86400)
def _carregar_nomes_municipios(uf: str) -> dict[str, str]:
    """
    Retorna dicionário {codarea (str): nome_municipio}.
    Tenta arquivo local primeiro; fallback via API do IBGE.
    """
    path = PASTA_MUNICIPIOS / f"{uf}_nomes.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    url = (
        f"https://servicodados.ibge.gov.br/api/v1/localidades"
        f"/estados/{uf}/municipios"
    )
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        nomes = {str(m["id"]): m["nome"] for m in r.json()}
        PASTA_MUNICIPIOS.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(nomes, ensure_ascii=False, indent=2), encoding="utf-8")
        return nomes
    except Exception:
        return {}


def criar_mapa_municipios(df: pd.DataFrame, uf: str) -> folium.Map | None:
    """
    Cria um folium.Map choroplético com os casos de TB por município do estado.

    Parâmetros
    ----------
    df  : DataFrame já filtrado (pelo menos com coluna 'municipio_notificacao')
    uf  : Sigla do estado (ex: 'SP')

    Retorna
    -------
    folium.Map ou None se não houver dados suficientes.
    """
    if "municipio_notificacao" not in df.columns:
        return None

    geojson = _carregar_geojson_municipios(uf)
    if geojson is None:
        return None

    nomes_por_cod: dict[str, str] = _carregar_nomes_municipios(uf)

    # ── Enriquece o GeoJSON com o nome do município ────────────────────────────
    # A feature property 'codarea' é o código IBGE de 7 dígitos
    for feat in geojson.get("features", []):
        cod = feat["properties"].get("codarea", "")
        feat["properties"]["nome_municipio"] = nomes_por_cod.get(cod, cod)

    # ── Contagem de casos por município ───────────────────────────────────────
    contagem = (
        df["municipio_notificacao"].astype(str)
        .value_counts().reset_index()
        .rename(columns={"municipio_notificacao": "municipio", "count": "casos"})
    )
    contagem["norm"] = contagem["municipio"].map(_normalizar)

    # Índice de nome normalizado → casos (para join rápido)
    casos_por_norm: dict[str, int] = dict(
        zip(contagem["norm"], contagem["casos"])
    )

    # Agrega casos no GeoJSON via campo calculado
    for feat in geojson["features"]:
        nome = feat["properties"]["nome_municipio"]
        feat["properties"]["casos"] = casos_por_norm.get(_normalizar(nome), 0)

    # ── Configura o mapa ───────────────────────────────────────────────────────
    lat, lon, zoom = CENTROIDES_UF.get(uf, (-14.24, -51.93, 4))
    m = folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        prefer_canvas=True,
    )

    folium.Choropleth(
        geo_data=geojson,
        data=contagem,
        columns=["municipio", "casos"],
        key_on="feature.properties.nome_municipio",
        fill_color="YlOrRd",
        fill_opacity=0.8,
        line_opacity=0.3,
        line_color="#ffffff",
        nan_fill_color="rgba(40,40,60,0.4)",
        nan_fill_opacity=0.4,
        legend_name="Notificações de TB",
        highlight=True,
    ).add_to(m)

    # ── Tooltip interativo ────────────────────────────────────────────────────
    tooltip = folium.GeoJsonTooltip(
        fields=["nome_municipio", "casos"],
        aliases=["Município:", "Notificações:"],
        localize=True,
        sticky=False,
        labels=True,
        style=(
            "background-color: rgba(20,20,35,0.95);"
            "color: #f1f5f9;"
            "font-family: 'Inter', sans-serif;"
            "font-size: 13px;"
            "border-radius: 6px;"
            "border: 1px solid rgba(255,255,255,0.15);"
            "padding: 8px 12px;"
        ),
    )
    folium.GeoJson(
        geojson,
        style_function=lambda feat: {
            "fillOpacity": 0,
            "weight": 0,
        },
        tooltip=tooltip,
        highlight_function=lambda feat: {
            "fillColor": "#facc15",
            "fillOpacity": 0.4,
            "weight": 2,
            "color": "#facc15",
        },
    ).add_to(m)

    return m
