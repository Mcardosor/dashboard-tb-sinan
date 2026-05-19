"""
dados.py
────────
Funções de carregamento e cache dos dados do dashboard.

Convenções de cache:
  @st.cache_resource — objetos grandes compartilhados (DataFrame, GeoJSON).
                        Retorna o mesmo objeto na memória; não faz cópia.
                        Correto para dados que nunca são mutados in-place.
  @st.cache_data     — objetos pequenos ou que precisam de cópia por segurança.
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.constantes import GEOJSON_PATH


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


@st.cache_data(
    show_spinner="Preparando analise livre...",
    hash_funcs={pd.DataFrame: lambda df: (df.shape, df.columns.tolist())},
)
def gerar_html_pygwalker(df: pd.DataFrame, spec_path: str | None = None) -> str:
    """
    Gera o HTML do PyGWalker com spec opcional.
    hash_funcs evita hashing completo do DataFrame (usa shape + colunas).
    """
    import pygwalker as pyg  # lazy import — biblioteca pesada, so usada aqui

    kwargs: dict = {"appearance": "dark"}
    if spec_path and Path(spec_path).exists():
        kwargs["spec"] = spec_path
    return pyg.to_html(df, **kwargs)
