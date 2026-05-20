# Relatório de Progresso — 18/05/2026

**Projeto:** Dashboard de Vigilância Epidemiológica — Tuberculose no Brasil (SINAN NET)
**Repositório:** `dashboard-tb-sinan`
**Responsável:** Matheus Cardoso
**Apresentação:** Segunda-feira 18/05/2026 (hoje)

---

## Resumo do Dia

Sessão de finalização antes do seminário. Duas entregas principais: (1) migração visual completa do dashboard para o design superior do projeto anterior e (2) implementação das 6 recomendações de melhoria levantadas pela colaboradora Raquel após revisão do sistema.

---

## O que foi feito

### 1. Migração Visual Completa

Trouxe o design do `dashboard-tuberculose-completinho` para o novo repositório unificado `dashboard-tb-sinan`, mantendo a arquitetura modular já implementada.

**Visual implementado:**
- CSS dark theme completo (estilo GitHub Dark) injetado via `st.markdown`
- **Hero header** com gradiente tricolor e badges dinâmicos (ano, registros, período)
- **8 KPI cards** clicáveis com barra lateral colorida, glow ao selecionar e badge de variação vs ano anterior
- Tabs estilizadas com fundo pill-shaped e highlight laranja
- Sidebar expandida em 5 seções colapsáveis

**Mapa interativo (Folium):**
- Choropleth com tema CartoDB dark matter
- Tooltip estilizado ao hover (fundo escuro, fonte monospace)
- 3 métricas selecionáveis pelos KPI cards: Total de Casos · Incidência · Mortalidade (ambas por 100 mil hab.)
- Fallback automático para Plotly se Folium não estiver disponível

### 2. Refatoração dos Módulos `src/`

| Arquivo | Antes | Depois | Principais adições |
|---|---|---|---|
| `src/constantes.py` | 141 linhas | 342 linhas | `TB_COLORS`, `POP_ESTADO`, `tb_layout()`, `kpi_card_html()`, helpers |
| `src/dados.py` | 45 linhas | 116 linhas | `enriquecer_df()`, `load_historico()`, `load_municipios()` |
| `src/graficos.py` | 260 linhas | 734 linhas | +8 novas funções de gráfico |
| `app.py` | 242 linhas | 776 linhas | Reescrita completa |

**Novas funções em `graficos.py`:**
- `safe_pie()` — donut chart com paleta semântica TB
- `safe_bar_h()` / `safe_bar_v()` — barras horizontal/vertical com cores clínicas
- `fig_coinfeccao_hiv_uf()` — coinfecção TB-HIV por estado (%)
- `fig_comorbidades()` / `fig_comorbidades_uf()` — comorbidades com detalhamento estadual
- `fig_tendencia_mensal()` — comparativo mensal com média histórica
- `fig_tendencia_anual()` — evolução anual total
- `fig_tendencia_uf()` — variação por estado vs histórico
- `fig_piramide_obitos()` — pirâmide etária dos óbitos por TB *(novo)*
- `fig_desfecho_por_hiv()` — desfechos por status HIV *(novo)*
- `fig_indicadores_historicos()` — série temporal de indicadores com multiselect *(novo)*

### 3. Dashboard com 6 abas completas

| Aba | Conteúdo |
|---|---|
| 🗺️ Distribuição Geográfica | Mapa Folium + ranking por estado |
| 👥 Perfil dos Pacientes | Sexo, forma clínica, tipo de entrada, raça/cor, 2 pirâmides etárias |
| 🏥 Clínico & Diagnóstico | HIV, baciloscopia, TMR-TB, desfecho por HIV, coinfecção por estado |
| ⚠️ Comorbidades & Vulnerabilidades | Comorbidades, populações vulneráveis, breakdown estadual |
| 📈 Tendência Histórica | Mensal vs histórico, evolução anual, variação por estado, indicadores |
| 🔬 Análise Livre | PyGWalker interativo |

### 4. Implementação das 6 Recomendações da Raquel

Revisão realizada por colaboradora da área de epidemiologia. Todas as 6 sugestões foram implementadas:

| # | Recomendação | Status | Implementação |
|---|---|---|---|
| 1 | Padronizar "por 100 mil hab." (em vez de "100k") | ✅ | KPI cards, legendas do mapa, eixos e tooltips |
| 2 | Reordenar KPI cards (incid. · mort. · óbitos · HIV / cura · abandon. · total · municípios) | ✅ | Reordenação + renomeação "Municípios prioritários" |
| 3 | Especificar unidade/métrica em todos os títulos de gráfico | ✅ | Subtítulos explícitos com `st.caption` em todos os charts |
| 4 | Adicionar série temporal dos 10 indicadores principais da TB | ✅ | Multiselect + `fig_indicadores_historicos()` na aba Tendência |
| 5 | Pirâmide etária dos óbitos (além da de casos) | ✅ | `fig_piramide_obitos()` — exibidas lado a lado na aba Perfil |
| 6 | Gráfico "Desfecho por status HIV" | ✅ | Barra empilhada por HIV+/−/Em andamento — aba Clínico |

### 5. Dependências Adicionadas

```
folium >= 0.19
streamlit-folium >= 0.25
```

---

## Estado atual do projeto

```
dashboard-tb-sinan/
├── app.py                  ← entrada principal (776 linhas)
├── requirements.txt        ← 10 dependências
├── src/
│   ├── constantes.py       ← paletas, mapas, KPI helpers
│   ├── dados.py            ← carregamento, cache, enriquecimento
│   └── graficos.py         ← 15+ funções de visualização
├── scripts/
│   ├── conectar_banco.py   ← PostgreSQL → Parquet por ano
│   ├── preparar_dados.py   ← limpeza e enriquecimento
│   └── baixar_geojson.py   ← GeoJSON dos estados
├── dados_dashboard/
│   └── sinan_tube_2025_tratado.parquet   ← dados disponíveis
└── docs/
    ├── plano_semana.md
    ├── roteiro_apresentacao.md
    └── relatorio_2026-05-18.md
```

---

## Para rodar o dashboard hoje

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Próximos passos (pós-seminário)

- Conectar ao banco e exportar dados históricos (`python scripts/conectar_banco.py 2001 2024`)
- Habilitar aba de Tendência com comparativo histórico completo
- Mapa drill-down por município
- DuckDB para performance com múltiplos usuários
- Deploy em servidor com nginx

---

*Relatório gerado em 18/05/2026 — semana do seminário*
