"""
dados.py
--------
Funcoes de carregamento e cache dos dados do dashboard.
"""

import copy
import json
import requests
import streamlit as st
import pandas as pd
from io import StringIO
from pathlib import Path

from src.constantes import (
    GEOJSON_PATH, HIST_MENSAL, HIST_ESTADUAL, HIST_ANUAL,
    MUN_PARQUET, MUN_URL, UF_SIGLAS, COLUNAS_ANALISE,
    NORMALIZAR_DESFECHO,
)


@st.cache_data(show_spinner="Carregando dados...")
def carregar_dados(anos: tuple) -> pd.DataFrame:
    """
    Carrega os dados de um ou mais anos via DuckDB (max. 3 anos).
    anos: tupla ordenada de inteiros, ex: (2022,) ou (2022, 2023, 2024)
    Leitura colunar: so as colunas usadas pelo dashboard (COLUNAS_DASHBOARD)
    cache_data: resultado cacheado pela combinacao de anos
    """
    from src.banco import query
    anos_literais = ", ".join(f"'{a}'" for a in anos)
    return query(
        f"SELECT * FROM sinan WHERE CAST(ano_notificacao AS VARCHAR) IN ({anos_literais})"
    )


@st.cache_resource(show_spinner=False)
def carregar_geojson() -> dict:
    """Carrega o GeoJSON dos estados brasileiros (leitura unica)."""
    if not GEOJSON_PATH.exists():
        raise FileNotFoundError(f"GeoJSON nao encontrado em {GEOJSON_PATH}")
    with open(GEOJSON_PATH, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def geojson_enriquecido(casos_uf: pd.DataFrame) -> dict:
    """
    Retorna uma copia do GeoJSON com casos/incidencia/mortalidade injetados.
    Cacheado por casos_uf: so refaz o deepcopy quando os dados mudam.
    Evita deepcopy a cada rerun do Streamlit (operacao O(n) no GeoJSON inteiro).
    """
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
            feat["properties"]["casos"]       = 0
            feat["properties"]["incidencia"]  = 0.0
            feat["properties"]["mortalidade"] = 0.0
    return gj


def selecionar_colunas(df: pd.DataFrame, colunas: tuple) -> pd.DataFrame:
    """Filtra apenas as colunas existentes no DataFrame."""
    return df[[c for c in colunas if c in df.columns]]


def render_pygwalker(df: pd.DataFrame, spec_path: str | None = None) -> None:
    """Renderiza o PyGWalker diretamente no Streamlit (API 0.4+)."""
    try:
        from pygwalker.api.streamlit import StreamlitRenderer
        kwargs: dict = {"appearance": "dark", "spec": spec_path} if (spec_path and Path(spec_path).exists()) else {"appearance": "dark"}
        renderer = StreamlitRenderer(df, **kwargs)
        renderer.explorer()
    except ImportError:
        try:
            import pygwalker as pyg
            import streamlit.components.v1 as components
            html = pyg.to_html(df, appearance="dark")
            components.html(html, height=1000, scrolling=True)
        except Exception as e:
            st.error(f"PyGWalker indisponivel: {e}")


def enriquecer_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adiciona colunas derivadas ao DataFrame para uso nos dashboards.
    Nao usa cache pois recebe df ja filtrado.
    """
    df = df.copy()

    if "estado_notificacao" in df.columns:
        df["uf_sigla"] = (
            df["estado_notificacao"].astype(str)
            .map(UF_SIGLAS)
            .fillna("?")
        )

    if "situacao_encerramento" in df.columns:
        df["situacao_enc_norm"] = (
            df["situacao_encerramento"].astype(str)
            .map(lambda x: NORMALIZAR_DESFECHO.get(x, x))
        )

    if "data_notificacao" in df.columns:
        try:
            dts = pd.to_datetime(df["data_notificacao"], errors="coerce")
            df["mes_num"] = dts.dt.month
        except Exception:
            df["mes_num"] = None

    return df


@st.cache_data(show_spinner="Carregando historico...")
def load_historico() -> dict | None:
    """Carrega os CSVs pre-agregados de historico. Retorna dict ou None."""
    paths = {
        "mensal":   HIST_MENSAL,
        "estadual": HIST_ESTADUAL,
        "anual":    HIST_ANUAL,
    }
    if not all(p.exists() for p in paths.values()):
        return None
    try:
        return {k: pd.read_csv(str(v)) for k, v in paths.items()}
    except Exception:
        return None


@st.cache_resource(show_spinner="Carregando coordenadas dos municipios...")
def load_municipios() -> pd.DataFrame:
    """Carrega coordenadas dos municipios (local ou download)."""
    if MUN_PARQUET.exists():
        return pd.read_parquet(str(MUN_PARQUET))
    try:
        r = requests.get(MUN_URL, timeout=15)
        r.raise_for_status()
        mun = pd.read_csv(StringIO(r.text))
        mun["codigo_6"] = mun["codigo_ibge"].astype(str).str[:6]
        return mun[["codigo_6", "nome", "latitude", "longitude"]]
    except Exception:
        return pd.DataFrame(columns=["codigo_6", "nome", "latitude", "longitude"])
