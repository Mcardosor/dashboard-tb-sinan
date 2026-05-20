"""
dados.py
────────
Funções de carregamento e cache dos dados do dashboard.
"""

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


@st.cache_resource(show_spinner="Carregando dados...")
def carregar_dados(path: str) -> pd.DataFrame:
    """
    Lê o Parquet tratado e mantém um único objeto em memória.
    cache_resource evita a cópia que cache_data faria a cada interação.
    """
    return pd.read_parquet(path)


@st.cache_resource(show_spinner=False)
def carregar_geojson() -> dict:
    """Carrega o GeoJSON dos estados brasileiros (leitura única)."""
    if not GEOJSON_PATH.exists():
        raise FileNotFoundError(f"GeoJSON nao encontrado em {GEOJSON_PATH}")
    with open(GEOJSON_PATH, encoding="utf-8") as f:
        return json.load(f)


def selecionar_colunas(df: pd.DataFrame, colunas: tuple) -> pd.DataFrame:
    """
    Filtra apenas as colunas existentes no DataFrame.
    Sem cache: hashing de DataFrame é O(n*m) e mais caro que a operação.
    """
    return df[[c for c in colunas if c in df.columns]]


def render_pygwalker(df: pd.DataFrame, spec_path: str | None = None) -> None:
    """Renderiza o PyGWalker diretamente no Streamlit (API 0.4+)."""
    try:
        from pygwalker.api.streamlit import StreamlitRenderer
        kwargs: dict = {"appearance": "dark", "spec": spec_path} if (spec_path and Path(spec_path).exists()) else {"appearance": "dark"}
        renderer = StreamlitRenderer(df, **kwargs)
        renderer.explorer()
    except ImportError:
        # fallback para versões antigas
        try:
            import pygwalker as pyg
            import streamlit.components.v1 as components
            html = pyg.to_html(df, appearance="dark")
            components.html(html, height=1000, scrolling=True)
        except Exception as e:
            st.error(f"PyGWalker indisponível: {e}")


def enriquecer_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adiciona colunas derivadas ao DataFrame para uso nos dashboards.
    Não usa cache pois recebe df já filtrado.
    """
    df = df.copy()

    # uf_sigla: mapa de nome do estado → sigla
    if "estado_notificacao" in df.columns:
        df["uf_sigla"] = (
            df["estado_notificacao"].astype(str)
            .map(UF_SIGLAS)
            .fillna("?")
        )

    # situacao_enc_norm: desfechos normalizados (sem acentos)
    if "situacao_encerramento" in df.columns:
        df["situacao_enc_norm"] = (
            df["situacao_encerramento"].astype(str)
            .map(lambda x: NORMALIZAR_DESFECHO.get(x, x))
        )

    # mes_num / data de notificação
    if "data_notificacao" in df.columns:
        try:
            dts = pd.to_datetime(df["data_notificacao"], errors="coerce")
            df["mes_num"] = dts.dt.month
        except Exception:
            df["mes_num"] = None

    return df


@st.cache_data(show_spinner="Carregando histórico...")
def load_historico() -> dict | None:
    """Carrega os CSVs pré-agregados de histórico. Retorna dict ou None."""
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


@st.cache_resource(show_spinner="Carregando coordenadas dos municípios...")
def load_municipios() -> pd.DataFrame:
    """Carrega coordenadas dos municípios (local ou download)."""
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
