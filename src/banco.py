"""
banco.py
────────
Engine DuckDB sobre os Parquets tratados.

Estrategia: cada chamada abre uma conexao DuckDB propria (thread-safe).
O cache fica no nivel do resultado (DataFrame), via @st.cache_data em dados.py.

Por que DuckDB?
  - Leitura colunar paralela — so carrega as colunas usadas
  - Filtros pushdown — so le as linhas que passam no WHERE
  - union_by_name — lida automaticamente com colunas ausentes em anos antigos
  - Nenhuma migracao de dados necessaria — usa os Parquets existentes
"""

import duckdb
import pandas as pd
from pathlib import Path

from src.constantes import PASTA_DADOS


def _glob() -> str:
    """Retorna o padrao glob dos Parquets tratados (forward slashes para DuckDB)."""
    return (PASTA_DADOS / "sinan_tube_*_tratado.parquet").as_posix()


def query(sql: str, params: list | None = None) -> pd.DataFrame:
    """
    Executa SQL sobre a view 'sinan' (todos os anos) e retorna um DataFrame.
    Thread-safe: cada chamada usa sua propria conexao DuckDB em memoria.

    Exemplo:
        query("SELECT * FROM sinan WHERE CAST(ano_notificacao AS VARCHAR) = ?", ["2025"])
    """
    with duckdb.connect() as con:
        con.execute(f"""
            CREATE VIEW sinan AS
            SELECT * FROM read_parquet('{_glob()}', union_by_name = true)
        """)
        return con.execute(sql, params or []).df()


def anos_no_banco() -> list[int]:
    """Retorna lista de anos com Parquet tratado disponivel, do mais recente ao mais antigo."""
    return sorted(
        [
            int(p.stem.split("_")[2])
            for p in PASTA_DADOS.glob("sinan_tube_*_tratado.parquet")
        ],
        reverse=True,
    )
