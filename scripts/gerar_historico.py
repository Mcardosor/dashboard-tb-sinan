"""
gerar_historico.py
------------------
Lê todos os Parquets _tratado disponíveis em dados_dashboard/ e gera
quatro arquivos CSV pré-agregados consumidos pela aba de Tendência:

  historico_mensal.csv      — casos por ano × mês
  historico_estadual.csv    — casos por ano × estado (sigla UF)
  historico_anual.csv       — total de casos por ano
  historico_indicadores.csv — indicadores percentuais por ano

Execute após ter Parquets tratados para todos os anos desejados:
    python scripts/gerar_historico.py
    python scripts/gerar_historico.py 2022 2025   # intervalo específico
"""

import sys
import time
from pathlib import Path

# Permite importar src/ quando o script é chamado direto da raiz do projeto
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from src.constantes import PASTA_DADOS, UF_SIGLAS

# ── CLI — anos opcionais ───────────────────────────────────────────────────────
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

ANOS = list(range(ano_ini, ano_fim + 1))

# ── Descobre quais arquivos existem ───────────────────────────────────────────
arquivos = {}
for ano in ANOS:
    path = PASTA_DADOS / f"sinan_tube_{ano}_tratado.parquet"
    if path.exists():
        arquivos[ano] = path

if not arquivos:
    print(f"Nenhum arquivo _tratado encontrado em {PASTA_DADOS} para os anos {ano_ini}-{ano_fim}.")
    print("Execute primeiro: python scripts/conectar_banco.py e python scripts/preparar_dados.py")
    sys.exit(1)

print(f"Encontrados {len(arquivos)} arquivo(s): {sorted(arquivos.keys())}")

# ── Carrega e concatena todos os anos ─────────────────────────────────────────
print("\nCarregando Parquets...")
inicio = time.time()

dfs = []
for ano, path in sorted(arquivos.items()):
    df_ano = pd.read_parquet(
        path,
        columns=[
            "ano_notificacao", "estado_notificacao", "data_notificacao",
            "situacao_encerramento", "status_hiv", "tipo_entrada", "forma",
            "agravo_aids", "agravo_alcoolismo", "agravo_diabetes",
            "agravo_drogas_ilicitas", "agravo_tabagismo", "agravo_doenca_mental",
            "populacao_privada_liberdade", "populacao_situacao_rua",
        ],
    )
    # garante ano_notificacao como int
    df_ano["ano_notificacao"] = pd.to_numeric(
        df_ano["ano_notificacao"], errors="coerce"
    ).fillna(ano).astype(int)
    dfs.append(df_ano)
    print(f"  {ano}: {len(df_ano):,} registros")

df = pd.concat(dfs, ignore_index=True)
print(f"\nTotal concatenado: {len(df):,} registros em {time.time()-inicio:.1f}s")

# ── Converte categoria para string para evitar problemas no groupby ────────────
for col in df.select_dtypes("category").columns:
    df[col] = df[col].astype(str)

# ── Sigla UF a partir do nome do estado ───────────────────────────────────────
df["uf_sigla"] = df["estado_notificacao"].map(UF_SIGLAS).fillna("Desconhecido")

# ── Mês de notificação ────────────────────────────────────────────────────────
df["data_notificacao"] = pd.to_datetime(df["data_notificacao"], errors="coerce")
df["mes_num"] = df["data_notificacao"].dt.month

# ── 1. Histórico mensal ───────────────────────────────────────────────────────
print("\n[1/4] Gerando historico_mensal.csv...")
mensal = (
    df.dropna(subset=["mes_num"])
    .groupby(["ano_notificacao", "mes_num"])
    .size()
    .reset_index(name="casos")
)
mensal.to_csv(PASTA_DADOS / "historico_mensal.csv", index=False)
print(f"      {len(mensal):,} linhas")

# ── 2. Histórico estadual ─────────────────────────────────────────────────────
print("[2/4] Gerando historico_estadual.csv...")
estadual = (
    df[df["uf_sigla"] != "Desconhecido"]
    .groupby(["ano_notificacao", "uf_sigla"])
    .size()
    .reset_index(name="casos")
)
estadual.to_csv(PASTA_DADOS / "historico_estadual.csv", index=False)
print(f"      {len(estadual):,} linhas")

# ── 3. Histórico anual ────────────────────────────────────────────────────────
print("[3/4] Gerando historico_anual.csv...")
anual = df.groupby("ano_notificacao").size().reset_index(name="casos")
anual.to_csv(PASTA_DADOS / "historico_anual.csv", index=False)
print(f"      {len(anual):,} linhas")

# ── 4. Indicadores históricos ─────────────────────────────────────────────────
print("[4/4] Gerando historico_indicadores.csv...")

# Flags booleanas baseadas nos valores decodificados do schema silver
def _sim(serie: pd.Series) -> pd.Series:
    """Retorna True onde o valor é 'Sim' (case-insensitive)."""
    return serie.astype(str).str.strip().str.lower() == "sim"

df["hiv_pos"]   = df["status_hiv"].astype(str).str.strip().str.lower() == "positivo"
df["cura"]      = df["situacao_encerramento"].astype(str).str.strip() == "Cura"
df["abandono"]  = df["situacao_encerramento"].astype(str).str.strip().isin(
    ["Abandono", "Abandono Primário", "Abandono Primario"]
)
df["obito_tb"]  = df["situacao_encerramento"].astype(str).str.strip() == "Óbito por TB"
df["caso_novo"] = df["tipo_entrada"].astype(str).str.strip() == "Caso Novo"
df["pulmonar"]  = df["forma"].astype(str).str.strip() == "Pulmonar"
df["aids"]      = _sim(df["agravo_aids"])
df["alcool"]    = _sim(df["agravo_alcoolismo"])
df["pop_rua"]   = _sim(df["populacao_situacao_rua"])
df["pop_liber"] = _sim(df["populacao_privada_liberdade"])

ind = df.groupby("ano_notificacao").agg(
    total     =("ano_notificacao", "count"),
    hiv_pos   =("hiv_pos",   "sum"),
    cura      =("cura",      "sum"),
    abandono  =("abandono",  "sum"),
    obito_tb  =("obito_tb",  "sum"),
    caso_novo =("caso_novo", "sum"),
    pulmonar  =("pulmonar",  "sum"),
    aids      =("aids",      "sum"),
    alcool    =("alcool",    "sum"),
    pop_rua   =("pop_rua",   "sum"),
    pop_liber =("pop_liber", "sum"),
).reset_index()

# Percentuais (evita divisão por zero)
_t = ind["total"].replace(0, 1)
ind["pct_hiv"]    = (ind["hiv_pos"]   / _t * 100).round(1)
ind["pct_cura"]   = (ind["cura"]      / _t * 100).round(1)
ind["pct_abandon"]= (ind["abandono"]  / _t * 100).round(1)
ind["pct_obito"]  = (ind["obito_tb"]  / _t * 100).round(1)
ind["pct_novo"]   = (ind["caso_novo"] / _t * 100).round(1)
ind["pct_pulm"]   = (ind["pulmonar"]  / _t * 100).round(1)
ind["pct_aids"]   = (ind["aids"]      / _t * 100).round(1)
ind["pct_alcool"] = (ind["alcool"]    / _t * 100).round(1)

ind.to_csv(PASTA_DADOS / "historico_indicadores.csv", index=False)
print(f"      {len(ind):,} anos")

# ── Resumo ────────────────────────────────────────────────────────────────────
elapsed = time.time() - inicio
print(f"\nConcluido em {elapsed:.1f}s. Arquivos em {PASTA_DADOS}:")
for nome in sorted(["historico_mensal.csv", "historico_estadual.csv",
                     "historico_indicadores.csv"]):
    p = PASTA_DADOS / nome
    if p.exists():
        print(f"  {nome:<35} {p.stat().st_size/1024:>7.1f} KB")
