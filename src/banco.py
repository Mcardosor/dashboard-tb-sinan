"""
banco.py
────────
Engine DuckDB sobre os Parquets tratados.

Estratégia: cada chamada abre uma conexão DuckDB própria (thread-safe).
O cache fica no nível do resultado (DataFrame), via @st.cache_data em dados.py.

Otimizações:
  - SELECT com colunas específicas (não SELECT *) — 44% menos dados lidos
  - SET threads para paralelismo máximo na leitura colunar
  - read_parquet() inline como CTE — sem CREATE VIEW separado
"""

from pathlib import Path
import os
import duckdb
import pandas as pd

from src.constantes import PASTA_DADOS, COLUNAS_DASHBOARD


def _glob() -> str:
    """Glob dos Parquets tratados (forward slashes para DuckDB em qualquer OS)."""
    return (PASTA_DADOS / "sinan_tube_*_tratado.parquet").as_posix()


def _threads() -> int:
    """Número de threads para DuckDB — usa todos os CPUs disponíveis (max 8)."""
    return min(os.cpu_count() or 2, 8)


def query(sql: str, params: list | None = None) -> pd.DataFrame:
    """
    Executa SQL sobre todos os Parquets tratados e retorna um DataFrame.
    Thread-safe: cada chamada usa sua própria conexão DuckDB em memória.

    O SQL do chamador deve referenciar a tabela como 'sinan' — ela é
    injetada como CTE com apenas as colunas necessárias ao dashboard.
    """
    glob = _glob()
    cols = ", ".join(COLUNAS_DASHBOARD)
    wrapped = f"""
        WITH sinan AS (
            SELECT {cols}
            FROM read_parquet('{glob}', union_by_name = true)
        )
        {sql}
    """
    with duckdb.connect() as con:
        con.execute(f"SET threads = {_threads()}")
        return con.execute(wrapped, params or []).df()


def query_all_cols(sql: str, params: list | None = None) -> pd.DataFrame:
    """
    Igual a query() mas com SELECT * — usado pela aba Análise Livre (PyGWalker).
    Só deve ser chamado para anos individuais (a carga é maior).
    """
    glob = _glob()
    wrapped = f"""
        WITH sinan AS (
            SELECT * FROM read_parquet('{glob}', union_by_name = true)
        )
        {sql}
    """
    with duckdb.connect() as con:
        con.execute(f"SET threads = {_threads()}")
        return con.execute(wrapped, params or []).df()


def anos_no_banco() -> list[int]:
    """Retorna anos com Parquet tratado disponível, do mais recente ao mais antigo."""
    return sorted(
        [
            int(p.stem.split("_")[2])
            for p in PASTA_DADOS.glob("sinan_tube_*_tratado.parquet")
        ],
        reverse=True,
    )
