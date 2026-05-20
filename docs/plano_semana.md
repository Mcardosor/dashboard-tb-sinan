# Plano de Trabalho — Semana do Seminário
**Prazo: Sexta-feira | Apresentação: Segunda-feira 25/05**

---

## ✅ O QUE JÁ ESTÁ FEITO

- Conexão ao banco PostgreSQL (SINAN NET) e exportação dos dados por ano
- Pipeline de limpeza e preparação: Parquet bruto → Parquet tratado e otimizado
- **Migração visual completa** (18/05): CSS dark theme, hero header, 8 KPI cards, 6 abas
  - Mapa Folium interativo (CartoDB dark matter, tooltip estilizado, 3 métricas)
  - Pirâmide etária de casos + pirâmide de óbitos por TB (lado a lado)
  - Desfechos do tratamento com paleta semântica clínica
  - Casos por Raça/Cor, Forma Clínica, Tipo de Entrada (donuts)
  - Comorbidades associadas e breakdown por estado
  - Populações em vulnerabilidade com métricas absolutas
  - Aba Clínico: HIV, baciloscopia, TMR-TB, Desfecho por status HIV, coinfecção por UF
  - Aba Tendência: mensal vs histórico, evolução anual, variação por estado, indicadores
  - Análise Livre (PyGWalker)
- **Revisão Raquel implementada** (18/05): 6 melhorias aplicadas
  - Padronização "por 100 mil hab.", reordenação KPIs, subtítulos explícitos
  - Série temporal de 10 indicadores (multiselect), 2ª pirâmide, desfecho por HIV
- Sidebar com 5 seções expandíveis (localização, perfil, clínico, vulneráveis, comorbidades)
- Arquitetura modular limpa: src/constantes, dados, graficos (15+ funções)
- scripts/ separados: conectar_banco, preparar_dados, baixar_geojson
  - Suporte a múltiplos anos via CLI: `python scripts/conectar_banco.py 2001 2024`
- Repositório unificado: dashboard-tb-sinan

---

## 🚧 O QUE FALTA — PRIORIZADO POR IMPACTO

### 🔴 Alta prioridade (até quinta)

1. **Dados históricos do banco**
   - Rodar `python scripts/conectar_banco.py 2001 2024`
   - Rodar `python scripts/preparar_dados.py 2001 2024`
   - Gerar `historico_mensal.csv`, `historico_estadual.csv`, `historico_anual.csv`
   - Habilita a aba Tendência com série temporal 2001–2025

2. **Aba de Tendência Histórica completa**
   - Evolução anual de casos (linha do tempo 2001–2025)
   - Usa agregados leves (não carrega todos os Parquets ao mesmo tempo)
   - Indicadores com multiselect (10 métricas)

3. **Mapa drill-down por município**
   - Clicar num estado → ver municípios daquele estado
   - GeoJSON de municípios carregado por estado (~300 KB/estado)

### 🟡 Média prioridade (se der tempo)

4. **Relatórios para prestação de contas**
   - Relatório técnico (stack, decisões, o que foi feito)
   - Roadmap com próximos passos

### 🟢 Pode ficar para depois do seminário

5. DuckDB para queries sob demanda (performance com múltiplos usuários)
6. Autenticação de usuários
7. Atualização automática agendada dos dados
8. Deploy em servidor com nginx

---

## 📅 CRONOGRAMA ATUALIZADO

| Dia | Status | Foco |
|-----|--------|------|
| Segunda (18/05) | ✅ Feito | Migração visual + recomendações Raquel |
| Terça (19/05) | ⏳ | Dados históricos (conectar banco, preparar 2001–2024) |
| Quarta (20/05) | ⏳ | Aba Tendência histórica completa + indicadores |
| Quinta (21/05) | ⏳ | Mapa drill-down municípios |
| Sexta (22/05) | ⏳ | Relatório técnico + ensaio da apresentação |
| Segunda (25/05) | 🎯 | **Seminário** |
