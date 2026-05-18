# Plano de Trabalho — Semana do Seminário
**Prazo: Sexta-feira | Apresentação: Segunda-feira**

---

## ✅ O QUE JÁ ESTÁ FEITO

### Projeto 1 — Streamlit + PyGWalker (atual)
- Conexão ao banco PostgreSQL (SINAN NET) e exportação dos dados
- Pipeline de limpeza e preparação dos dados → Parquet otimizado
- Dashboard com 7 visualizações interativas:
  - Mapa coroplético por estado (Plotly)
  - Pirâmide etária (sexo × faixa etária)
  - Desfechos do tratamento (Cura, Abandono, Óbito...)
  - Casos por Raça/Cor
  - Forma Clínica (Pulmonar / Extrapulmonar)
  - Agravos associados (AIDS, alcoolismo, diabetes...)
  - Populações em vulnerabilidade (PPL, situação de rua...)
- Aba de Análise Livre (PyGWalker — exploração sem código)
- Arquitetura modular: src/constantes, dados, graficos
- GeoJSON dos estados versionado no repositório
- Deploy no Streamlit Cloud (temporário)
- Hover tooltips melhorados e valores dentro das barras
- Scroll zoom desabilitado nos gráficos

### Projeto 2 — Dashboard Tuberculose (anterior)
- Dados históricos 2001–2025 (~2,3 milhões de registros)
- Múltiplas abas: Geográfico, Perfil, Clínico, Comorbidades, Tendência
- Filtros completos na sidebar (ano, estado, sexo, raça, HIV, populações)
- Mapa Folium por município (drill-down estado → município)
- Aba de Tendência: comparação 2025 vs média histórica
- Aba Clínico: HIV, baciloscopia, TMR-TB por estado
- Dockerfile pronto para deploy em servidor
- Arquitetura documentada com fluxo de dados completo

---

## 🚧 O QUE FALTA — PRIORIZADO POR IMPACTO

### 🔴 Alta prioridade (até quinta)

1. **Unificar os dois projetos em um repositório único**
   - Trazer os dados históricos (2001–2025) para o projeto atual
   - Manter arquitetura modular do projeto 1 (src/)

2. **Sidebar com filtros** ← grande salto de maturidade
   - Filtro de ano (2025 isolado ou série completa)
   - Filtro por estado (UF)
   - Filtro por sexo e forma clínica

3. **Aba de Tendência Histórica**
   - Evolução anual de casos 2001–2025
   - Comparativo 2025 vs média histórica
   - Indicadores clínicos ao longo dos anos

4. **Mapa por município** (Folium drill-down)
   - Já implementado no projeto 2, trazer para cá

### 🟡 Média prioridade (se der tempo)

5. **Aba Clínico & Diagnóstico**
   - Coinfecção TB-HIV por estado
   - Resultados de baciloscopia e TMR-TB

6. **Rodar em localhost** (sair do Streamlit Cloud)
   - Remover dependência do Streamlit Cloud
   - Testar execução local com todos os dados históricos

7. **Dockerfile** (do projeto 2 já existe, só adaptar)
   - Base para o deploy futuro com nginx

### 🟢 Pode ficar para depois do seminário

8. DuckDB para queries sob demanda (performance)
9. Autenticação de usuários
10. Atualização automática agendada
11. Deploy em servidor com nginx

---

## 📋 RELATÓRIOS PARA PRESTAÇÃO DE CONTAS

- [ ] Relatório técnico de desenvolvimento (o que foi feito, stack, decisões)
- [ ] Documento de funcionalidades implementadas vs. planejadas
- [ ] Roadmap com próximos passos e estimativas
- [ ] Capturas de tela do dashboard para documentação

---

## 📅 SUGESTÃO DE CRONOGRAMA

| Dia | Foco |
|-----|------|
| Terça | Unificar projetos + sidebar com filtros |
| Quarta | Aba de tendência histórica + mapa por município |
| Quinta | Rodar em localhost + ajustes visuais |
| Sexta | Relatórios + documentação + ensaio da apresentação |
| Segunda | Seminário |

