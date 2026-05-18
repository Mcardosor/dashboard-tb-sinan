# Plano de Trabalho — Semana do Seminário
**Prazo: Sexta-feira | Apresentação: Segunda-feira**

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

1. **Aba de Tendência Histórica**
   - Evolução anual de casos (linha do tempo 2001–2025)
   - Requer rodar conectar_banco.py + preparar_dados.py para anos anteriores
   - Usar agregados leves (não carrega todos os Parquets ao mesmo tempo)

2. **Mapa drill-down por município**
   - Clicar num estado → ver municípios daquele estado
   - GeoJSON de municípios carregado por estado (leve, ~300 KB/estado)

### 🟡 Média prioridade (se der tempo)

3. **Aba Clínico & Diagnóstico**
   - Coinfecção TB-HIV por estado
   - Resultados de baciloscopia e teste molecular (TMR-TB)

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
| Segunda/Terça | ✅ Feito | Novo repo, estrutura, filtros, 7 painéis |
| Quarta | 🔄 Hoje | Aba de tendência histórica |
| Quinta | ⏳ | Dados históricos (banco) + indicadores série temporal |
| Sexta | ⏳ | Relatório técnico + ensaio |
| Segunda | 🎯 | Seminário |

