"""
graficos.py
───────────
Uma função por gráfico Plotly. Cada função recebe um DataFrame
e retorna uma go.Figure pronta para st.plotly_chart().

Para adicionar um novo gráfico:
  1. Crie uma função fig_nome(df) aqui
  2. Importe e chame no app.py
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.constantes import (
    UF_SIGLAS, AGRAVOS, POPULACOES, NORMALIZAR_DESFECHO,
    CORES_DESFECHOS, CORES_RACA, CORES_FORMA,
    ESCALA_MAPA, BG, HOVER_LABEL,
)


# ── Mapa coroplético ──────────────────────────────────────────────────────────
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


# ── Pirâmide etária ────────────────────────────────────────────────────────────
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
    for sexo, cor in [("Masculino", "#3B82F6"), ("Feminino", "#F43F5E")]:
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
        xaxis=dict(
            tickvals=[-15000, -10000, -5000, 0, 5000, 10000],
            ticktext=["15k", "10k", "5k", "0", "5k", "10k"],
            title="Numero de casos", gridcolor="rgba(255,255,255,0.08)",
        ),
        yaxis=dict(title="Faixa etaria", gridcolor="rgba(255,255,255,0.08)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5, xanchor="center"),
        hoverlabel=HOVER_LABEL, margin=dict(l=20, r=20, t=30, b=20),
        height=420, **BG,
    )
    return fig


# ── Desfechos do tratamento ────────────────────────────────────────────────────
def fig_desfechos(df: pd.DataFrame) -> go.Figure:
    desfechos = (
        df["situacao_encerramento"].astype(str)
        .map(lambda x: NORMALIZAR_DESFECHO.get(x, x))
        .value_counts().reset_index()
        .rename(columns={"situacao_encerramento": "desfecho", "count": "casos"})
    )
    desfechos = desfechos.sort_values("casos", ascending=True)
    desfechos["pct"] = (desfechos["casos"] / desfechos["casos"].sum() * 100).round(1)

    fig = px.bar(
        desfechos, x="casos", y="desfecho", orientation="h",
        color="desfecho", color_discrete_map=CORES_DESFECHOS,
        custom_data=["pct"], labels={"casos": "Notificacoes", "desfecho": ""},
    )
    fig.update_traces(
        text=desfechos["casos"].apply(lambda v: f"{v:,}"),
        textposition="auto", insidetextanchor="middle",
        textfont=dict(color="white", size=12),
        hovertemplate=(
            "<b>%{y}</b><br>%{x:,} casos<br>%{customdata[0]}% do total<extra></extra>"
        ),
    )
    fig.update_layout(
        showlegend=False,
        xaxis=dict(title="Numero de casos", gridcolor="rgba(255,255,255,0.08)"),
        hoverlabel=HOVER_LABEL, margin=dict(l=10, r=20, t=10, b=20),
        height=420, **BG,
    )
    return fig


# ── Raça/Cor ───────────────────────────────────────────────────────────────────
def fig_raca_cor(df: pd.DataFrame) -> go.Figure | None:
    if "raca_cor" not in df.columns:
        return None
    raca = (
        df["raca_cor"].astype(str).value_counts().reset_index()
        .rename(columns={"raca_cor": "categoria", "count": "casos"})
    )
    raca = raca[~raca["categoria"].isin(["nan", "Nao informado", "Ignorado"])]
    raca = raca.sort_values("casos", ascending=True)
    raca["pct"] = (raca["casos"] / raca["casos"].sum() * 100).round(1)

    fig = px.bar(
        raca, x="casos", y="categoria", orientation="h",
        color="categoria", color_discrete_map=CORES_RACA,
        custom_data=["pct"], labels={"casos": "Notificacoes", "categoria": ""},
    )
    fig.update_traces(
        text=raca["casos"].apply(lambda v: f"{v:,}"),
        textposition="auto", insidetextanchor="middle",
        textfont=dict(color="white", size=12), marker_line_width=0,
        hovertemplate=(
            "<b>%{y}</b><br>%{x:,} casos<br>%{customdata[0]}% do total<extra></extra>"
        ),
    )
    fig.update_layout(
        showlegend=False,
        xaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
        hoverlabel=HOVER_LABEL, margin=dict(l=10, r=20, t=10, b=20),
        height=340, **BG,
    )
    return fig


# ── Forma clínica ──────────────────────────────────────────────────────────────
def fig_forma_clinica(df: pd.DataFrame) -> go.Figure | None:
    if "forma" not in df.columns:
        return None
    forma = (
        df["forma"].astype(str).value_counts().reset_index()
        .rename(columns={"forma": "categoria", "count": "casos"})
    )
    forma = forma[~forma["categoria"].isin(["nan", "Nao informado", "Ignorado"])]
    forma = forma.sort_values("casos", ascending=True)
    forma["pct"] = (forma["casos"] / forma["casos"].sum() * 100).round(1)

    fig = px.bar(
        forma, x="casos", y="categoria", orientation="h",
        color="categoria", color_discrete_map=CORES_FORMA,
        custom_data=["pct"], labels={"casos": "Notificacoes", "categoria": ""},
    )
    fig.update_traces(
        text=forma["casos"].apply(lambda v: f"{v:,}"),
        textposition="auto", insidetextanchor="middle",
        textfont=dict(color="white", size=12), marker_line_width=0,
        hovertemplate=(
            "<b>%{y}</b><br>%{x:,} casos<br>%{customdata[0]}% do total<extra></extra>"
        ),
    )
    fig.update_layout(
        showlegend=False,
        xaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
        hoverlabel=HOVER_LABEL, margin=dict(l=10, r=20, t=10, b=20),
        height=340, **BG,
    )
    return fig


# ── Helper interno: barras de percentual (agravos / populações) ────────────────
def _barras_percentual(
    df: pd.DataFrame,
    mapeamento: dict,
    escala_cores: list,
    height: int,
) -> go.Figure | None:
    total = len(df)
    dados = []
    for col, nome in mapeamento.items():
        if col in df.columns:
            n = (df[col].astype(str).str.strip().str.lower() == "sim").sum()
            dados.append({
                "categoria": nome,
                "casos": int(n),
                "percentual": round(100 * n / total, 1),
            })
    if not dados:
        return None

    df_d = pd.DataFrame(dados).sort_values("percentual", ascending=True)
    n = len(df_d)
    cores = [
        escala_cores[int(i * (len(escala_cores) - 1) / max(n - 1, 1))]
        for i in range(n)
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_d["percentual"], y=df_d["categoria"],
        orientation="h", marker=dict(color=cores, line_width=0),
        text=[f"{p}%  ({c:,})" for p, c in zip(df_d["percentual"], df_d["casos"])],
        textposition="auto", insidetextanchor="middle",
        textfont=dict(color="white", size=12),
        customdata=df_d[["casos", "percentual"]].values,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Percentual: <b>%{customdata[1]}%</b><br>"
            "Notificacoes: <b>%{customdata[0]:,}</b><extra></extra>"
        ),
    ))
    fig.update_layout(
        xaxis=dict(
            title="% dos casos", ticksuffix="%",
            range=[0, df_d["percentual"].max() * 1.35],
            gridcolor="rgba(255,255,255,0.08)",
        ),
        hoverlabel=HOVER_LABEL, yaxis_title="",
        margin=dict(l=10, r=20, t=10, b=30),
        height=height, **BG,
    )
    return fig


# ── Agravos associados ─────────────────────────────────────────────────────────
def fig_agravos(df: pd.DataFrame) -> go.Figure | None:
    return _barras_percentual(df, AGRAVOS, px.colors.sequential.Oranges, height=300)


# ── Populações vulneráveis ─────────────────────────────────────────────────────
def fig_populacoes(df: pd.DataFrame) -> go.Figure | None:
    return _barras_percentual(df, POPULACOES, px.colors.sequential.Blues, height=260)
