import streamlit as st
import datetime

# Importando os componentes do novo sistema modular
from components.grammar.grammar_base import init_gemini, init_session_state
from components.grammar.grammar_tools import render_grammar_analyzer
from components.grammar.grammar_learning import render_grammar_lessons
# Removed Lottie import

# Page configuration
st.set_page_config(
    page_title="Dante AI - Grammatica Italiana",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ Grammatica Italiana")
st.caption("La tua risorsa per l'analisi grammaticale italiana")

# Inicialização do estado da sessão e configuração do Gemini
init_session_state()
has_gemini = init_gemini()

# Sidebar for token usage and about section
with st.sidebar:
    # Removed Lottie animations section
    # Creator info
    st.markdown("### Created by [Paulo Giavoni](https://www.linkedin.com/in/paulogiavoni/)")
    
    st.header("Risorse Grammaticali")
    
    # Token usage display
    with st.container():
        st.subheader("Utilizzo Token")
        st.metric("Oggi", st.session_state.grammar_token_usage["today"])
        st.metric("Totale", st.session_state.grammar_token_usage["total"])
        
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        if st.sidebar.button("Azzera Contatore"):
            st.session_state.grammar_token_usage = {
                "total": 0,
                "today": 0,
                "last_day": today
            }
            st.rerun()
    
    # About section
    with st.expander("Informazioni sulla Grammatica Italiana"):
        st.markdown("""
        L'italiano è una lingua romanza con una ricca struttura grammaticale. Le caratteristiche principali includono:
        
        - Sostantivi con genere (maschile/femminile)
        - Coniugazioni verbali basate su persona, tempo e modo
        - Articoli che concordano con genere e numero del sostantivo
        - Ricco sistema di pronomi e preposizioni
        
        Usa questo strumento per analizzare e comprendere la grammatica italiana!
        """)

# Create tabs for grammar tools - removida a tab do dicionário
tab1, tab2 = st.tabs([
    "Analizzatore Grammaticale", 
    "Lezioni di Grammatica"
])

# Tab 1: Grammar Analyzer
with tab1:
    render_grammar_analyzer(has_gemini)

# Tab 2: Grammar Lessons
with tab2:
    render_grammar_lessons(has_gemini)

# Page footer
st.divider()
st.caption("Dante AI Strumenti Grammaticali Italiani • Realizzato con NLTK e Gemini")

# Add token count for API usage at the bottom
if has_gemini:
    st.caption(f"Utilizzo token oggi: {st.session_state.grammar_token_usage['today']} · Utilizzo token totale: {st.session_state.grammar_token_usage['total']}")