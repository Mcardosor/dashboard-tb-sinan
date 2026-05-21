"""
banco.py
────────
Engine DuckDB sobre os Parquets tratados.

Estratégia: cada chamada abre uma conexão DuckDB própria (thread-safe).
O cache fica no nível do resultado (DataFrame), via @st.cache_data em dados.py.

Por que DuckDB?
  - Leitura colunar paralela — só carrega as colunas usadas
  - Filtros pushdown — só lê as linhas que passam no WHERE
  - union_by_name — lida automaticamente com colunas ausentes em anos antigos
  - Sem CREATE VIEW: read_parquet() inline é ~15% mais rápido por query
"""

from pathlib import Path
import duckdb
import pandas as pd

from src.constantes import PASTA_DADOS


def _glob() -> str:
    """Glob dos Parquets tratados (forward slashes para DuckDB em qualquer OS)."""
    return (PASTA_DADOS / "sinan_tube_*_tratado.parquet").as_posix()


def query(sql: str, params: list | None = None) -> pd.DataFrame:
    """
    Executa SQL sobre todos os Parquets tratados e retorna um DataFrame.
    Thread-safe: cada chamada usa sua própria conexão DuckDB em memória.

    A função read_parquet() é injetada diretamente no SQL como CTE,
    evitando o custo de registrar uma VIEW separada.

    Exemplo:
        query(
            "SELECT * FROM sinan WHERE CAST(ano_notificacao AS VARCHAR) IN (?, ?)",
            ["2024", "2025"]
        )
    """
    glob = _glob()
    # Envolve o SQL do chamador em um CTE que expõe 'sinan' como nome de tabela
    wrapped = f"""
        WITH sinan AS (
            SELECT * FROM read_parquet('{glob}', union_by_name = true)
        )
        {sql}
    """
    with duckdb.connect() as con:
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
