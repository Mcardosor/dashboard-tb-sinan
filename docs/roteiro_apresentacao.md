# Roteiro de Apresentacao — Dashboard TB SINAN 2025
**Publico: devs e analistas | Tempo: 4 a 5 minutos**

---

## 1. Abre ja no dashboard (sem slide, direto na tela) — 20 seg

"Esse e o dashboard que desenvolvi pra visualizacao dos dados de
Tuberculose do SINAN 2025. Vou mostrar o que foi feito tecnico,
nao vou entrar muito na parte epidemiologica."

---

## 2. Stack e dados — 45 seg

"O projeto e 100% Python. Stack:

- Streamlit pra interface e deploy
- Pandas + PyArrow pra manipulacao dos dados em Parquet
- Plotly pra visualizacoes interativas
- PyGWalker pra analise exploratoria sem codigo

A base vem do SINAN NET via exportacao SQL — 116 mil linhas,
cerca de 50 colunas depois do tratamento. O dado bruto passa por
um pipeline de limpeza que normaliza strings, trata nulos e
converte tipos antes de gerar o Parquet que o app consome."

---

## 3. Demonstracao rapida dos paineis — 1 min 30 seg

"Primeira aba tem os paineis fixos. Destaco tres decisoes tecnicas:

**Mapa coropletico:** carrega um GeoJSON dos estados brasileiros
commitado no proprio repo — nao depende de URL externa, que quebrava
no Streamlit Cloud.

**Cache com st.cache_data:** os dados sao carregados uma vez e
reutilizados entre interacoes, entao a performance e boa mesmo
com 116k linhas.

**Scroll zoom desabilitado:** config scrollZoom: false em todos
os charts Plotly — detalhe pequeno mas que faz diferenca na
experiencia de uso."

---

## 4. Analise Livre com PyGWalker — 1 min

"Essa e a parte que eu mais gosto. A segunda aba renderiza o
PyGWalker direto no Streamlit via components.html.

O usuario arrasta qualquer campo, escolhe o tipo de grafico,
filtra, agrupa — tudo no browser, sem escrever uma linha de codigo.
E uma alternativa bem mais leve do que embedar um Metabase ou
Superset pra um caso de uso assim.

O app tambem suporta carregar um spec JSON pre-definido — voce
exporta uma configuracao do PyGWalker e commita no repo,
ai ela carrega automaticamente como estado inicial."

---

## 5. Deploy e proximos passos — 30 seg

"Deploy no Streamlit Cloud, direto do GitHub, zero infra pra
gerenciar. Qualquer push na main ja atualiza o app.

Proximos passos possiveis: filtro por estado na sidebar,
serie historica se tiver dados de anos anteriores, e
talvez mover o pipeline de preparacao pro dbt."

---

## 6. Fecha — 10 seg

"Codigo aberto, qualquer duvida tecnica fico a disposicao."

---

*Dica: mantenha o terminal fechado e o browser em tela cheia.
Abre direto na aba Paineis e navega pra Analise Livre ao vivo.*
