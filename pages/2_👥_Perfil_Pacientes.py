"""Perfil dos Pacientes — Sexo, Forma Clínica, Raça/Cor, Pirâmides Etárias."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from src.styles import inject_css_page
from src.session import get_df, get_context
from src.constantes import H_SMALL, H_MEDIUM, PLOTLY_CFG
from src.graficos import grafico_vazio
from src import graficos

st.set_page_config(page_title="Perfil dos Pacientes | TB SINAN", page_icon="👥", layout="wide")
inject_css_page()

df  = get_df()
ctx = get_context()

_INVAL   = ["nan", "None", "undefined", ""]
_NI_NORM = {"Nao informado": "Não informado"}

st.title("👥 Perfil dos Pacientes")

c1, c2 = st.columns(2)
with c1:
    st.subheader("Por Sexo")
    st.caption("Distribuição dos casos entre homens e mulheres. Historicamente, a TB afeta mais homens no Brasil.")
    if "sexo" in df.columns:
        d = df["sexo"].astype(str).replace("nan", "Não informado").replace(_NI_NORM).value_counts().reset_index()
        d.columns = ["Sexo", "Casos"]
        d = d[~d["Sexo"].isin(_INVAL)]
        graficos.safe_pie(d, "Sexo", "Casos", height=H_SMALL)
        n_ign = int(df["sexo"].isna().sum() + df["sexo"].isin(["Ignorado", "Nao informado", "Não informado"]).sum())
        if n_ign > 0:
            st.caption(f"⚠️ {n_ign:,} casos com sexo não informado/ignorado não aparecem no gráfico.")
    else:
        grafico_vazio()

with c2:
    st.subheader("Forma Clínica")
    st.caption("**Pulmonar**: TB nos pulmões — transmissível pelo ar. **Extrapulmonar**: TB em outros órgãos.")
    if "forma" in df.columns:
        d = df["forma"].astype(str).replace("nan", "Não informado").replace(_NI_NORM).value_counts().reset_index()
        d.columns = ["Forma", "Casos"]
        d = d[~d["Forma"].isin(_INVAL)]
        graficos.safe_pie(d, "Forma", "Casos", height=H_SMALL)
        n_ign = int(df["forma"].isna().sum() + df["forma"].isin(["Ignorado", "Nao informado", "Não informado"]).sum())
        if n_ign > 0:
            st.caption(f"⚠️ {n_ign:,} casos com forma clínica não informada não aparecem no gráfico.")
    else:
        grafico_vazio()

_, c3mid, _ = st.columns([1, 2, 1])
with c3mid:
    st.subheader("Tipo de Entrada")
    st.caption("**Caso Novo**: primeiro diagnóstico. **Recidiva**: já teve TB e voltou a adoecer. **Reingresso**: interrompeu o tratamento e retornou.")
    if "tipo_entrada" in df.columns:
        d = df["tipo_entrada"].astype(str).replace("nan", "Não informado").replace(_NI_NORM).value_counts().reset_index()
        d.columns = ["Tipo", "Casos"]
        d = d[~d["Tipo"].isin(_INVAL)]
        graficos.safe_pie(d, "Tipo", "Casos", height=H_SMALL)
    else:
        grafico_vazio()

st.divider()
c4, c5 = st.columns(2)
with c4:
    st.subheader("Por Raça/Cor")
    st.caption("A TB afeta desproporcionalmente populações negras e indígenas no Brasil.")
    if "raca_cor" in df.columns:
        d = df["raca_cor"].astype(str).replace("nan", "Não informado").replace(_NI_NORM).value_counts().reset_index()
        d.columns = ["Raça", "Casos"]
        d = d[~d["Raça"].isin(["nan", "None"])]
        graficos.safe_bar_v(d, "Raça", "Casos", height=H_MEDIUM)
    else:
        grafico_vazio()

with c5:
    st.subheader("Situação de Encerramento")
    st.caption("Como o caso foi concluído: **Cura**, **Abandono**, **Óbito por TB**.")
    col_enc = "situacao_enc_norm" if "situacao_enc_norm" in df.columns else "situacao_encerramento"
    if col_enc in df.columns:
        d = df[col_enc].astype(str).replace("nan", "Não informado").replace(_NI_NORM).value_counts().reset_index()
        d.columns = ["Situação", "Casos"]
        d = d[~d["Situação"].isin(_INVAL)]
        graficos.safe_bar_h(d.sort_values("Casos", ascending=False), "Casos", "Situação", height=H_MEDIUM)
    else:
        grafico_vazio()

st.divider()
p1, p2 = st.columns(2)
with p1:
    st.subheader("Pirâmide Etária — Casos de TB")
    st.caption("Distribuição dos casos por faixa etária e sexo")
    if "idade_anos" in df.columns and "sexo" in df.columns:
        st.plotly_chart(graficos.fig_piramide(df), use_container_width=True, config=PLOTLY_CFG)
    else:
        grafico_vazio()
with p2:
    st.subheader("Pirâmide Etária — Óbitos por TB")
    st.caption("Distribuição dos óbitos por TB por faixa etária e sexo")
    fig_ob = graficos.fig_piramide_obitos(df)
    if fig_ob:
        st.plotly_chart(fig_ob, use_container_width=True, config=PLOTLY_CFG)
    else:
        st.info("Dados insuficientes de óbitos para a pirâmide.")
