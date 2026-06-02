"""Tendência Histórica — evolução anual e mensal de casos de TB."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px

from src.styles import inject_css_page
from src.session import get_df, get_context
from src.constantes import ANO_INICIO, ANO_ATUAL, HIST_INDICADORES, H_LARGE, PLOTLY_CFG
from src.graficos import tb_layout
from src.dados import load_historico
from src import graficos

st.set_page_config(page_title="Tendência Histórica | TB SINAN", page_icon="📈", layout="wide")
inject_css_page()

df  = get_df()
ctx = get_context()
ano_sel   = ctx["ano_sel"]
total     = ctx["total_filt"]

st.title("📈 Tendência Histórica")

df_hist   = load_historico()
ANOS_HIST = list(range(ANO_INICIO, ano_sel))

if df_hist is None or not ANOS_HIST:
    st.warning(
        "Dados históricos não encontrados — apenas 1 ano disponível.\n\n"
        "Execute `python scripts/conectar_banco.py 2001 2024` para popular o histórico."
    )
    if "mes_num" in df.columns:
        st.subheader(f"Número de casos por mês — {ano_sel}")
        st.caption(f"Total de notificações de TB por mês de notificação — ano {ano_sel}")
        mes = (df.dropna(subset=["mes_num"])
               .groupby("mes_num").size().reset_index(name="casos"))
        mes["mes_label"] = mes["mes_num"].map(graficos.MESES_PT)
        mes = mes.sort_values("mes_num")
        media_m = mes["casos"].mean()
        fig_mes = px.bar(mes, x="mes_label", y="casos",
                         labels={"mes_label": "Mês", "casos": "Nº de casos notificados"})
        fig_mes.add_hline(y=media_m, line_dash="dot", line_color="#58a6ff",
                          annotation_text=f"Média mensal: {media_m:,.0f}".replace(",", "."),
                          annotation_font=dict(color="#58a6ff", size=11))
        tb_layout(fig_mes, altura=H_LARGE)
        fig_mes.update_traces(marker_color="#d29922",
                              marker_line_color="#0d1117", marker_line_width=1,
                              hovertemplate="<b>%{x}</b><br>Nº de casos: %{y:,}<extra></extra>")
        st.plotly_chart(fig_mes, use_container_width=True, config=PLOTLY_CFG)
else:
    df_mensal = df_hist["mensal"]
    hist_anos = df_mensal[df_mensal["nu_ano"].astype(str).isin([str(a) for a in ANOS_HIST])]
    media_anual_hist = hist_anos.groupby("nu_ano")["casos"].sum().mean() if not hist_anos.empty else 0
    variacao_geral   = ((total - media_anual_hist) / media_anual_hist * 100) if media_anual_hist else 0
    tend_icon  = "⬆️" if variacao_geral > 5 else ("⬇️" if variacao_geral < -5 else "➡️")
    tend_label = "Para Mais" if variacao_geral > 5 else ("Para Menos" if variacao_geral < -5 else "Estável")

    ka, kb, kc = st.columns(3)
    ka.metric("Tendência vs histórico", f"{tend_icon} {tend_label}",
              f"{variacao_geral:+.1f}% vs {ANO_INICIO}–{ano_sel-1}")
    kb.metric(f"Total {ano_sel}", f"{int(total):,}".replace(",", "."), "casos notificados")
    kc.metric("Média anual histórica", f"{int(media_anual_hist):,}".replace(",", "."),
              f"casos/ano | {ANO_INICIO}–{ano_sel-1}")

    st.divider()
    st.subheader(f"Casos por Mês — {ano_sel} vs Média Histórica")
    st.caption(f"Barras laranja = casos de {ano_sel}. Linha pontilhada = média histórica {ANO_INICIO}–{ano_sel-1}.")
    graficos.fig_tendencia_mensal(df, df_hist, ano_sel, ANOS_HIST)

    st.divider()
    st.subheader(f"Evolução Anual — {ANO_INICIO}–{ANO_ATUAL}")
    st.caption(f"Total de casos notificados por ano. A barra vermelha destaca {ano_sel}.")
    graficos.fig_tendencia_anual(df_hist, ano_sel)

    st.divider()
    st.subheader(f"Variação por Estado — {ano_sel} vs Média Histórica")
    st.caption(f"Variação de cada estado em relação à sua média histórica ({ANO_INICIO}–{ano_sel-1}).")
    graficos.fig_tendencia_uf(df, df_hist, ano_sel, ANOS_HIST)

    if HIST_INDICADORES.exists():
        st.divider()
        st.subheader(f"Evolução Histórica de Indicadores Clínicos — {ANO_INICIO}–{ANO_ATUAL}")
        st.caption("Acompanhe como os principais indicadores de TB evoluíram ao longo dos anos.")
        try:
            df_ind = pd.read_csv(str(HIST_INDICADORES))
            opcoes_multisel = [
                "Coeficiente de incidência (por 100 mil)",
                "Coeficiente de mortalidade (por 100 mil)",
                "Taxa de cura (%)", "Taxa de abandono (%)",
                "Coinfecção HIV (%)", "Forma pulmonar (%)",
                "Testagem para HIV (%)", "TDO (%)",
                "Óbito por TB (%)", "Casos novos (%)",
            ]
            sel_ind = st.multiselect(
                "Selecione os indicadores:",
                options=opcoes_multisel,
                default=["Coinfecção HIV (%)", "Taxa de cura (%)", "Taxa de abandono (%)"],
            )
            if sel_ind:
                graficos.fig_indicadores_historicos(df_ind, sel_ind, ano_sel)
        except Exception as e:
            st.warning(f"Erro ao carregar indicadores históricos: {e}")
