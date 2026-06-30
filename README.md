# Dashboard TB · SINAN NET

Painel de vigilância epidemiológica da tuberculose no Brasil, a partir das notificações do SINAN NET (2001–2026).

Acesso: http://164.41.147.175:8502/cenarios/tb

## Conteúdo

- Visão geral: incidência, mortalidade, óbitos, cura, abandono e coinfecção HIV
- Distribuição geográfica: mapa coroplético por estado, com drill-down para municípios
- Perfil dos pacientes: sexo, raça/cor, faixa etária, forma clínica, pirâmides etárias
- Clínico & diagnóstico: HIV, baciloscopia, TB-MR, desfecho por status HIV
- Comorbidades & vulnerabilidades: diabetes, alcoolismo, privados de liberdade, situação de rua
- Tendência histórica: série 2001–2026, comparativo mensal vs. histórico, indicadores clínicos
- Análise livre: exploração com PyGWalker e download em CSV

## Notas técnicas

- Base com 2,3 milhões de registros (2001–2026, ~116 mil notificações/ano)
- Drill-down de estado para município, com tooltip de cura, abandono, óbitos e HIV
- Distrito Federal: 35 Regiões Administrativas via OpenStreetMap (Overpass API), sem geometria comprada
- PyGWalker carrega sob demanda para não pesar o carregamento inicial
- Dados de 2026 são parciais — o painel avisa sobre o lag de notificação do SINAN

## Stack

| Tecnologia | Uso |
|---|---|
| Python 3.11 + Streamlit | Interface e servidor |
| DuckDB | Queries sobre Parquet |
| Folium + Leaflet | Mapas interativos |
| Plotly | Gráficos |
| PyGWalker | Análise drag-and-drop |
| OpenStreetMap / Overpass API | Geometrias das RAs do DF |

## Como rodar

```bash
pip install -r requirements.txt

# exporta dados do banco (requer acesso ao PostgreSQL)
python scripts/conectar_banco.py 2001 2026

# prepara e agrega
python scripts/preparar_dados.py 2001 2026
python scripts/gerar_historico.py

streamlit run app.py
```

## Estrutura

```
dashboard-tb-sinan/
├── app.py                        # entrada principal (hero + KPIs + abas)
├── requirements.txt
├── src/
│   ├── styles.py                 # CSS
│   ├── ui_sidebar.py             # sidebar de filtros
│   ├── constantes.py             # paletas, mapas, configurações
│   ├── dados.py                  # carregamento e cache (DuckDB)
│   ├── graficos.py               # visualizações Plotly
│   ├── mapa_interativo.py        # mapas Folium e Plotly
│   └── session.py                # helpers de session_state
├── scripts/
│   ├── conectar_banco.py         # PostgreSQL → Parquet por ano
│   ├── preparar_dados.py         # limpeza e enriquecimento
│   ├── gerar_historico.py        # CSVs agregados para Tendência
│   └── baixar_ras_df.py          # RAs do DF via OpenStreetMap
└── dados_dashboard/
    ├── tuberculose_*_tratado.parquet
    ├── historico_*.csv
    ├── _geo_cache/                # GeoJSON de estados e municípios
    └── df_regioes_administrativas.geojson
```

Fonte: SINAN NET (Ministério da Saúde). Cobertura: Brasil, 2001–2026. Última atualização: junho/2026.
