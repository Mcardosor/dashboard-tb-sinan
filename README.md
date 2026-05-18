# Dashboard de Tuberculose — SINAN

Plataforma interativa de monitoramento epidemiologico da tuberculose no Brasil,
construida com Python e Streamlit, conectada ao banco de dados SINAN NET.

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Interface | Streamlit |
| Visualizacoes | Plotly |
| Analise livre | PyGWalker |
| Dados | PostgreSQL (SINAN NET) → Parquet |
| Processamento | Pandas + PyArrow |
| Deploy | Docker + Nginx (em implantacao) |

## Estrutura

```
dashboard-tb-sinan/
├── app.py                  # Ponto de entrada (Streamlit)
├── requirements.txt        # Dependencias Python
├── Dockerfile              # Imagem para deploy
│
├── src/                    # Logica do app
│   ├── constantes.py       # Cores, mapeamentos, configs
│   ├── dados.py            # Carregamento e cache
│   └── graficos.py         # Funcoes de visualizacao
│
├── scripts/                # Executar localmente
│   ├── conectar_banco.py   # Exporta dados do PostgreSQL por ano
│   ├── preparar_dados.py   # Processa Parquet bruto → tratado
│   └── baixar_geojson.py   # Baixa GeoJSON dos estados (1x)
│
├── dados_dashboard/        # Dados (nao versionados, exceto GeoJSON)
│   └── br_states.geojson
│
├── spec/                   # Configs salvas do PyGWalker
└── docs/                   # Documentacao e materiais
```

## Como rodar localmente

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar credenciais do banco

```bash
cp .env.example .env
# Edite .env com as credenciais do PostgreSQL
```

### 3. Exportar e preparar os dados

```bash
# Exporta um ano especifico
python scripts/conectar_banco.py 2025

# Exporta um intervalo de anos
python scripts/conectar_banco.py 2020 2025

# Processa os dados brutos
python scripts/preparar_dados.py 2025
```

### 4. Iniciar o dashboard

```bash
streamlit run app.py
```

Acesse em: http://localhost:8501

## Como adicionar um novo ano

```bash
python scripts/conectar_banco.py 2024
python scripts/preparar_dados.py 2024
```

O dashboard detecta automaticamente os anos disponíveis
e atualiza o seletor na sidebar.

## Deploy com Docker

```bash
docker build -t dashboard-tb .
docker run -p 8501:8501 dashboard-tb
```

---
*Fonte dos dados: SINAN NET — Ministerio da Saude*
