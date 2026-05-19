"""
constantes.py
─────────────
Mapeamentos, paletas de cores e configurações globais do dashboard.
Centraliza aqui tudo que é reutilizado em graficos.py e app.py.
"""

from pathlib import Path

# ── Caminhos ───────────────────────────────────────────────────────────────────
PASTA_DADOS  = Path("dados_dashboard")
GEOJSON_PATH = PASTA_DADOS / "br_states.geojson"
SPEC_PATH    = "spec/dashboard_tb.json"


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
    # Com acentos (como podem vir do SINAN)
    "Amapá": "AP", "Ceará": "CE", "Espírito Santo": "ES", "Goiás": "GO",
    "Maranhão": "MA", "Pará": "PA", "Paraíba": "PB", "Piauí": "PI",
    "Rondônia": "RO", "São Paulo": "SP", "Paraná": "PR",
}

# ── Populações por estado — IBGE Censo 2022 ───────────────────────────────────
POP_ESTADO: dict[str, int] = {
    "AC":    906_876,  "AL":  3_127_683,  "AM":  4_269_995,
    "AP":    877_613,  "BA": 14_873_064,  "CE":  9_240_580,
    "DF":  3_094_325,  "ES":  4_108_508,  "GO":  7_206_589,
    "MA":  7_114_598,  "MG": 21_292_666,  "MS":  2_839_188,
    "MT":  3_658_813,  "PA":  8_777_124,  "PB":  4_059_905,
    "PE":  9_674_793,  "PI":  3_281_480,  "PR": 11_597_484,
    "RJ": 17_366_189,  "RN":  3_302_406,  "RO":  1_590_011,
    "RR":    652_713,  "RS": 11_466_630,  "SC":  7_786_786,
    "SE":  2_338_474,  "SP": 46_649_132,  "TO":  1_607_363,
}
POP_BRASIL: int = sum(POP_ESTADO.values())  # ~203 milhões (Censo 2022)

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

# ── Normalização de desfechos (lida com acentos e variações do SINAN) ──────────
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

# ── Paletas de cores ───────────────────────────────────────────────────────────
CORES_DESFECHOS = {
    "Cura":                    "#22C55E",
    "Em acompanhamento":       "#94A3B8",
    "Transferencia":           "#60A5FA",
    "Mudanca de Esquema":      "#FB923C",
    "Abandono Primario":       "#FACC15",
    "Abandono":                "#F97316",
    "Falencia":                "#EF4444",
    "TB-DR":                   "#A855F7",
    "Obito por outras causas": "#DC2626",
    "Obito por TB":            "#7F1D1D",
}

CORES_RACA = {
    "Parda":    "#F59E0B", "Branca":   "#93C5FD",
    "Preta":    "#818CF8", "Amarela":  "#34D399", "Indigena": "#F472B6",
}

CORES_FORMA = {
    "Pulmonar":                 "#38BDF8",
    "Extrapulmonar":            "#818CF8",
    "Pulmonar + Extrapulmonar": "#F472B6",
}

ESCALA_MAPA = [
    [0.0,  "#FFF5F0"], [0.15, "#FDCBB7"],
    [0.35, "#FC8A6A"], [0.55, "#F14432"],
    [0.75, "#C0151A"], [1.0,  "#67000D"],
]

# ── Configurações Plotly ───────────────────────────────────────────────────────
PLOTLY_CFG  = {"scrollZoom": False}
BG          = {"paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": "rgba(0,0,0,0)"}
HOVER_LABEL = dict(
    bgcolor="rgba(30,30,40,0.95)",
    bordercolor="rgba(255,255,255,0.15)",
    font=dict(size=13),
)

# ── Colunas expostas na aba de Análise Livre (PyGWalker) ──────────────────────
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
