"""
gerar_historico.py
------------------
Le todos os Parquets _tratado em dados_dashboard/ e gera 4 CSVs
pre-agregados para a aba de Tendencias. Minusculos, carregam instantaneo.

  historico_mensal.csv      — casos por nu_ano x mes_num
  historico_estadual.csv    — casos por nu_ano x uf_sigla
  historico_anual.csv       — total de casos por nu_ano
  historico_indicadores.csv — taxas percentuais por nu_ano

Uso:
    python scripts/gerar_historico.py
    python scripts/gerar_historico.py 2022 2025
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import pyarrow.parquet as pq
from src.constantes import PASTA_DADOS, UF_SIGLAS

# ── CLI ───────────────────────────────────────────────────────────────────────
args = sys.argv[1:]
if len(args) == 0:
    ano_ini, ano_fim = 2001, 2025
elif len(args) == 1:
    ano_ini = ano_fim = int(args[0])
elif len(args) == 2:
    ano_ini, ano_fim = int(args[0]), int(args[1])
else:
    print("Uso: python gerar_historico.py [ano_inicio] [ano_fim]")
    sys.exit(1)

# ── Descobre arquivos disponiveis ─────────────────────────────────────────────
arquivos = {}
for ano in range(ano_ini, ano_fim + 1):
    p = PASTA_DADOS / f"sinan_tube_{ano}_tratado.parquet"
    if p.exists():
        arquivos[ano] = p

if not arquivos:
    print(f"Nenhum parquet tratado encontrado para {ano_ini}-{ano_fim}.")
    sys.exit(1)

print(f"Processando {len(arquivos)} ano(s)...\n")

# Colunas que queremos (pode faltar em anos antigos)
COLUNAS_QUERER = [
    "ano_notificacao", "estado_notificacao", "data_notificacao",
    "situacao_encerramento", "status_hiv", "tipo_entrada", "forma",
    "agravo_aids", "agravo_alcoolismo", "agravo_diabetes",
    "agravo_drogas_ilicitas", "agravo_tabagismo", "agravo_doenca_mental",
    "populacao_privada_liberdade", "populacao_situacao_rua",
]

# ── Carrega ano a ano — so colunas existentes ─────────────────────────────────
inicio = time.time()
dfs = []

for ano, path in sorted(arquivos.items()):
    # descobre schema sem carregar dados
    schema_cols = pq.read_schema(path).names
    cols = [c for c in COLUNAS_QUERER if c in schema_cols]

    df_ano = pd.read_parquet(path, columns=cols)
    df_ano["nu_ano"] = ano   # garante coluna com nome padrao
    dfs.append(df_ano)
    print(f"  {ano}: {len(df_ano):,} registros")

df = pd.concat(dfs, ignore_index=True)
print(f"\nTotal: {len(df):,} registros em {time.time()-inicio:.1f}s\n")

# Converte categorias para string (groupby mais rapido e seguro)
for col in df.select_dtypes("category").columns:
    df[col] = df[col].astype(str)

# Sigla UF
if "estado_notificacao" in df.columns:
    df["uf_sigla"] = df["estado_notificacao"].map(UF_SIGLAS).fillna("?")

# Mes de notificacao
if "data_notificacao" in df.columns:
    df["mes_num"] = pd.to_datetime(df["data_notificacao"], errors="coerce").dt.month

# ── 1. Mensal ─────────────────────────────────────────────────────────────────
print("[1/4] historico_mensal.csv...")
if "mes_num" in df.columns:
    mensal = (
        df.dropna(subset=["mes_num"])
        .groupby(["nu_ano", "mes_num"])
        .size()
        .reset_index(name="casos")
    )
    mensal["mes_num"] = mensal["mes_num"].astype(int)
    mensal.to_csv(PASTA_DADOS / "historico_mensal.csv", index=False)
    print(f"      {len(mensal)} linhas")

# ── 2. Estadual ───────────────────────────────────────────────────────────────
print("[2/4] historico_estadual.csv...")
if "uf_sigla" in df.columns:
    estadual = (
        df[df["uf_sigla"] != "?"]
        .groupby(["nu_ano", "uf_sigla"])
        .size()
        .reset_index(name="casos")
    )
    estadual.to_csv(PASTA_DADOS / "historico_estadual.csv", index=False)
    print(f"      {len(estadual)} linhas")

# ── 3. Anual ──────────────────────────────────────────────────────────────────
print("[3/4] historico_anual.csv...")
anual = df.groupby("nu_ano").size().reset_index(name="casos")
anual.to_csv(PASTA_DADOS / "historico_anual.csv", index=False)
print(f"      {len(anual)} linhas")

# ── 4. Indicadores ────────────────────────────────────────────────────────────
print("[4/4] historico_indicadores.csv...")

def _sim(s): return s.astype(str).str.strip().str.lower() == "sim"

col = lambda c: df[c] if c in df.columns else pd.Series(False, index=df.index)

df["_hiv"]    = col("status_hiv").astype(str).str.strip().str.lower() == "positivo"
df["_cura"]   = col("situacao_encerramento").astype(str).str.strip() == "Cura"
df["_aband"]  = col("situacao_encerramento").astype(str).str.strip().isin(
                    ["Abandono", "Abandono Primario", "Abandono Primario"])
df["_obito"]  = col("situacao_encerramento").astype(str).str.strip().isin(
                    ["Obito por TB", "Obito por TB"])
df["_novo"]   = col("tipo_entrada").astype(str).str.strip() == "Caso Novo"
df["_pulm"]   = col("forma").astype(str).str.strip() == "Pulmonar"
df["_aids"]   = _sim(col("agravo_aids"))
df["_alcool"] = _sim(col("agravo_alcoolismo"))
df["_rua"]    = _sim(col("populacao_situacao_rua"))
df["_liber"]  = _sim(col("populacao_privada_liberdade"))

ind = df.groupby("nu_ano").agg(
    total   =("nu_ano",  "count"),
    hiv_pos =("_hiv",   "sum"),
    cura    =("_cura",  "sum"),
    abandono=("_aband", "sum"),
    obito_tb=("_obito", "sum"),
    caso_novo=("_novo", "sum"),
    pulmonar =("_pulm", "sum"),
    aids     =("_aids", "sum"),
    alcool   =("_alcool","sum"),
    pop_rua  =("_rua",  "sum"),
    pop_liber=("_liber","sum"),
).reset_index()

t = ind["total"].replace(0, 1)
ind["pct_hiv"]    = (ind["hiv_pos"]  / t * 100).round(1)
ind["pct_cura"]   = (ind["cura"]     / t * 100).round(1)
ind["pct_abandon"]= (ind["abandono"] / t * 100).round(1)
ind["pct_obito"]  = (ind["obito_tb"] / t * 100).round(1)
ind["pct_novo"]   = (ind["caso_novo"]/ t * 100).round(1)
ind["pct_pulm"]   = (ind["pulmonar"] / t * 100).round(1)
ind["pct_aids"]   = (ind["aids"]     / t * 100).round(1)
ind["pct_alcool"] = (ind["alcool"]   / t * 100).round(1)

ind.to_csv(PASTA_DADOS / "historico_indicadores.csv", index=False)
print(f"      {len(ind)} anos")

# ── Resumo ────────────────────────────────────────────────────────────────────
print(f"\nConcluido em {time.time()-inicio:.1f}s")
for nome in ["historico_mensal.csv", "historico_estadual.csv",
             "historico_anual.csv", "historico_indicadores.csv"]:
    p = PASTA_DADOS / nome
    if p.exists():
        print(f"  {nome:<35} {p.stat().st_size/1024:.1f} KB")
