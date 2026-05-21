# Dashboard TB · SINAN NET

Painel de vigilância epidemiológica da tuberculose no Brasil. Consome dados de notificação do SINAN NET (2001–2025), processa via DuckDB e entrega visualizações interativas em Streamlit.

**Funcionalidades:**
- Mapa interativo por estado com drill-down por município
- KPI cards: casos, cura, óbito, abandono, incidência, mortalidade
- Perfil epidemiológico: sexo, raça/cor, forma clínica, tipo de entrada
- Desfechos clínicos e HIV/comorbidades
- Populações vulneráveis: PPL, situação de rua, imigrantes
- Tendências históricas 2001–2025 com comparação de períodos
- Seleção de múltiplos anos e filtros por estado, perfil e comorbidades
- Exploração livre via PyGWalker

---

## Início rápido (desenvolvimento local)

```bash
git clone https://github.com/Mcardosor/dashboard-tb-sinan.git
cd dashboard-tb-sinan

# Dependências do dashboard
pip install -r requirements.txt

# Dependências do pipeline ETL (só se for rodar os scripts de dados)
pip install -r requirements-pipeline.txt
```

**Sem acesso ao banco PostgreSQL?** Gere dados sintéticos para testar:

```bash
python scripts/gerar_dados_sinteticos.py 2025
streamlit run app.py
```

---

## Pipeline de dados

Os dados saem do PostgreSQL (`silver.sinan_tube`) e chegam ao dashboard como Parquet otimizado. **Requer VPN e `.env` configurado.**

```bash
cp .env.example .env   # preencher com credenciais
```

`.env`:
```
DB_HOST=<host>
DB_PORT=5432
DB_NAME=<banco>
DB_USER=<usuario>
DB_PASSWORD=<senha>
```

```bash
# 1. Exportar do banco → Parquet bruto
python scripts/conectar_banco.py 2001 2025

# 2. Parquet bruto → Parquet otimizado (_tratado.parquet)
python scripts/preparar_dados.py 2001 2025

# 3. Parquets → CSVs históricos (aba Tendências)
python scripts/gerar_historico.py 2001 2025
```

Cada ano vira `dados_dashboard/sinan_tube_{ano}_tratado.parquet` (~2–3 MB, compressão Snappy). Nenhum arquivo de dados entra no git — só código.

---

## Deploy na VM com Docker

```bash
# 1. Build e execução simples
docker compose up -d --build

# 2. Acompanhar logs
docker compose logs -f

# 3. Parar
docker compose down
```

O `.dockerignore` exclui automaticamente os raw parquets (~103 MB) e scripts de ETL — a imagem contém apenas o app e os `_tratado.parquet`.

Para expor via nginx (porta 80/443), descomente o bloco `nginx` no `docker-compose.yml` e aponte para um `nginx.conf` com:

```nginx
server {
    listen 80;
    server_name seu.dominio.com;

    location / {
        proxy_pass         http://dashboard:8501;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "upgrade";
        proxy_set_header   Host $host;
        proxy_read_timeout 86400;
    }
}
```

---

## Estrutura do projeto

```
dashboard-tb-sinan/
├── app.py                          # UI e navegação (892 linhas)
├── src/
│   ├── constantes.py               # Paletas, mapeamentos, POP_ESTADO, helpers
│   ├── banco.py                    # Engine DuckDB sobre os Parquets
│   ├── dados.py                    # Carregamento, cache e enriquecimento
│   ├── graficos.py                 # Funções Plotly (uma por gráfico)
│   ├── mapa_interativo.py          # Mapa Plotly com drill-down estado→município
│   └── mapa_municipios.py          # Mapa Folium por município (Folium)
├── scripts/
│   ├── conectar_banco.py           # PostgreSQL → Parquet bruto
│   ├── preparar_dados.py           # Parquet bruto → Parquet otimizado
│   ├── gerar_historico.py          # Parquets → CSVs de série histórica
│   ├── gerar_dados_sinteticos.py   # Dados de teste (sem banco)
│   ├── baixar_geojson_municipios.py
│   ├── preparar_geo_cache.py
│   └── consultar_banco.py          # Diagnóstico da conexão
├── dados_dashboard/
│   ├── br_states.geojson           # GeoJSON estados (versionado)
│   ├── _geo_cache/                 # Cache GeoJSON municípios (versionado)
│   ├── historico_*.csv             # Série histórica pré-agregada (não versionado)
│   └── sinan_tube_*_tratado.parquet  # Dados de produção (não versionado)
├── docs/                           # Documentação interna
├── spec/                           # Spec PyGWalker (exploração livre)
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── requirements.txt                # Dependências do dashboard (produção)
└── requirements-pipeline.txt      # Dependências do ETL (desenvolvimento)
```

---

## Arquitetura técnica

| Componente | Tecnologia | Motivo |
|---|---|---|
| Query engine | DuckDB | Leitura colunar paralela, filtro pushdown, union_by_name |
| Cache | `@st.cache_data` | DataFrame cacheado por combinação de anos |
| Mapa estados | Plotly Choropleth | Render 100% no browser, drill-down clicável |
| Mapa municípios | Folium | GeoJSON por UF, cache `@st.cache_resource` |
| Gráficos | Plotly Express/GO | Tema dark consistente, paleta TB semântica |
| Exploração livre | PyGWalker | Interface drag-and-drop sobre os dados filtrados |

---

**Fonte dos dados:** SINAN NET — Ministério da Saúde  
**Cobertura:** notificações de tuberculose, Brasil, 2001–2025  
**Última atualização do pipeline:** maio/2025
