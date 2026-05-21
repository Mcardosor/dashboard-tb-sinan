"""
graficos.py
───────────
Uma função por gráfico Plotly. Cada função recebe um DataFrame
e retorna uma go.Figure pronta para st.plotly_chart().
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.constantes import (
    UF_SIGLAS, AGRAVOS, POPULACOES, NORMALIZAR_DESFECHO,
    CORES_DESFECHOS, CORES_RACA, CORES_FORMA, ESCALA_MAPA,
    BG, HOVER_LABEL, TB_COLORS, TB_SEQ_INCIDENCIA, TB_SEQ_MORTAL,
    CORES, H_SMALL, H_MEDIUM, H_LARGE,
    tb_layout, tb_color_map, grafico_vazio, POP_ESTADO,
)

MESES_PT = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr",
    5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago",
    9: "Set", 10: "Out", 11: "Nov", 12: "Dez",
}


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS VISUAIS
# ══════════════════════════════════════════════════════════════════════════════

def safe_pie(df_plot: pd.DataFrame, names: str, values: str,
             height=H_SMALL, titulo=None):
    """Donut chart com paleta TB semântica."""
    if df_plot.empty or df_plot[values].sum() == 0:
        grafico_vazio()
        return
    color_map = tb_color_map(df_plot[names].astype(str).tolist())
    total_val = df_plot[values].sum()
    fig = px.pie(df_plot, names=names, values=values,
                 color=names, color_discrete_map=color_map, hole=0.45)
    tb_layout(fig, titulo=titulo, altura=height)
    fig.update_layout(
        # Legenda horizontal embaixo — evita overflow lateral
        legend=dict(
            orientation="h",
            x=0.5, xanchor="center",
            y=-0.18, yanchor="top",
            font=dict(color="#c9d1d9", size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        margin={"t": 20, "r": 10, "l": 10, "b": 80},
        uniformtext_minsize=9,
        uniformtext_mode="hide",
    )
    fig.update_traces(
        textfont_color="#f0f6fc", textfont_size=11,
        # Mostra % apenas dentro de fatias com mais de 6% — oculta fatias pequenas
        textinfo="percent",
        insidetextorientation="horizontal",
        marker=dict(line=dict(color="#0d1117", width=2)),
        hovertemplate="<b>%{label}</b><br>Casos: %{value:,}<br>"
                      "Participação: %{percent}<extra></extra>",
        texttemplate="%{percent:.1%}",
    )
    # Zera rótulo das fatias menores que 6% para não sobrepor
    fig.for_each_trace(lambda t: t.update(
        text=["" if (v / total_val) < 0.06 else f"{v/total_val:.1%}"
              for v in df_plot[values]]
    ))
    st.plotly_chart(fig, use_container_width=True,
                    config={"displayModeBar": False, "scrollZoom": False})


def safe_bar_h(df_plot: pd.DataFrame, x: str, y: str,
               height=H_MEDIUM, titulo=None, label_x="Casos"):
    """Barra horizontal com paleta TB semântica."""
    if df_plot.empty:
        grafico_vazio()
        return
    color_map = tb_color_map(df_plot[y].astype(str).tolist())
    fig = px.bar(df_plot, x=x, y=y, orientation="h",
                 color=y, color_discrete_map=color_map,
                 labels={y: "", x: label_x})
    tb_layout(fig, titulo=titulo, altura=height)
    fig.update_layout(showlegend=False,
                      xaxis=dict(title=label_x), yaxis=dict(title=""))
    fig.update_traces(
        hovertemplate=f"<b>%{{y}}</b><br>{label_x}: %{{x:,}}<extra></extra>",
        marker_line_color="#0d1117", marker_line_width=1,
    )
    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": False})


def safe_bar_v(df_plot: pd.DataFrame, x: str, y: str,
               height=H_SMALL, titulo=None, label_y="Casos"):
    """Barra vertical com paleta TB semântica."""
    if df_plot.empty:
        grafico_vazio()
        return
    color_map = tb_color_map(df_plot[x].astype(str).tolist())
    fig = px.bar(df_plot, x=x, y=y, color=x, color_discrete_map=color_map,
                 labels={x: "", y: label_y})
    tb_layout(fig, titulo=titulo, altura=height)
    fig.update_layout(showlegend=False,
                      xaxis=dict(title="", tickangle=-30), yaxis=dict(title=label_y))
    fig.update_traces(
        hovertemplate=f"<b>%{{x}}</b><br>{label_y}: %{{y:,}}<extra></extra>",
        marker_line_color="#0d1117", marker_line_width=1,
    )
    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": False})


# ══════════════════════════════════════════════════════════════════════════════
#  GRÁFICOS ORIGINAIS (mantidos para compatibilidade)
# ══════════════════════════════════════════════════════════════════════════════

def fig_mapa(df: pd.DataFrame, geojson: dict) -> go.Figure:
    df_mapa = (
        df["estado_notificacao"].value_counts().reset_index()
        .rename(columns={"estado_notificacao": "estado", "count": "casos"})
    )
    df_mapa["uf"] = df_mapa["estado"].map(UF_SIGLAS)
    fig = px.choropleth(
        df_mapa, geojson=geojson,
        locations="uf", featureidkey="properties.sigla",
        color="casos", hover_name="estado",
        hover_data={"uf": False, "casos": ":,"},
        color_continuous_scale=ESCALA_MAPA,
        labels={"casos": "Notificacoes"},
    )
    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>%{customdata[0]} notificacoes<extra></extra>",
    )
    fig.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        coloraxis_colorbar=dict(title="Casos", thickness=14, len=0.7),
        hoverlabel=HOVER_LABEL,
        height=500,
    )
    return fig


def fig_piramide(df: pd.DataFrame) -> go.Figure:
    bins   = [0, 10, 20, 30, 40, 50, 60, 70, 200]
    labels = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70+"]
    df_p = df[df["sexo"].isin(["Masculino", "Feminino"])].copy()
    df_p["faixa"] = pd.cut(
        df_p["idade_anos"].astype("Int64"), bins=bins, labels=labels, right=False
    )
    pir = df_p.groupby(["faixa", "sexo"], observed=True).size().reset_index(name="casos")
    pir["valor"] = pir.apply(
        lambda r: -r["casos"] if r["sexo"] == "Masculino" else r["casos"], axis=1
    )
    fig = go.Figure()
    for sexo, cor in [("Masculino", "#58a6ff"), ("Feminino", "#f778ba")]:
        d = pir[pir["sexo"] == sexo]
        fig.add_trace(go.Bar(
            name=sexo, y=d["faixa"].astype(str), x=d["valor"],
            orientation="h", marker_color=cor,
            text=d["casos"].apply(lambda v: f"{v:,}"),
            textposition="inside", insidetextanchor="middle",
            textfont=dict(color="white", size=11),
            hovertemplate=(
                "<b>Faixa: %{y}</b><br>" + sexo +
                ": <b>%{customdata:,}</b> casos<extra></extra>"
            ),
            customdata=d["casos"],
        ))
    fig.update_layout(
        barmode="relative",
        xaxis=dict(tickvals=[-15000, -10000, -5000, 0, 5000, 10000],
                   ticktext=["15k", "10k", "5k", "0", "5k", "10k"],
                   title="Numero de casos", gridcolor="rgba(255,255,255,0.08)"),
        yaxis=dict(title="Faixa etaria", gridcolor="rgba(255,255,255,0.08)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5, xanchor="center"),
        hoverlabel=HOVER_LABEL, margin=dict(l=20, r=20, t=30, b=20),
        height=420, **BG,
    )
    return fig


def fig_desfechos(df: pd.DataFrame) -> go.Figure:
    col = "situacao_enc_norm" if "situacao_enc_norm" in df.columns else "situacao_encerramento"
    desfechos = (
        df[col].astype(str)
        .map(lambda x: NORMALIZAR_DESFECHO.get(x, x))
        .value_counts().reset_index()
        .rename(columns={col: "desfecho", "count": "casos"})
    )
    desfechos = desfechos[~desfechos["desfecho"].isin(["nan", "None"])]
    desfechos = desfechos.sort_values("casos", ascending=True)
    desfechos["pct"] = (desfechos["casos"] / desfechos["casos"].sum() * 100).round(1)
    color_map = {**CORES_DESFECHOS, **tb_color_map(desfechos["desfecho"].tolist())}
    fig = px.bar(
        desfechos, x="casos", y="desfecho", orientation="h",
        color="desfecho", color_discrete_map=color_map,
        custom_data=["pct"], labels={"casos": "Notificacoes", "desfecho": ""},
    )
    fig.update_traces(
        text=desfechos["casos"].apply(lambda v: f"{v:,}"),
        textposition="auto", insidetextanchor="middle",
        textfont=dict(color="white", size=12),
        hovertemplate="<b>%{y}</b><br>%{x:,} casos<br>%{customdata[0]}% do total<extra></extra>",
        marker_line_color="#0d1117", marker_line_width=1,
    )
    fig.update_layout(showlegend=False,
                      xaxis=dict(title="Numero de casos", gridcolor="rgba(255,255,255,0.08)"),
                      hoverlabel=HOVER_LABEL, margin=dict(l=10, r=20, t=10, b=20),
                      height=420, **BG)
    return fig


def fig_raca_cor(df: pd.DataFrame) -> go.Figure | None:
    if "raca_cor" not in df.columns:
        return None
    raca = (df["raca_cor"].astype(str).value_counts().reset_index()
            .rename(columns={"raca_cor": "categoria", "count": "casos"}))
    raca = raca[~raca["categoria"].isin(["nan", "Nao informado", "Ignorado"])]
    raca = raca.sort_values("casos", ascending=True)
    raca["pct"] = (raca["casos"] / raca["casos"].sum() * 100).round(1)
    color_map = tb_color_map(raca["categoria"].tolist())
    fig = px.bar(raca, x="casos", y="categoria", orientation="h",
                 color="categoria", color_discrete_map=color_map,
                 custom_data=["pct"], labels={"casos": "Notificacoes", "categoria": ""})
    fig.update_traces(
        text=raca["casos"].apply(lambda v: f"{v:,}"),
        textposition="auto", insidetextanchor="middle",
        textfont=dict(color="white", size=12), marker_line_width=0,
        hovertemplate="<b>%{y}</b><br>%{x:,} casos<br>%{customdata[0]}% do total<extra></extra>",
    )
    fig.update_layout(showlegend=False, xaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
                      hoverlabel=HOVER_LABEL, margin=dict(l=10, r=20, t=10, b=20),
                      height=340, **BG)
    return fig


def fig_forma_clinica(df: pd.DataFrame) -> go.Figure | None:
    if "forma" not in df.columns:
        return None
    forma = (df["forma"].astype(str).value_counts().reset_index()
             .rename(columns={"forma": "categoria", "count": "casos"}))
    forma = forma[~forma["categoria"].isin(["nan", "Nao informado", "Ignorado"])]
    forma = forma.sort_values("casos", ascending=True)
    forma["pct"] = (forma["casos"] / forma["casos"].sum() * 100).round(1)
    color_map = {**CORES_FORMA, **tb_color_map(forma["categoria"].tolist())}
    fig = px.bar(forma, x="casos", y="categoria", orientation="h",
                 color="categoria", color_discrete_map=color_map,
                 custom_data=["pct"], labels={"casos": "Notificacoes", "categoria": ""})
    fig.update_traces(
        text=forma["casos"].apply(lambda v: f"{v:,}"),
        textposition="auto", insidetextanchor="middle",
        textfont=dict(color="white", size=12), marker_line_width=0,
        hovertemplate="<b>%{y}</b><br>%{x:,} casos<br>%{customdata[0]}% do total<extra></extra>",
    )
    fig.update_layout(showlegend=False, xaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
                      hoverlabel=HOVER_LABEL, margin=dict(l=10, r=20, t=10, b=20),
                      height=340, **BG)
    return fig


def _barras_percentual(df, mapeamento, escala_cores, height):
    total = len(df)
    dados = []
    for col, nome in mapeamento.items():
        if col in df.columns:
            n = (df[col].astype(str).str.strip().str.lower() == "sim").sum()
            dados.append({"categoria": nome, "casos": int(n),
                          "percentual": round(100 * n / total, 1)})
    if not dados:
        return None
    df_d = pd.DataFrame(dados).sort_values("percentual", ascending=True)
    n    = len(df_d)
    cores = [escala_cores[int(i * (len(escala_cores) - 1) / max(n - 1, 1))] for i in range(n)]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_d["percentual"], y=df_d["categoria"], orientation="h",
        marker=dict(color=cores, line_width=0),
        text=[f"{p}%  ({c:,})" for p, c in zip(df_d["percentual"], df_d["casos"])],
        textposition="auto", insidetextanchor="middle",
        textfont=dict(color="white", size=12),
        customdata=df_d[["casos", "percentual"]].values,
        hovertemplate="<b>%{y}</b><br>Percentual: <b>%{customdata[1]}%</b><br>"
                      "Notificacoes: <b>%{customdata[0]:,}</b><extra></extra>",
    ))
    fig.update_layout(
        xaxis=dict(title="% dos casos", ticksuffix="%",
                   range=[0, df_d["percentual"].max() * 1.35],
                   gridcolor="rgba(255,255,255,0.08)"),
        hoverlabel=HOVER_LABEL, yaxis_title="",
        margin=dict(l=10, r=20, t=10, b=30), height=height, **BG,
    )
    return fig


def fig_agravos(df: pd.DataFrame) -> go.Figure | None:
    return _barras_percentual(df, AGRAVOS, px.colors.sequential.Oranges, height=300)


def fig_populacoes(df: pd.DataFrame) -> go.Figure | None:
    return _barras_percentual(df, POPULACOES, px.colors.sequential.Blues, height=260)


# ══════════════════════════════════════════════════════════════════════════════
#  GRÁFICOS NOVOS — Clínico, Comorbidades, Tendência
# ══════════════════════════════════════════════════════════════════════════════

def fig_coinfeccao_hiv_uf(df: pd.DataFrame) -> None:
    """Coinfecção TB-HIV por estado (renderiza diretamente via st.plotly_chart)."""
    if "status_hiv" not in df.columns or "uf_sigla" not in df.columns:
        grafico_vazio()
        return
    hiv_uf   = (df[df["status_hiv"] == "Positivo"]
                .groupby("uf_sigla").size().reset_index(name="hiv_pos"))
    total_uf = df.groupby("uf_sigla").size().reset_index(name="total")
    coinfec  = hiv_uf.merge(total_uf, on="uf_sigla")
    if coinfec.empty:
        grafico_vazio()
        return
    coinfec["pct"] = (coinfec["hiv_pos"] / coinfec["total"] * 100).round(1)
    coinfec = coinfec.sort_values("pct", ascending=True)
    fig = px.bar(coinfec, x="pct", y="uf_sigla", orientation="h",
                 labels={"pct": "% coinfecção HIV", "uf_sigla": "Estado"}, text="pct")
    tb_layout(fig, altura=H_LARGE)
    fig.update_traces(
        marker_color="#da3633",
        texttemplate="%{text:.1f}%", textposition="outside",
        textfont=dict(color="#c9d1d9", size=11),
        hovertemplate="<b>%{y}</b><br>Coinfecção HIV: %{x:.1f}%<extra></extra>",
        marker_line_color="#0d1117", marker_line_width=1,
    )
    fig.update_layout(showlegend=False,
                      xaxis=dict(title="% coinfecção HIV"), yaxis=dict(title=""))
    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": False})


def fig_comorbidades(df: pd.DataFrame, total: int) -> None:
    """Barras horizontais de comorbidades com percentual."""
    comorbidades = {
        "AIDS/HIV":        "agravo_aids",
        "Alcoolismo":      "agravo_alcoolismo",
        "Diabetes":        "agravo_diabetes",
        "Drogas ilícitas": "agravo_drogas_ilicitas",
        "Tabagismo":       "agravo_tabagismo",
        "Doença Mental":   "agravo_doenca_mental",
    }
    cor_comor = {
        "AIDS/HIV":        "#da3633",
        "Alcoolismo":      "#d29922",
        "Diabetes":        "#8957e5",
        "Drogas ilícitas": "#f0883e",
        "Tabagismo":       "#cf222e",
        "Doença Mental":   "#a371f7",
    }
    dados = []
    for nome, col in comorbidades.items():
        if col in df.columns:
            n = (df[col].astype(str).str.lower().str.strip() == "sim").sum()
            dados.append({"Comorbidade": nome, "Casos": int(n),
                          "Percentual": round(n / total * 100, 1) if total else 0})
    if not dados:
        grafico_vazio()
        return
    df_c = pd.DataFrame(dados).sort_values("Casos", ascending=True)
    fig = px.bar(df_c, x="Casos", y="Comorbidade", orientation="h",
                 color="Comorbidade", color_discrete_map=cor_comor,
                 text="Percentual", labels={"Casos": "Nº de casos"})
    tb_layout(fig, altura=360)
    fig.update_traces(
        texttemplate="%{text:.1f}%", textposition="outside",
        textfont=dict(color="#c9d1d9", size=11),
        hovertemplate="<b>%{y}</b><br>Casos: %{x:,}<br>Participação: %{text:.1f}%<extra></extra>",
        marker_line_color="#0d1117", marker_line_width=1,
    )
    fig.update_layout(showlegend=False, xaxis=dict(title="Nº de casos"), yaxis=dict(title=""))
    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": False})


def fig_comorbidades_uf(df: pd.DataFrame) -> None:
    """Comorbidades agrupadas por estado (% sobre total de casos no estado)."""
    if "uf_sigla" not in df.columns:
        grafico_vazio()
        return
    cols_map = {
        "agravo_aids": "AIDS", "agravo_alcoolismo": "Alcoolismo",
        "agravo_drogas_ilicitas": "Drogas", "agravo_tabagismo": "Tabagismo",
    }
    cols_exist = {k: v for k, v in cols_map.items() if k in df.columns}
    if not cols_exist:
        grafico_vazio()
        return

    agg = df.groupby("uf_sigla").agg(total=("forma", "count"),
                                      **{k: (k, lambda s: (s.astype(str).str.lower() == "sim").sum())
                                         for k in cols_exist}).reset_index()
    for col in cols_exist:
        agg[col] = (agg[col] / agg["total"].replace(0, 1) * 100).round(1)
    agg = agg.sort_values(list(cols_exist.keys())[0], ascending=False)

    nomes = cols_exist
    cor_map = {"agravo_aids": "#da3633", "agravo_alcoolismo": "#d29922",
               "agravo_drogas_ilicitas": "#f0883e", "agravo_tabagismo": "#cf222e"}
    fig = px.bar(agg, x="uf_sigla", y=list(cols_exist.keys()), barmode="group",
                 labels={"value": "%", "uf_sigla": "Estado", "variable": "Comorbidade"},
                 color_discrete_map=cor_map)
    fig.for_each_trace(lambda t: t.update(
        name=nomes.get(t.name, t.name),
        hovertemplate=f"<b>%{{x}}</b><br>{nomes.get(t.name, t.name)}: %{{y:.1f}}%<extra></extra>",
    ))
    tb_layout(fig, altura=H_LARGE)
    fig.update_layout(
        xaxis=dict(title="Estado", tickangle=-45), yaxis=dict(title="%"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=""),
        bargap=0.15, bargroupgap=0.05,
    )
    fig.update_traces(marker_line_color="#0d1117", marker_line_width=1)
    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": False})


def fig_tendencia_mensal(df_filtrado: pd.DataFrame, df_hist: dict,
                          ano_sel: int, anos_hist: list[int]) -> None:
    """2025 vs média histórica por mês."""
    if "mes_num" not in df_filtrado.columns:
        grafico_vazio()
        return

    mes_ano = (df_filtrado.dropna(subset=["mes_num"])
               .groupby("mes_num").size().reset_index(name=f"casos_{ano_sel}"))
    mes_max = int(mes_ano["mes_num"].max()) if not mes_ano.empty else 12

    # Um mês só é realmente "incompleto" se for o mês atual do ano atual.
    # Para anos passados, todos os meses têm dados completos.
    import datetime as _dt
    _hoje = _dt.datetime.now()
    mes_incompleto_num = (
        mes_max
        if (ano_sel == _hoje.year and mes_max == _hoje.month)
        else None
    )

    df_mensal   = df_hist["mensal"]
    hist_anos   = df_mensal[df_mensal["nu_ano"].astype(str).isin([str(a) for a in anos_hist])]
    media_hist  = (hist_anos.groupby("mes_num")["casos"].sum().reset_index(name="total"))
    media_hist["media_hist"] = (media_hist["total"] / len(anos_hist)).round(0)

    tabela = mes_ano.merge(media_hist[["mes_num", "media_hist"]], on="mes_num", how="outer").fillna(0)
    tabela = tabela.sort_values("mes_num")
    tabela["mes_label"] = tabela["mes_num"].map(MESES_PT)
    tabela["variacao"]  = ((tabela[f"casos_{ano_sel}"] - tabela["media_hist"])
                           / tabela["media_hist"].replace(0, 1) * 100).round(1)
    tabela["direcao"]   = tabela["variacao"].apply(
        lambda v: "Para Mais" if v > 5 else ("Para Menos" if v < -5 else "Estavel")
    )

    COR_MAIS = "#da3633"; COR_MENOS = "#3fb950"; COR_ESTAVEL = "#d29922"
    COR_INC  = "#6e7681"; COR_HIST  = "#58a6ff"
    cores_barras = [
        COR_INC if (mes_incompleto_num and int(r["mes_num"]) == mes_incompleto_num) else
        COR_MAIS if r["direcao"] == "Para Mais" else
        COR_MENOS if r["direcao"] == "Para Menos" else COR_ESTAVEL
        for _, r in tabela.iterrows()
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=tabela["mes_label"], y=tabela[f"casos_{ano_sel}"],
        marker_color=cores_barras, name=f"Casos {ano_sel}",
        marker_line_color="#0d1117", marker_line_width=1,
        hovertemplate=f"<b>%{{x}} — {ano_sel}</b><br>Casos: %{{y:,}}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=tabela["mes_label"], y=tabela["media_hist"],
        mode="lines+markers", name=f"Média {anos_hist[0]}–{anos_hist[-1]}",
        line=dict(color=COR_HIST, width=2.5, dash="dot"),
        marker=dict(size=7, color=COR_HIST, line=dict(color="#0d1117", width=1)),
        hovertemplate="<b>%{x} — Média histórica</b><br>%{y:,.0f} casos<extra></extra>",
    ))
    if mes_incompleto_num is not None:
        mes_inc = tabela[tabela["mes_num"] == mes_incompleto_num]
        if not mes_inc.empty:
            fig.add_annotation(
                x=mes_inc.iloc[0]["mes_label"], y=mes_inc.iloc[0][f"casos_{ano_sel}"],
                text="mês incompleto", showarrow=True, arrowhead=2,
                font=dict(color="#8b949e", size=10), arrowcolor="#8b949e", ay=-30,
            )
    tb_layout(fig, altura=H_LARGE)
    fig.update_layout(
        xaxis=dict(title=""), yaxis=dict(title="Nº de casos"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=""),
        bargap=0.3,
    )
    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": False})
    st.caption("🔴 Para Mais  |  🟢 Para Menos  |  🟡 Estável  |  ⬜ Mês incompleto"
               f"  |  Linha azul = média {anos_hist[0]}–{anos_hist[-1]}")


def fig_tendencia_anual(df_hist: dict, ano_sel: int) -> None:
    """Evolução anual de casos."""
    anual = df_hist["anual"].sort_values("nu_ano")
    anual["cor"] = anual["nu_ano"].apply(
        lambda a: "#da3633" if str(a) == str(ano_sel) else "#58a6ff"
    )
    fig = go.Figure(go.Bar(
        x=anual["nu_ano"], y=anual["casos"],
        marker_color=anual["cor"],
        marker_line_color="#0d1117", marker_line_width=1,
        text=anual["casos"].apply(lambda v: f"{v:,}".replace(",", ".")),
        textposition="outside", textfont=dict(color="#c9d1d9", size=11),
        hovertemplate="<b>Ano %{x}</b><br>Total: %{y:,} casos<extra></extra>",
    ))
    tb_layout(fig, altura=350)
    fig.update_layout(xaxis=dict(title="Ano"), yaxis=dict(title="Total de casos"),
                      showlegend=False)
    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": False})


def fig_tendencia_uf(df_filtrado: pd.DataFrame, df_hist: dict,
                      ano_sel: int, anos_hist: list[int]) -> None:
    """Variação por estado vs média histórica."""
    if "uf_sigla" not in df_filtrado.columns:
        grafico_vazio()
        return
    uf_ano  = df_filtrado.groupby("uf_sigla").size().reset_index(name=f"casos_{ano_sel}")
    df_est  = df_hist["estadual"]
    uf_hist_anos = df_est[df_est["nu_ano"].astype(str).isin([str(a) for a in anos_hist])]
    uf_hist = (uf_hist_anos.groupby("uf_sigla")["casos"]
               .sum().reset_index(name="total_hist"))
    uf_hist["media_hist_uf"] = (uf_hist["total_hist"] / len(anos_hist)).round(0)
    uf_comp = uf_ano.merge(uf_hist[["uf_sigla", "media_hist_uf"]], on="uf_sigla", how="outer").fillna(0)
    uf_comp["variacao"] = ((uf_comp[f"casos_{ano_sel}"] - uf_comp["media_hist_uf"])
                           / uf_comp["media_hist_uf"].replace(0, 1) * 100).round(1)
    uf_comp["direcao"]  = uf_comp["variacao"].apply(
        lambda v: "Para Mais ⬆️" if v > 5 else ("Para Menos ⬇️" if v < -5 else "Estável ➡️")
    )
    uf_comp = uf_comp[uf_comp["uf_sigla"] != "?"].sort_values("variacao", ascending=True)
    cor_map = {"Para Mais ⬆️": "#da3633", "Estável ➡️": "#d29922", "Para Menos ⬇️": "#3fb950"}
    fig = px.bar(uf_comp, x="variacao", y="uf_sigla", orientation="h",
                 color="direcao", color_discrete_map=cor_map,
                 labels={"variacao": "Variação %", "uf_sigla": "Estado", "direcao": "Tendência"},
                 text="variacao")
    fig.update_traces(
        texttemplate="%{text:+.1f}%", textposition="outside",
        textfont=dict(color="#c9d1d9", size=10),
        hovertemplate=(f"<b>%{{y}}</b><br>{ano_sel}: %{{customdata[0]:,}} casos<br>"
                       "Média histórica: %{{customdata[1]:,.0f}}<br>"
                       "Variação: %{{x:+.1f}}%<extra></extra>"),
        customdata=uf_comp[[f"casos_{ano_sel}", "media_hist_uf"]].values,
        marker_line_color="#0d1117", marker_line_width=1,
    )
    fig.add_vline(x=0, line_color="#58a6ff", line_width=1.5, line_dash="dot")
    tb_layout(fig, altura=620)
    fig.update_layout(
        xaxis=dict(title=f"Variação % vs média {anos_hist[0]}–{anos_hist[-1]}", zeroline=False),
        yaxis=dict(title=""),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=""),
    )
    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": False})


# ══════════════════════════════════════════════════════════════════════════════
#  RECOMENDAÇÕES RAQUEL — Pirâmide de óbitos + Desfecho por HIV + Indicadores
# ══════════════════════════════════════════════════════════════════════════════

def fig_piramide_obitos(df: pd.DataFrame) -> go.Figure | None:
    """Pirâmide etária dos ÓBITOS por TB (Raquel ponto 5)."""
    col_enc = "situacao_enc_norm" if "situacao_enc_norm" in df.columns else "situacao_encerramento"
    if col_enc not in df.columns or "idade_anos" not in df.columns or "sexo" not in df.columns:
        return None

    df_ob = df[df[col_enc].astype(str).str.lower().str.contains("obito por tb", na=False)].copy()
    if df_ob.empty:
        return None

    bins   = [0, 15, 25, 35, 45, 55, 65, 200]
    labels = ["0-14", "15-24", "25-34", "35-44", "45-54", "55-64", "65+"]
    df_ob["faixa"] = pd.cut(
        df_ob["idade_anos"].astype("Int64"), bins=bins, labels=labels, right=False
    )
    df_ob = df_ob[df_ob["sexo"].isin(["Masculino", "Feminino"])]
    pir = df_ob.groupby(["faixa", "sexo"], observed=True).size().reset_index(name="casos")
    pir["valor"] = pir.apply(
        lambda r: -r["casos"] if r["sexo"] == "Masculino" else r["casos"], axis=1
    )

    fig = go.Figure()
    for sexo, cor in [("Masculino", "#58a6ff"), ("Feminino", "#f778ba")]:
        d = pir[pir["sexo"] == sexo]
        fig.add_trace(go.Bar(
            name=sexo, y=d["faixa"].astype(str), x=d["valor"],
            orientation="h", marker_color=cor,
            text=d["casos"].apply(lambda v: f"{v:,}"),
            textposition="inside", insidetextanchor="middle",
            textfont=dict(color="white", size=11),
            hovertemplate=(
                "<b>Faixa: %{y}</b><br>" + sexo +
                ": <b>%{customdata:,}</b> óbitos<extra></extra>"
            ),
            customdata=d["casos"],
        ))
    fig.update_layout(
        barmode="relative",
        xaxis=dict(title="Número de óbitos por TB",
                   gridcolor="rgba(255,255,255,0.08)"),
        yaxis=dict(title="Faixa etária", gridcolor="rgba(255,255,255,0.08)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5, xanchor="center"),
        hoverlabel=HOVER_LABEL, margin=dict(l=20, r=20, t=30, b=20),
        height=400, **BG,
    )
    return fig


def fig_desfecho_por_hiv(df: pd.DataFrame) -> None:
    """
    Desfecho do tratamento por status HIV (Raquel ponto 6).
    HIV+ tem piores desfechos (mais óbito e abandono).
    """
    col_hiv = "status_hiv"
    col_enc = "situacao_enc_norm" if "situacao_enc_norm" in df.columns else "situacao_encerramento"

    if col_hiv not in df.columns or col_enc not in df.columns:
        grafico_vazio()
        return

    hiv_order = ["Positivo", "Negativo", "Em andamento", "Não realizado", "Ignorado"]
    enc_order = ["Cura", "Obito por TB", "Obito por outras causas",
                 "Abandono", "Abandono Primario", "Transferencia", "Falencia", "TB-DR"]
    enc_labels = {
        "Cura":                  "Cura",
        "Obito por TB":          "Óbito por TB",
        "Obito por outras causas":"Óbito outras causas",
        "Abandono":              "Abandono",
        "Abandono Primario":     "Abandono Primário",
        "Transferencia":         "Transferência",
        "Falencia":              "Falência",
        "TB-DR":                 "TB-DR",
    }
    cor_enc = {
        "Cura":                  "#2ea043",
        "Óbito por TB":          "#da3633",
        "Óbito outras causas":   "#8957e5",
        "Abandono":              "#d29922",
        "Abandono Primário":     "#bb8009",
        "Transferência":         "#58a6ff",
        "Falência":              "#f85149",
        "TB-DR":                 "#cf222e",
    }

    df_plot = df[[col_hiv, col_enc]].copy()
    df_plot[col_enc] = df_plot[col_enc].astype(str).map(lambda x: NORMALIZAR_DESFECHO.get(x, x))
    df_plot[col_hiv] = df_plot[col_hiv].astype(str)
    df_plot = df_plot[
        df_plot[col_hiv].isin(hiv_order) &
        df_plot[col_enc].isin(enc_order)
    ]
    if df_plot.empty:
        grafico_vazio()
        return

    ct = (df_plot.groupby([col_hiv, col_enc]).size()
          .reset_index(name="n"))
    total_hiv = ct.groupby(col_hiv)["n"].sum().reset_index(name="total_hiv")
    ct = ct.merge(total_hiv, on=col_hiv)
    ct["pct"] = (ct["n"] / ct["total_hiv"] * 100).round(1)
    ct["enc_label"] = ct[col_enc].map(enc_labels).fillna(ct[col_enc])

    fig = px.bar(
        ct, x=col_hiv, y="pct", color="enc_label",
        color_discrete_map=cor_enc,
        labels={col_hiv: "Status HIV", "pct": "% dos casos", "enc_label": "Desfecho"},
        barmode="stack",
        category_orders={col_hiv: hiv_order},
        text="pct",
    )
    tb_layout(fig, altura=420)
    fig.update_traces(
        texttemplate="%{text:.0f}%",
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(color="white", size=10),
        hovertemplate="<b>HIV %{x}</b><br>%{data.name}: %{y:.1f}%<extra></extra>",
        marker_line_color="#0d1117", marker_line_width=1,
    )
    fig.update_layout(
        xaxis=dict(title="Status HIV"),
        yaxis=dict(title="% dos pacientes", ticksuffix="%"),
        legend=dict(orientation="v", x=1.01, y=0.5,
                    title="Desfecho", font=dict(size=11)),
        uniformtext_minsize=8, uniformtext_mode="hide",
    )
    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": False})


def fig_indicadores_historicos(df_ind: pd.DataFrame, sel_ind: list[str],
                                ano_sel: int) -> None:
    """
    Evolução histórica de indicadores clínicos — Série temporal (Raquel ponto 4).
    df_ind deve ter colunas: nu_ano, pct_cura, pct_abandon, pct_hiv, pct_obito,
    pct_novo, pct_pulm, pct_aids, pct_alcool, pct_tdo.
    """
    opcoes_col = {
        "Coeficiente de incidência (por 100 mil)": "incidencia_100k",
        "Coeficiente de mortalidade (por 100 mil)": "mortalidade_100k",
        "Taxa de cura (%)":           "pct_cura",
        "Taxa de abandono (%)":       "pct_abandon",
        "Coinfecção HIV (%)":         "pct_hiv",
        "Forma pulmonar (%)":         "pct_pulm",
        "Testagem para HIV (%)":      "pct_test_hiv",
        "TDO (%)":                    "pct_tdo",
        "Óbito por TB (%)":           "pct_obito",
        "Casos novos (%)":            "pct_novo",
    }
    cor_indicador = {
        "Coeficiente de incidência (por 100 mil)":  "#58a6ff",
        "Coeficiente de mortalidade (por 100 mil)": "#f85149",
        "Taxa de cura (%)":           "#3fb950",
        "Taxa de abandono (%)":       "#d29922",
        "Coinfecção HIV (%)":         "#da3633",
        "Forma pulmonar (%)":         "#79c0ff",
        "Testagem para HIV (%)":      "#a371f7",
        "TDO (%)":                    "#f0b342",
        "Óbito por TB (%)":           "#bb0000",
        "Casos novos (%)":            "#7ee787",
    }

    cols_disp = [c for c in sel_ind if opcoes_col.get(c) in df_ind.columns]
    if not cols_disp:
        st.info("Colunas de indicadores não encontradas no arquivo histórico.")
        return

    fig_ind = go.Figure()
    df_ind_sorted = df_ind.sort_values("nu_ano")
    df_ind_sorted["nu_ano"] = pd.to_numeric(df_ind_sorted["nu_ano"], errors="coerce").astype(int)
    for nome in cols_disp:
        col = opcoes_col[nome]
        fig_ind.add_trace(go.Scatter(
            x=df_ind_sorted["nu_ano"],
            y=df_ind_sorted[col],
            mode="lines+markers",
            name=nome,
            line=dict(color=cor_indicador.get(nome, "#58a6ff"), width=2.5),
            marker=dict(size=6, line=dict(color="#0d1117", width=1)),
            hovertemplate=f"<b>{nome}</b><br>Ano: %{{x}}<br>Valor: %{{y:.1f}}<extra></extra>",
        ))
    # Destaca ano selecionado (eixo numerico — add_vline funciona normalmente)
    anos_disp = df_ind_sorted["nu_ano"].tolist()
    if ano_sel in anos_disp:
        fig_ind.add_vline(
            x=ano_sel, line_dash="dot",
            line_color="#f78166", line_width=1.5,
            annotation_text=str(ano_sel),
            annotation_font=dict(color="#f78166", size=11),
        )
    tb_layout(fig_ind, altura=420)
    fig_ind.update_layout(
        xaxis=dict(title="Ano", tickangle=-45),
        yaxis=dict(title="Valor"),
        legend=dict(orientation="v", x=1.01, y=0.5, title="Indicador",
                    font=dict(size=11)),
        hovermode="x unified",
    )
    st.plotly_chart(fig_ind, use_container_width=True, config={"scrollZoom": False})
