import streamlit as st
import datetime
import logging
import nltk
import re
from utils.local_storage import get_key
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download NLTK data explicitly with specific language support
try:
    nltk.download(['punkt', 'words', 'averaged_perceptron_tagger'], quiet=True)
    nltk.download(['stopwords'], quiet=True)
    logger.info("Dati NLTK scaricati con successo")
except Exception as e:
    logger.error(f"Errore durante il download dei dati NLTK: {e}")

# Grammar topics
GRAMMAR_TOPICS = {
    "articles": "Articoli",
    "nouns": "Sostantivi",
    "adjectives": "Aggettivi",
    "adverbs": "Avverbi",
    "prepositions": "Preposizioni",
    "conjunctions": "Congiunzioni",
    "pronouns": "Pronomi",
    "verb_tenses": "Tempi Verbali",
    "sentence_structure": "Struttura della Frase"
}

# Helper function for tokenization that handles language specification
def safe_tokenize(text, is_word=True, language='italian'):
    if not text:
        return []
    try:
        if is_word:
            return nltk.word_tokenize(text)  # Use default tokenizer
        else:
            return nltk.sent_tokenize(text)
    except Exception as e:
        logger.warning(f"Tokenizzazione fallita: {e}. Utilizzo split semplice.")
        if is_word:
            return text.split()
        else:
            return [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]

# Function to count tokens
def count_tokens(text):
    """Stima il conteggio dei token basato su parole e caratteri"""
    if not text:
        return 0
    # Stima approssimativa: ~4 caratteri per token
    char_estimate = len(text) / 4
    # Stima basata sulle parole: ~0.75 token per parola
    word_estimate = len(text.split()) * 0.75
    # Media dei due metodi
    return int((char_estimate + word_estimate) / 2)

# Initialize Gemini if key is available
def init_gemini():
    gemini_key = get_key("gemini_key")
    has_gemini = bool(gemini_key)
    if has_gemini:
        genai.configure(api_key=gemini_key)
    return has_gemini

# Initialize session state for usage tracking
def init_session_state():
    if 'grammar_token_usage' not in st.session_state:
        st.session_state.grammar_token_usage = {
            "total": 0,
            "today": 0,
            "last_day": None
        }
    
    # Reset token count if it's a new day
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    if st.session_state.grammar_token_usage.get("last_day") != today:
        st.session_state.grammar_token_usage["today"] = 0
        st.session_state.grammar_token_usage["last_day"] = today