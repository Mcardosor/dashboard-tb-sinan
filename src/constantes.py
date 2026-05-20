"""
constantes.py
─────────────
Mapeamentos, paletas de cores e configurações globais do dashboard.
Centraliza aqui tudo que é reutilizado em graficos.py e app.py.
"""

import streamlit as st
import pandas as pd
from pathlib import Path

# ── Caminhos ───────────────────────────────────────────────────────────────────
PASTA_DADOS  = Path("dados_dashboard")
PASTA        = PASTA_DADOS          # alias de compatibilidade
GEOJSON_PATH = PASTA_DADOS / "br_states.geojson"
SPEC_PATH    = "spec/dashboard_tb.json"

# Histórico pré-agregado (gerado por conectar_banco.py para múltiplos anos)
HIST_MENSAL      = PASTA_DADOS / "historico_mensal.csv"
HIST_ESTADUAL    = PASTA_DADOS / "historico_estadual.csv"
HIST_ANUAL       = PASTA_DADOS / "historico_anual.csv"
HIST_INDICADORES = PASTA_DADOS / "historico_indicadores.csv"
MUN_PARQUET      = PASTA_DADOS / "municipios.parquet"
MUN_URL = "https://raw.githubusercontent.com/kelvins/municipios-brasileiros/main/csv/municipios.csv"

ANO_ATUAL  = 2025
ANO_INICIO = 2001


def parquet_path(ano: int) -> Path:
    """Retorna o caminho do Parquet tratado para um dado ano."""
    return PASTA_DADOS / f"sinan_tube_{ano}_tratado.parquet"


def anos_disponiveis() -> list[int]:
    """Detecta automaticamente quais anos têm Parquet tratado disponível."""
    arquivos = sorted(PASTA_DADOS.glob("sinan_tube_*_tratado.parquet"), reverse=True)
    anos = []
    for f in arquivos:
        try:
            ano = int(f.stem.split("_")[2])
            anos.append(ano)
        except (IndexError, ValueError):
            pass
    return anos if anos else [2025]


# ── Mapeamento de estados → siglas ─────────────────────────────────────────────
UF_SIGLAS = {
    "Acre": "AC", "Alagoas": "AL", "Amapa": "AP", "Amazonas": "AM",
    "Bahia": "BA", "Ceara": "CE", "Distrito Federal": "DF", "Espirito Santo": "ES",
    "Goias": "GO", "Maranhao": "MA", "Mato Grosso": "MT", "Mato Grosso do Sul": "MS",
    "Minas Gerais": "MG", "Para": "PA", "Paraiba": "PB", "Parana": "PR",
    "Pernambuco": "PE", "Piaui": "PI", "Rio de Janeiro": "RJ",
    "Rio Grande do Norte": "RN", "Rio Grande do Sul": "RS", "Rondonia": "RO",
    "Roraima": "RR", "Santa Catarina": "SC", "Sao Paulo": "SP",
    "Sergipe": "SE", "Tocantins": "TO",
    # Com acentos
    "Amapá": "AP", "Ceará": "CE", "Espírito Santo": "ES", "Goiás": "GO",
    "Maranhão": "MA", "Pará": "PA", "Paraíba": "PB", "Piauí": "PI",
    "Rondônia": "RO", "São Paulo": "SP", "Paraná": "PR",
}

# ── Agravos associados ─────────────────────────────────────────────────────────
AGRAVOS = {
    "agravo_aids":            "AIDS/HIV",
    "agravo_alcoolismo":      "Alcoolismo",
    "agravo_diabetes":        "Diabetes",
    "agravo_doenca_mental":   "Doenca Mental",
    "agravo_drogas_ilicitas": "Drogas Ilicitas",
    "agravo_tabagismo":       "Tabagismo",
}

# ── Populações vulneráveis ─────────────────────────────────────────────────────
POPULACOES = {
    "populacao_privada_liberdade": "Privada de Liberdade",
    "populacao_situacao_rua":      "Situacao de Rua",
    "populacao_imigrante":         "Imigrante",
    "profissional_saude":          "Profissional de Saude",
    "beneficiario_governo":        "Beneficiario Prog. Social",
}

# ── Normalização de desfechos ──────────────────────────────────────────────────
NORMALIZAR_DESFECHO = {
    "Nao informado":           "Em acompanhamento",
    "Não informado":           "Em acompanhamento",
    "Óbito por TB":            "Obito por TB",
    "Óbito por outras causas": "Obito por outras causas",
    "Mudança de Esquema":      "Mudanca de Esquema",
    "Abandono Primário":       "Abandono Primario",
    "Transferência":           "Transferencia",
    "Falência":                "Falencia",
}

# ── Paletas de cores legadas (mantidas para fig_mapa / fig_piramide) ───────────
CORES_DESFECHOS = {
    "Cura":                    "#2ea043",
    "Em acompanhamento":       "#388bfd",
    "Transferencia":           "#58a6ff",
    "Mudanca de Esquema":      "#d29922",
    "Abandono Primario":       "#bb8009",
    "Abandono":                "#f0883e",
    "Falencia":                "#f85149",
    "TB-DR":                   "#a371f7",
    "Obito por outras causas": "#8957e5",
    "Obito por TB":            "#da3633",
}

CORES_RACA = {
    "Parda":    "#d2a8ff", "Branca": "#79c0ff",
    "Preta":    "#a371f7", "Amarela": "#f0b342", "Indigena": "#3fb950",
    "Indígena": "#3fb950",
}

CORES_FORMA = {
    "Pulmonar":                 "#58a6ff",
    "Extrapulmonar":            "#a371f7",
    "Pulmonar + Extrapulmonar": "#d2a8ff",
}

ESCALA_MAPA = [
    [0.0,  "#0d1117"], [0.15, "#1f4d8a"],
    [0.35, "#1f6feb"], [0.55, "#58a6ff"],
    [0.75, "#a5d6ff"], [1.0,  "#cae8ff"],
]

# ── Paleta TB — semântica epidemiológica ──────────────────────────────────────
TB_COLORS = {
    # Desfecho clínico
    "Cura":                     "#2ea043",
    "Óbito por TB":             "#da3633",
    "Obito por TB":             "#da3633",
    "Óbito outras causas":      "#8957e5",
    "Obito por outras causas":  "#8957e5",
    "Abandono":                 "#d29922",
    "Abandono Primario":        "#bb8009",
    "Abandono Primário":        "#bb8009",
    "Falencia":                 "#f85149",
    "Falência":                 "#f85149",
    "TB-DR":                    "#cf222e",
    "Transferencia":            "#1f6feb",
    "Transferência":            "#1f6feb",
    "Mudanca de Esquema":       "#8b949e",
    "Mudança de Esquema":       "#8b949e",
    "Mudança Diagnóstico":      "#6e7681",
    "Em acompanhamento":        "#388bfd",
    # HIV
    "Positivo":                 "#da3633",
    "Negativo":                 "#3fb950",
    "Em andamento":             "#d29922",
    "Não realizado":            "#6e7681",
    "Nao realizado":            "#6e7681",
    # Sexo
    "Masculino":                "#58a6ff",
    "Feminino":                 "#f778ba",
    # Sim/Não
    "Sim":                      "#da3633",
    "Não":                      "#3fb950",
    "Nao":                      "#3fb950",
    "Ignorado":                 "#6e7681",
    # Baciloscopia / TMR
    "Positiva":                 "#da3633",
    "Negativa":                 "#3fb950",
    "Não realizada":            "#6e7681",
    "Nao realizada":            "#6e7681",
    "Não se aplica":            "#484f58",
    "Detectável sensível":      "#d29922",
    "Detectavel sensivel":      "#d29922",
    "Detectável resistente":    "#da3633",
    "Detectavel resistente":    "#da3633",
    "Não detectável":           "#3fb950",
    "Nao detectavel":           "#3fb950",
    "Inconclusivo":             "#8b949e",
    # Raça
    "Branca":                   "#79c0ff",
    "Preta":                    "#a371f7",
    "Parda":                    "#d2a8ff",
    "Amarela":                  "#f0b342",
    "Indígena":                 "#3fb950",
    "Indigena":                 "#3fb950",
    # Forma clínica
    "Pulmonar":                       "#58a6ff",
    "Extrapulmonar":                  "#a371f7",
    "Pulmonar + Extrapulmonar":       "#d2a8ff",
    # Tipo de entrada
    "Caso Novo":                "#3fb950",
    "Recidiva":                 "#d29922",
    "Reingresso Abandono":      "#f0883e",
    "Não Sabe":                 "#6e7681",
    "Nao Sabe":                 "#6e7681",
    "Pos-obito":                "#a40e26",
    "Pós-óbito":                "#a40e26",
}

# Paletas sequenciais para mapas
TB_SEQ_INCIDENCIA = ["#0d1117", "#1f4d8a", "#1f6feb", "#58a6ff", "#79c0ff", "#a5d6ff"]
TB_SEQ_MORTAL     = ["#0d1117", "#67060c", "#a40e26", "#da3633", "#f85149", "#ffa198"]

# Sequência para categorias sem cor semântica definida
CORES = ["#58a6ff", "#a371f7", "#3fb950", "#d29922", "#f778ba", "#79c0ff", "#d2a8ff"]


def tb_color_map(labels: list[str]) -> dict:
    """Mapeia lista de labels para cores TB (fallback determinístico)."""
    mapping = {}
    fallback_idx = 0
    for lbl in labels:
        if lbl in TB_COLORS:
            mapping[lbl] = TB_COLORS[lbl]
        else:
            mapping[lbl] = CORES[fallback_idx % len(CORES)]
            fallback_idx += 1
    return mapping


# ── Template Plotly padronizado ────────────────────────────────────────────────
PLOTLY_TEMPLATE = {
    "layout": {
        "font": {"family": "Inter, -apple-system, system-ui, sans-serif",
                 "color": "#c9d1d9", "size": 12},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor":  "rgba(0,0,0,0)",
        "title": {"font": {"size": 15, "color": "#f0f6fc", "family": "Inter, sans-serif"},
                  "x": 0.02, "xanchor": "left", "pad": {"t": 10, "b": 5}},
        "xaxis": {"gridcolor": "#21262d", "linecolor": "#30363d",
                  "tickfont": {"color": "#8b949e", "size": 11},
                  "title_font": {"color": "#c9d1d9", "size": 12}},
        "yaxis": {"gridcolor": "#21262d", "linecolor": "#30363d",
                  "tickfont": {"color": "#8b949e", "size": 11},
                  "title_font": {"color": "#c9d1d9", "size": 12}},
        "legend": {"bgcolor": "rgba(22,27,34,.7)", "bordercolor": "#30363d",
                   "borderwidth": 1, "font": {"color": "#c9d1d9", "size": 11}},
        "hoverlabel": {"bgcolor": "#161b22", "bordercolor": "#30363d",
                       "font": {"color": "#f0f6fc", "family": "Inter, sans-serif"}},
        "margin": {"l": 50, "r": 30, "t": 50, "b": 50},
    }
}

# Mantido para compatibilidade com graficos.py legado
BG = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor":  "rgba(0,0,0,0)",
}
HOVER_LABEL = dict(
    bgcolor="rgba(30,30,40,0.95)",
    bordercolor="rgba(255,255,255,0.15)",
    font=dict(size=13),
)
PLOTLY_CFG = {"scrollZoom": False}


def tb_layout(fig, titulo=None, altura=None):
    """Aplica template TB padronizado em uma figura Plotly."""
    fig.update_layout(**PLOTLY_TEMPLATE["layout"])
    if titulo:
        fig.update_layout(title_text=titulo)
    if altura:
        fig.update_layout(height=altura)
    return fig


# ── Alturas padrão de gráficos ─────────────────────────────────────────────────
H_SMALL  = 300
H_MEDIUM = 380
H_LARGE  = 480

# ── População por estado — IBGE Censo 2022 ─────────────────────────────────────
POP_ESTADO = {
    "AC":    906_876,   "AL":  3_127_683,  "AM":  4_269_995,
    "AP":    877_613,   "BA": 14_873_064,  "CE":  9_240_580,
    "DF":  3_094_325,   "ES":  4_108_508,  "GO":  7_206_589,
    "MA":  7_114_598,   "MG": 21_292_666,  "MS":  2_839_188,
    "MT":  3_658_813,   "PA":  8_777_124,  "PB":  4_059_905,
    "PE":  9_674_793,   "PI":  3_281_480,  "PR": 11_597_484,
    "RJ": 17_366_189,   "RN":  3_302_406,  "RO":  1_590_011,
    "RR":    652_713,   "RS": 11_466_630,  "SC":  7_786_786,
    "SE":  2_338_474,   "SP": 46_649_132,  "TO":  1_607_363,
}
POP_BRASIL = sum(POP_ESTADO.values())

# ── Colunas expostas na Análise Livre ─────────────────────────────────────────
COLUNAS_ANALISE = (
    "estado_notificacao", "municipio_notificacao", "uf_residencia",
    "ano_notificacao", "data_notificacao", "data_diagnostico",
    "data_inicio_tratamento", "data_encerramento",
    "idade_anos", "sexo", "raca_cor", "escolaridade",
    "tipo_entrada", "forma", "situacao_encerramento",
    "status_hiv", "uso_antirretroviral", "raio_x_torax",
    "baciloscopia_primeira_amostra", "cultura_escarro",
    "histopatologia", "teste_molecular", "teste_sensibilidade",
    "tratamento_supervisionado",
    "baciloscopia_mes_1", "baciloscopia_mes_2", "baciloscopia_mes_3",
    "baciloscopia_mes_4", "baciloscopia_mes_5", "baciloscopia_mes_6",
    "baciloscopia_apos_6_meses",
    "agravo_aids", "agravo_alcoolismo", "agravo_diabetes",
    "agravo_doenca_mental", "agravo_drogas_ilicitas", "agravo_tabagismo",
    "populacao_privada_liberdade", "populacao_situacao_rua",
    "profissional_saude", "populacao_imigrante", "beneficiario_governo",
    "numero_contatos", "numero_contatos_examinados",
)

# ── Helpers ────────────────────────────────────────────────────────────────────
def pct(valor, total):
    return f"{valor/total*100:.1f}%" if total and total > 0 else "—"


def grafico_vazio():
    st.info("Nenhum dado disponível para os filtros selecionados.")


# ── KPI Card builder ───────────────────────────────────────────────────────────
def _delta_badge(cur, prev, good_when_up=False):
    try:
        cur, prev = float(cur), float(prev)
        if prev == 0:
            return ""
        diff_pct = (cur - prev) / prev * 100
        if abs(diff_pct) < 0.1:
            return '<span class="kpi-delta flat">≈ estável vs ano anterior</span>'
        arrow = "↑" if diff_pct > 0 else "↓"
        cls   = "good" if (diff_pct > 0) == good_when_up else "bad"
        return f'<span class="kpi-delta {cls}">{arrow} {abs(diff_pct):.1f}% vs ano anterior</span>'
    except Exception:
        return ""


def kpi_card_html(title, value, delta_html, icon, accent, selected):
    sel   = "kpi-selected" if selected else ""
    delta = delta_html.strip() if delta_html else ""
    return (
        f'<div class="kpi-card {sel}" style="--accent:{accent};">'
        f'<div class="kpi-inner">'
        f'<div class="kpi-bar"></div>'
        f'<div class="kpi-body">'
        f'<div class="kpi-label">{title}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'{delta}'
        f'</div>'
        f'<div class="kpi-icon">{icon}</div>'
        f'</div>'
        f'</div>'
    )
