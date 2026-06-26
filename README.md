# Dashboard TB · SINAN NET

Painel interativo de vigilância epidemiológica da tuberculose no Brasil, com dados de notificação do SINAN NET cobrindo 2001 a 2026.

> **Acesso:** http://164.41.147.175:8502/cenarios/tb

---

## O que você encontra no painel

- **Visão geral** — KPIs em tempo real: incidência, mortalidade, óbitos, cura, abandono, coinfecção HIV
- **Distribuição Geográfica** — mapa coroplético por estado com drill-down para municípios
- **Perfil dos Pacientes** — sexo, raça/cor, faixa etária, forma clínica, pirâmides etárias
- **Clínico & Diagnóstico** — HIV, baciloscopia, TMR-TB, desfecho por status HIV
- **Comorbidades & Vulnerabilidades** — diabetes, alcoolismo, privados de liberdade, situação de rua
- **Tendência Histórica** — série temporal 2001–2026, comparativo mensal vs histórico, indicadores clínicos
- **Análise Livre** — exploração interativa com PyGWalker + download CSV

---

## Destaques técnicos

- **2,3 milhões de registros** — 26 anos de dados (2001–2026), ~116k notificações/ano
- **Mapa de municípios** — drill-down com tooltip enriquecido (cura, abandono, óbitos, HIV)
- **Distrito Federal** — 35 Regiões Administrativas via OpenStreetMap (Overpass API), custo zero
- **Análise sob demanda** — PyGWalker carrega só quando solicitado, preservando performance
- **Dados 2026** — aviso automático de dados parciais (lag de notificação do SINAN)

---

## Stack

| Tecnologia | Uso |
|---|---|
| Python 3.11 + Streamlit | Interface e servidor |
| DuckDB | Queries colunares sobre Parquet |
| Folium + Leaflet | Mapas interativos |
| Plotly | Gráficos |
| PyGWalker | Análise drag-and-drop |
| OpenStreetMap / Overpass API | Geometrias das RAs do DF |

---

## Como rodar

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Exportar dados do banco (requer acesso ao PostgreSQL)
python scripts/conectar_banco.py 2001 2026

# 3. Preparar os dados
python scripts/preparar_dados.py 2001 2026

# 4. Gerar histórico agregado
python scripts/gerar_historico.py

# 5. Rodar o dashboard
streamlit run app.py
```

---

## Estrutura do projeto

```
dashboard-tb-sinan/
├── app.py                        ← entrada principal (Hero + KPIs + abas)
├── requirements.txt
├── src/
│   ├── styles.py                 ← CSS centralizado
│   ├── ui_sidebar.py             ← sidebar de filtros
│   ├── constantes.py             ← paletas, mapas, configurações
│   ├── dados.py                  ← carregamento e cache (DuckDB)
│   ├── graficos.py               ← funções de visualização Plotly
│   ├── mapa_interativo.py        ← mapas Folium e Plotly
│   └── session.py                ← helpers de session_state
├── scripts/
│   ├── conectar_banco.py         ← PostgreSQL → Parquet por ano
│   ├── preparar_dados.py         ← limpeza e enriquecimento
│   ├── gerar_historico.py        ← CSVs agregados para Tendência
│   └── baixar_ras_df.py          ← RAs do DF via OpenStreetMap
└── dados_dashboard/
    ├── tuberculose_*_tratado.parquet
    ├── historico_*.csv
    ├── _geo_cache/               ← GeoJSON dos estados e municípios
    └── df_regioes_administrativas.geojson
```

---

**Fonte dos dados:** SINAN NET — Ministério da Saúde  
**Cobertura:** notificações de tuberculose, Brasil, 2001–2026  
**Última atualização:** junho/2026
