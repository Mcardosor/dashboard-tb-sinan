"""Clínico & Diagnóstico — HIV, Baciloscopia, TMR-TB, Desfecho por HIV."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from src.styles import inject_css_page
from src.session import get_df
from src.constantes import H_SMALL
from src.graficos import grafico_vazio
from src import graficos

st.set_page_config(page_title="Clínico & Diagnóstico | TB SINAN", page_icon="🏥", layout="wide")
inject_css_page()

df = get_df()

_INVAL   = ["nan", "None", "undefined", ""]
_NI_NORM = {"Nao informado": "Não informado"}

st.title("🏥 Clínico & Diagnóstico")

c1, c2 = st.columns(2)
with c1:
    st.subheader("Status HIV")
    st.caption("Resultado do teste de HIV entre os pacientes com TB. Pacientes com HIV têm imunidade reduzida, tornando a TB mais grave.")
    if "status_hiv" in df.columns:
        d = df["status_hiv"].astype(str).replace("nan", "Não informado").replace(_NI_NORM).value_counts().reset_index()
        d.columns = ["HIV", "Casos"]
        d = d[~d["HIV"].isin(_INVAL)]
        graficos.safe_pie(d, "HIV", "Casos", height=H_SMALL)
    else:
        grafico_vazio()

with c2:
    st.subheader("Baciloscopia — 1ª amostra")
    st.caption("Exame de escarro que detecta a bactéria da TB. **Positivo**: caso confirmado e transmissível.")
    if "baciloscopia_primeira_amostra" in df.columns:
        d = df["baciloscopia_primeira_amostra"].astype(str).replace("nan", "Não informado").replace(_NI_NORM).value_counts().reset_index()
        d.columns = ["Resultado", "Casos"]
        d = d[~d["Resultado"].isin(_INVAL)]
        graficos.safe_pie(d, "Resultado", "Casos", height=H_SMALL)
    else:
        grafico_vazio()

_, c3mid, _ = st.columns([1, 2, 1])
with c3mid:
    st.subheader("Teste Molecular Rápido (TMR-TB)")
    st.caption("Detecta TB e resistência à rifampicina em poucas horas. Mais preciso e rápido que a baciloscopia.")
    if "teste_molecular" in df.columns:
        d = df["teste_molecular"].astype(str).replace("nan", "Não informado").replace(_NI_NORM).value_counts().reset_index()
        d.columns = ["Resultado", "Casos"]
        d = d[~d["Resultado"].isin(_INVAL)]
        graficos.safe_pie(d, "Resultado", "Casos", height=H_SMALL)
    else:
        grafico_vazio()

st.divider()
st.subheader("Desfecho do Tratamento por Status HIV")
st.caption("Compara como o tratamento de TB termina dependendo do status HIV. Cada coluna soma 100% — proporção de cada desfecho dentro de cada grupo.")
graficos.fig_desfecho_por_hiv(df)

st.divider()
st.subheader("Coinfecção TB-HIV por Estado")
st.caption("De cada 100 pacientes com TB no estado, quantos também têm HIV.")
graficos.fig_coinfeccao_hiv_uf(df)
