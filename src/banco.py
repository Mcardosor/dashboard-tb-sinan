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
  - Colunas string reconvertidas para category após carga (~60% menos RAM)
"""

from pathlib import Path
import os
import duckdb
import pandas as pd

from src.constantes import PASTA_DADOS, COLUNAS_DASHBOARD

# Colunas de baixa cardinalidade que voltam como object do DuckDB — reconverter
# para category economiza ~60% de memória nessas colunas.
_COLUNAS_CATEGORIA = (
    "estado_notificacao", "uf_residencia", "municipio_notificacao", "municipio_residencia",
    "sexo", "raca_cor", "escolaridade",
    "tipo_entrada", "forma", "extrapulmonar",
    "situacao_encerramento",
    "status_hiv", "uso_antirretroviral", "raio_x_torax", "teste_tuberculinico",
    "baciloscopia_primeira_amostra", "cultura_escarro", "histopatologia",
    "teste_molecular", "teste_sensibilidade", "tratamento_supervisionado",
    "baciloscopia_mes_1", "baciloscopia_mes_2", "baciloscopia_mes_3",
    "baciloscopia_mes_4", "baciloscopia_mes_5", "baciloscopia_mes_6",
    "baciloscopia_apos_6_meses",
    "agravo_aids", "agravo_alcoolismo", "agravo_diabetes",
    "agravo_doenca_mental", "agravo_drogas_ilicitas", "agravo_tabagismo", "agravo_outros",
    "populacao_privada_liberdade", "populacao_situacao_rua",
    "profissional_saude", "populacao_imigrante", "beneficiario_governo",
    "tipo_notificacao",
)


def _aplicar_categorias(df: pd.DataFrame) -> pd.DataFrame:
    """Reconverte colunas string para category após carga do DuckDB."""
    for col in _COLUNAS_CATEGORIA:
        if col in df.columns and df[col].dtype == object:
            df[col] = df[col].astype("category")
    return df


def _glob() -> str:
    """Glob dos Parquets tratados (forward slashes para DuckDB em qualquer OS)."""
    return (PASTA_DADOS / "tuberculose_*_tratado.parquet").as_posix()


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
            for p in PASTA_DADOS.glob("tuberculose_*_tratado.parquet")
        ],
        reverse=True,
    )
