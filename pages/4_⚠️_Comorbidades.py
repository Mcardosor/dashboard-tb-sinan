"""Comorbidades & Vulnerabilidades."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd

from src.styles import inject_css_page
from src.session import get_df, get_context
from src.constantes import pct
from src import graficos

st.set_page_config(page_title="Comorbidades & Vulnerabilidades | TB SINAN", page_icon="⚠️", layout="wide")
inject_css_page()

df  = get_df()
ctx = get_context()
total = ctx["total_filt"]

st.title("⚠️ Comorbidades & Vulnerabilidades")

col_comor, col_vuln = st.columns([3, 2])
with col_comor:
    st.subheader("Comorbidades Associadas")
    st.caption("Doenças presentes junto com a TB. Ex: diabéticos têm risco 3x maior de desenvolver TB.")
    graficos.fig_comorbidades(df, total)

with col_vuln:
    st.subheader("Populações Vulneráveis")
    st.caption("Grupos com risco elevado de TB. Pessoas em situação de rua têm risco até 56x maior.")
    st.markdown("<br>", unsafe_allow_html=True)
    vuln = {
        "Privado de Liberdade":  (df.get("populacao_privada_liberdade", pd.Series(dtype=str)).astype(str).str.lower() == "sim").sum(),
        "Em Situação de Rua":    (df.get("populacao_situacao_rua",      pd.Series(dtype=str)).astype(str).str.lower() == "sim").sum(),
        "Profissional de Saúde": (df.get("profissional_saude",          pd.Series(dtype=str)).astype(str).str.lower() == "sim").sum(),
        "Imigrante":             (df.get("populacao_imigrante",         pd.Series(dtype=str)).astype(str).str.lower() == "sim").sum(),
    }
    for label, val in vuln.items():
        st.metric(label, f"{val:,}".replace(",", "."), pct(val, total))
        st.markdown("<div style='margin-bottom:6px'></div>", unsafe_allow_html=True)

st.divider()
st.subheader("Comorbidades por Estado")
st.caption("Proporção de casos com cada comorbidade em cada estado (% sobre o total de casos do estado).")
graficos.fig_comorbidades_uf(df)
