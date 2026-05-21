# Guia de Desenvolvimento

Documentação técnica para quem vai rodar, modificar ou fazer deploy do dashboard.

---

## Pré-requisitos

- Python 3.11+
- Acesso à rede interna (VPN) para conexão ao PostgreSQL
- Docker (para deploy)

---

## Instalação local

```bash
git clone https://github.com/Mcardosor/dashboard-tb-sinan.git
cd dashboard-tb-sinan

# Dependências do dashboard
pip install -r requirements.txt

# Dependências do pipeline ETL
pip install -r requirements-pipeline.txt
```

**Sem acesso ao banco?** Gere dados sintéticos para testar:

```bash
python scripts/gerar_dados_sinteticos.py 2025
streamlit run app.py
# http://localhost:8501
```

---

## Pipeline de dados

Os dados saem do PostgreSQL (`silver.sinan_tube`) e chegam ao dashboard como Parquet otimizado.

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

Cada ano vira `dados_dashboard/sinan_tube_{ano}_tratado.parquet` (~2–3 MB). Nenhum dado entra no git.

---

## Deploy na VM com Docker

```bash
# Subir em background
docker compose up -d --build

# Acompanhar logs
docker compose logs -f

# Parar
docker compose down
```

O `.dockerignore` exclui automaticamente os raw parquets (~103 MB) e scripts de ETL da imagem.

### Nginx como proxy reverso

Descomente o bloco `nginx` no `docker-compose.yml` e crie um `nginx.conf`:

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
├── app.py                          # UI e navegação (Streamlit)
├── src/
│   ├── constantes.py               # Paletas, mapeamentos, helpers
│   ├── banco.py                    # Engine DuckDB sobre os Parquets
│   ├── dados.py                    # Carregamento e cache
│   ├── graficos.py                 # Funções Plotly (uma por gráfico)
│   ├── mapa_interativo.py          # Mapa Plotly estado→município
│   └── mapa_municipios.py          # Mapa Folium por município
├── scripts/
│   ├── conectar_banco.py           # PostgreSQL → Parquet bruto
│   ├── preparar_dados.py           # Parquet bruto → Parquet otimizado
│   ├── gerar_historico.py          # Parquets → CSVs históricos
│   ├── gerar_dados_sinteticos.py   # Dados de teste (sem banco)
│   ├── baixar_geojson_municipios.py
│   ├── preparar_geo_cache.py
│   └── consultar_banco.py          # Diagnóstico da conexão
├── dados_dashboard/
│   ├── br_states.geojson           # GeoJSON estados (versionado)
│   ├── _geo_cache/                 # Cache GeoJSON municípios (versionado)
│   ├── historico_*.csv             # Série histórica (não versionado)
│   └── sinan_tube_*_tratado.parquet  # Dados de produção (não versionado)
├── docs/
│   └── DESENVOLVIMENTO.md          # Este arquivo
├── Dockerfile
├── docker-compose.yml
├── requirements.txt                # Deps do dashboard (produção)
└── requirements-pipeline.txt      # Deps do ETL (desenvolvimento)
```

---

## Arquitetura técnica

| Componente | Tecnologia | Motivo |
|---|---|---|
| Query engine | DuckDB | Leitura colunar paralela, filtro pushdown, union_by_name |
| Cache | `@st.cache_data` | DataFrame cacheado por combinação de anos |
| Mapa estados | Plotly Choropleth | Render no browser, drill-down clicável |
| Mapa municípios | Folium | GeoJSON por UF, cache por sessão |
| Gráficos | Plotly Express/GO | Tema dark, paleta semântica TB |
| Exploração livre | PyGWalker | Drag-and-drop sobre os dados filtrados |
