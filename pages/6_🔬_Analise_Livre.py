"""Análise Livre — PyGWalker interativo + download CSV."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from src.styles import inject_css_page
from src.session import get_df, get_context
from src.constantes import SPEC_PATH, COLUNAS_ANALISE
from src.dados import selecionar_colunas, render_pygwalker

st.set_page_config(page_title="Análise Livre | TB SINAN", page_icon="🔬", layout="wide")
inject_css_page()

df  = get_df()
ctx = get_context()
anos_sel = ctx["anos_sel"]

st.title("🔬 Análise Livre")
st.caption(
    "Monte seus próprios gráficos arrastando campos para os eixos — "
    "sem precisar de código. Ideal para investigar hipóteses específicas."
)

df_analise  = selecionar_colunas(df, COLUNAS_ANALISE)
n_registros = len(df_analise)
n_colunas   = len(df_analise.columns)

col_info, col_csv = st.columns([3, 1])
with col_info:
    st.info(
        f"📊 **{n_registros:,}** registros  ·  **{n_colunas}** variáveis  "
        f"· filtros da sidebar já aplicados",
    )
with col_csv:
    csv_bytes = df_analise.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Baixar CSV",
        data=csv_bytes,
        file_name=f"sinan_tb_{'-'.join(str(a) for a in anos_sel)}.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.divider()

if not st.session_state.get("abrir_pygwalker"):
    st.markdown(
        """
        <div style='text-align:center;padding:40px 20px'>
          <div style='font-size:3rem'>🧪</div>
          <h3 style='color:#f0f6fc;margin:12px 0 8px'>Exploração interativa de dados</h3>
          <p style='color:#8b949e;max-width:520px;margin:0 auto 24px'>
            Arraste campos para os eixos, filtre, agrupe e crie gráficos personalizados.
            A ferramenta carrega <b>{:,} registros</b> — pode levar alguns segundos
            dependendo da sua conexão.
          </p>
        </div>
        """.format(n_registros),
        unsafe_allow_html=True,
    )
    col_l, col_btn, col_r = st.columns([2, 1, 2])
    with col_btn:
        if st.button("▶ Abrir Análise", use_container_width=True, type="primary"):
            st.session_state["abrir_pygwalker"] = True
            st.session_state.pop("_dialog_uf", None)
            st.session_state["mapa_key_counter"] = st.session_state.get("mapa_key_counter", 0) + 1
            st.rerun()
else:
    spec = SPEC_PATH if Path(SPEC_PATH).exists() else None
    render_pygwalker(df_analise, spec_path=spec)
    if st.button("✕ Fechar Análise", key="fechar_pygwalker"):
        st.session_state["abrir_pygwalker"] = False
        st.rerun()
