import streamlit as st

# Language options
LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
    "hi": "Hindi",
}

PROVIDERS = {
    "auto": "Auto (Fallback Chain)",
    "deepl": "DeepL",
    "gemini": "Google Gemini",
    "openai": "OpenAI"
}

# Helper function to estimate tokens
def count_tokens(text):
    """Estimate token count based on words and characters"""
    if not text:
        return 0
    # Rough estimation: ~4 chars per token
    char_estimate = len(text) / 4
    # Word-based estimate: ~0.75 tokens per word
    word_estimate = len(text.split()) * 0.75
    # Average the two methods
    return int((char_estimate + word_estimate) / 2)

# Function to clear the input text area
def clear_input():
    st.session_state.input_text = ""

# Initialize session state
def init_session_state():
    if 'history' not in st.session_state:
        st.session_state.history = []
    if 'token_usage' not in st.session_state:
        st.session_state.token_usage = {
            "total": 0,
            "today": 0,
            "last_day": None
        }