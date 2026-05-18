"""
app.py
──────
Ponto de entrada do Streamlit.
Responsável apenas pelo layout e navegação — toda a lógica fica em src/.

Para rodar localmente:
    streamlit run app.py
"""

import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

from src.constantes import (
    SPEC_PATH, COLUNAS_ANALISE, PLOTLY_CFG,
    anos_disponiveis, parquet_path,
)
from src.dados import (
    carregar_dados, carregar_geojson,
    selecionar_colunas, gerar_html_pygwalker,
)
from src import graficos

st.set_page_config(
    page_title="Tuberculose Brasil - SINAN",
    page_icon=":lungs:",
    layout="wide",
)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("Filtros")

    # Ano
    anos = anos_disponiveis()
    ano_sel = st.selectbox(
        "Ano de notificacao",
        options=anos,
        index=0,
        help="Cada ano corresponde a um arquivo Parquet em dados_dashboard/.",
    )

    path_sel = parquet_path(ano_sel)
    if not path_sel.exists():
        st.error(
            f"Dados de {ano_sel} nao encontrados.\n\n"
            f"Execute:\n"
            f"```\npython scripts/conectar_banco.py {ano_sel}\n"
            f"python scripts/preparar_dados.py {ano_sel}\n```"
        )
        st.stop()

    # Carrega dados completos do ano
    df_completo = carregar_dados(str(path_sel))

    st.divider()

    # Estado
    estados_disponiveis = sorted(
        df_completo["estado_notificacao"].dropna().unique().tolist()
    )
    estados_sel = st.multiselect(
        "Estado (UF)",
        options=estados_disponiveis,
        default=[],
        placeholder="Todos os estados",
    )

    # Sexo
    sexos = ["Todos"] + sorted(
        df_completo["sexo"].dropna().unique().tolist()
    ) if "sexo" in df_completo.columns else ["Todos"]
    sexo_sel = st.selectbox("Sexo", options=sexos)

    # Forma clínica
    if "forma" in df_completo.columns:
        formas = ["Todas"] + sorted(
            [v for v in df_completo["forma"].dropna().unique().tolist()
             if v not in ("Nao informado", "Ignorado")]
        )
        forma_sel = st.selectbox("Forma Clinica", options=formas)
    else:
        forma_sel = "Todas"

    # Tipo de entrada
    if "tipo_entrada" in df_completo.columns:
        entradas = ["Todos"] + sorted(
            [v for v in df_completo["tipo_entrada"].dropna().unique().tolist()
             if v not in ("Nao informado", "Ignorado")]
        )
        entrada_sel = st.selectbox("Tipo de Entrada", options=entradas)
    else:
        entrada_sel = "Todos"

    st.divider()
    st.caption("Fonte: SINAN NET — Ministerio da Saude")

# ── Aplicação dos filtros ──────────────────────────────────────────────────────
df = df_completo.copy()

if estados_sel:
    df = df[df["estado_notificacao"].isin(estados_sel)]
if sexo_sel != "Todos":
    df = df[df["sexo"] == sexo_sel]
if forma_sel != "Todas":
    df = df[df["forma"] == forma_sel]
if entrada_sel != "Todos":
    df = df[df["tipo_entrada"] == entrada_sel]

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
st.title(f"Tuberculose no Brasil — SINAN {ano_sel}")

filtros_ativos = sum([
    bool(estados_sel),
    sexo_sel != "Todos",
    forma_sel != "Todas",
    entrada_sel != "Todos",
])

total = len(df_completo)
filtrado = len(df)
pct = round(100 * filtrado / total, 1) if total else 0

if filtros_ativos:
    st.caption(
        f"{filtrado:,} de {total:,} notificacoes ({pct}%)  |  "
        f"{df['estado_notificacao'].nunique()} estados  |  "
        f"{filtros_ativos} filtro(s) ativo(s)"
    )
else:
    st.caption(
        f"{total:,} notificacoes  |  "
        f"{df_completo['estado_notificacao'].nunique()} estados"
    )

if filtrado == 0:
    st.warning("Nenhum registro encontrado com os filtros selecionados. Ajuste os filtros na sidebar.")
    st.stop()

tab_paineis, tab_livre = st.tabs(["Paineis", "Analise Livre"])

# ── ABA: PAINEIS ───────────────────────────────────────────────────────────────
with tab_paineis:

    # Mapa
    st.subheader("Casos por Estado")
    st.caption("Cada estado colorido pela quantidade de notificacoes.")
    try:
        geojson = carregar_geojson()
        st.plotly_chart(
            graficos.fig_mapa(df, geojson),
            use_container_width=True, config=PLOTLY_CFG,
        )
    except FileNotFoundError:
        st.warning("GeoJSON nao encontrado. Execute: python scripts/baixar_geojson.py")

    st.divider()

    # Pirâmide + Desfechos
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Piramide Etaria")
        st.caption("Distribuicao dos casos por faixa etaria e sexo.")
        st.plotly_chart(
            graficos.fig_piramide(df),
            use_container_width=True, config=PLOTLY_CFG,
        )
    with col2:
        st.subheader("Desfechos do Tratamento")
        st.caption("Situacao de encerramento dos casos.")
        st.plotly_chart(
            graficos.fig_desfechos(df),
            use_container_width=True, config=PLOTLY_CFG,
        )

    st.divider()

    # Raça/Cor + Forma Clínica
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Casos por Raca/Cor")
        st.caption("Distribuicao segundo raca ou cor declarada.")
        fig = graficos.fig_raca_cor(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CFG)
        else:
            st.info("Coluna 'raca_cor' nao encontrada nos dados.")

    with col4:
        st.subheader("Forma Clinica")
        st.caption("Classificacao por apresentacao clinica.")
        fig = graficos.fig_forma_clinica(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CFG)
        else:
            st.info("Coluna 'forma' nao encontrada nos dados.")

    st.divider()

    # Agravos
    st.subheader("Agravos Associados")
    st.caption("Percentual dos casos com cada agravo ou condicao associada.")
    fig = graficos.fig_agravos(df)
    if fig:
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CFG)
    else:
        st.info("Colunas de agravos nao encontradas nos dados.")

    st.divider()

    # Populações
    st.subheader("Populacoes em Situacao de Vulnerabilidade")
    st.caption("Percentual dos casos em grupos populacionais prioritarios.")
    fig = graficos.fig_populacoes(df)
    if fig:
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CFG)
    else:
        st.info("Colunas de populacoes nao encontradas nos dados.")

# ── ABA: ANALISE LIVRE ─────────────────────────────────────────────────────────
with tab_livre:
    st.subheader("Analise Livre")
    st.caption("Monte seus proprios graficos arrastando e soltando os campos.")

    df_analise = selecionar_colunas(df, COLUNAS_ANALISE)
    st.info(
        f"**{len(df_analise):,}** registros  |  "
        f"**{len(df_analise.columns)}** variaveis disponíveis",
        icon="📊",
    )

    spec = SPEC_PATH if Path(SPEC_PATH).exists() else None
    html = gerar_html_pygwalker(df_analise, spec_path=spec)
    components.html(html, height=1000, scrolling=True)

    if not spec:
        st.caption(
            "Dica: monte um grafico no PyGWalker acima, exporte a configuracao "
            "e salve como spec/dashboard_tb.json para carregar automaticamente."
        )
