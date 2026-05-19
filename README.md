# Dashboard TB — SINAN NET

Painel de vigilância epidemiológica da tuberculose no Brasil. Consome os dados de notificação do SINAN NET (2001–2025), processa via pipeline Python e entrega visualizações interativas em Streamlit.

Desenvolvido para apoiar análises internas de saúde pública — distribuição geográfica, perfil dos pacientes, desfechos clínicos e tendências históricas.

---

## Pré-requisitos

- Python 3.11+
- Acesso à rede interna (VPN) para conexão ao PostgreSQL
- Credenciais em `.env` (ver abaixo)

---

## Configuração

```bash
git clone <repo>
cd dashboard-tb-sinan
pip install -r requirements.txt
cp .env.example .env   # preencher com as credenciais do banco
```

`.env`:
```
DB_HOST=10.20.10.107
DB_PORT=5432
DB_NAME=cenarios_ai
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
```

---

## Pipeline de dados

Os dados saem do PostgreSQL (`silver.sinan_tube`) e chegam ao dashboard como Parquet otimizado.

```bash
# 1. Exportar do banco (requer VPN)
python scripts/conectar_banco.py 2001 2025

# 2. Processar tipos e otimizar memória
python scripts/preparar_dados.py 2001 2025

# 3. Gerar agregados históricos para a aba de Tendência
python scripts/gerar_historico.py 2001 2025
```

Cada ano vira um arquivo `dados_dashboard/sinan_tube_{ano}_tratado.parquet` (~10–25 MB, compressão Snappy). O passo 3 gera quatro CSVs de série histórica que a aba de Tendência consome.

**Sem acesso ao banco?** Use os dados sintéticos para testar o dashboard localmente:

```bash
python scripts/gerar_dados_sinteticos.py 2025
```

---

## Rodando o dashboard

```bash
streamlit run app.py
# http://localhost:8501
```

O dashboard detecta automaticamente quais anos têm Parquet disponível e monta o seletor na sidebar.

---

## Estrutura do projeto

```
├── app.py                        # UI e navegação (Streamlit)
├── src/
│   ├── constantes.py             # Paletas, mapeamentos, POP_ESTADO
│   ├── dados.py                  # Carregamento e cache
│   ├── graficos.py               # Funções Plotly (uma por gráfico)
│   └── mapa_municipios.py        # Mapa Folium por município
├── scripts/
│   ├── conectar_banco.py         # Exporta PostgreSQL → Parquet bruto
│   ├── preparar_dados.py         # Parquet bruto → Parquet otimizado
│   ├── gerar_historico.py        # Parquets → CSVs de série histórica
│   ├── gerar_dados_sinteticos.py # Dados de teste (sem banco)
│   ├── baixar_geojson.py         # GeoJSON estados (rodar 1x)
│   ├── baixar_geojson_municipios.py
│   └── consultar_banco.py        # Diagnóstico da conexão
└── dados_dashboard/
    ├── br_states.geojson         # Versionado
    └── *.parquet / *.csv         # Não versionados (.gitignore)
```

---

## Deploy

```bash
docker build -t dashboard-tb .
docker run -p 8501:8501 --env-file .env dashboard-tb
```

A imagem expõe a porta 8501 e inclui health check via curl.

---

**Fonte dos dados:** SINAN NET — Ministério da Saúde  
**Cobertura:** notificações de tuberculose, Brasil, 2001–2025
