"""
dados.py
────────
Funções de carregamento e cache dos dados do dashboard.
Usa st.cache_data para evitar releituras desnecessárias entre interações.
"""

import json
import streamlit as st
import pandas as pd
import pygwalker as pyg
from pathlib import Path

from src.constantes import GEOJSON_PATH


@st.cache_data(show_spinner="Carregando dados...")
def carregar_dados(path: str) -> pd.DataFrame:
    """Lê o Parquet tratado do ano selecionado."""
    return pd.read_parquet(path)


@st.cache_data(show_spinner=False)
def carregar_geojson() -> dict:
    """Carrega o GeoJSON dos estados brasileiros."""
    if not GEOJSON_PATH.exists():
        raise FileNotFoundError(f"GeoJSON nao encontrado em {GEOJSON_PATH}")
    with open(GEOJSON_PATH, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def selecionar_colunas(df: pd.DataFrame, colunas: tuple) -> pd.DataFrame:
    """Filtra apenas as colunas existentes no DataFrame."""
    return df[[c for c in colunas if c in df.columns]]


@st.cache_data(show_spinner="Preparando analise livre...")
def gerar_html_pygwalker(df: pd.DataFrame, spec_path: str | None = None) -> str:
    """Gera o HTML do PyGWalker, opcionalmente com spec pre-configurado."""
    kwargs: dict = {"appearance": "dark"}
    if spec_path and Path(spec_path).exists():
        kwargs["spec"] = spec_path
    return pyg.to_html(df, **kwargs)
