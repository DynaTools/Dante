import streamlit as st
import datetime
import logging
from utils.local_storage import save_key, get_key
from components.home.config import PROVIDERS, init_session_state
from components.home.translator_ui import render_translator_interface
from components.home.history_ui import render_history

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure page with minimal settings
st.set_page_config(
    page_title="🏠 Dante AI",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
init_session_state()

# Reset token count if it's a new day
today = datetime.datetime.now().strftime("%Y-%m-%d")
if st.session_state.token_usage.get("last_day") != today:
    st.session_state.token_usage["today"] = 0
    st.session_state.token_usage["last_day"] = today

# API Keys setup in sidebar
with st.sidebar:
    # Creator info
    st.markdown("### Created by [Paulo Giavoni](https://www.linkedin.com/in/paulogiavoni/)")
    
    with st.expander("API Keys", expanded=True):
        with st.form("api_keys_form"):
            st.caption("Enter API keys for translation services")
            
            deepl_key = st.text_input("DeepL API Key", type="password", 
                                     value=get_key("deepl_key") or "")
            gemini_key = st.text_input("Google Gemini API Key", type="password", 
                                       value=get_key("gemini_key") or "")
            openai_key = st.text_input("OpenAI API Key", type="password", 
                                      value=get_key("openai_key") or "")
            
            submitted = st.form_submit_button("Save Keys")
            
            if submitted:
                if deepl_key:
                    save_key("deepl_key", deepl_key)
                if gemini_key:
                    save_key("gemini_key", gemini_key)
                if openai_key:
                    save_key("openai_key", openai_key)
                st.success("API keys saved!")

    # Display token usage
    st.sidebar.divider()
    with st.sidebar.container():
        st.subheader("Token Usage")
        st.metric("Today", st.session_state.token_usage["today"])
        st.metric("Total", st.session_state.token_usage["total"])
        if st.sidebar.button("Reset Counter"):
            st.session_state.token_usage = {
                "total": 0,
                "today": 0,
                "last_day": today
            }
            st.rerun()

# Main app header
col1, col2 = st.columns([1, 3])
with col1:
    st.title("Dante AI")
with col2:
    st.markdown("### Translation and Italian Grammar Learning Portal")
    st.markdown("*Quisquis postulat, recipit; qui quaerit, invenit; et qui postulat, aperietur*")
    st.caption("Fast and accurate translations with DeepL, Gemini, and OpenAI")

# Render the translator interface
render_translator_interface()

# Render translation history
render_history()

# Footer
st.divider()
st.caption("Dante AI Translator • " + 
          ("Using selected provider: " + PROVIDERS.get(st.session_state.get('selected_provider', 'auto')) 
           if st.session_state.get('selected_provider') != "auto" 
           else "Using fallback chain: DeepL → Gemini → OpenAI")
)