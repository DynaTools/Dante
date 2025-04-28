import streamlit as st
import datetime
import json
from services.translator import smart_translate, TranslationError
from utils.local_storage import get_key
from .config import LANGUAGES, PROVIDERS, count_tokens

def render_translator_interface():
    """Render the main translator interface with input and output sections"""
    
    # Main layout with two columns
    col1, col2 = st.columns(2)
    
    with col1:
        # Source text input
        st.subheader("Source Text")
        
        # Provider selection - the first key requirement
        available_providers = ["auto"]
        if get_key("deepl_key"):
            available_providers.append("deepl")
        if get_key("gemini_key"):
            available_providers.append("gemini")
        if get_key("openai_key"):
            available_providers.append("openai")
        
        selected_provider = st.selectbox(
            "Translation Provider",
            options=available_providers,
            format_func=lambda x: PROVIDERS.get(x, x),
            key="selected_provider"
        )
        
        source_lang = st.selectbox(
            "Source Language",
            options=list(LANGUAGES.keys()),
            format_func=lambda x: LANGUAGES[x],
            key="source_lang",
            index=5 # Set default to Portuguese ('pt')
        )
        
        input_text = st.text_area(
            "Enter text to translate",
            height=300,
            key="input_text",
            placeholder="Type or paste your text here..."
        )
        
        # Character counter with token estimation
        char_count = len(input_text)
        token_count = count_tokens(input_text)
        st.caption(f"{char_count} characters | ~{token_count} estimated tokens")
        
    with col2:
        # Translation output column
        st.subheader("Translation")
        
        target_lang = st.selectbox(
            "Target Language",
            options=[lang for lang in LANGUAGES.keys() if lang != "auto"],
            format_func=lambda x: LANGUAGES[x],
            key="target_lang",
            index=4 # Set default to Italian ('it')
        )
        
        tone = st.radio(
            "Translation Tone",
            options=["default", "formal", "informal"],
            horizontal=True,
            format_func=lambda x: {"default": "Default", "formal": "Formal", "informal": "Informal"}[x]
        )
        
        # Output area
        output_container = st.container()
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            translate_button = st.button("Translate", type="primary", use_container_width=True)
        with col2:
            # Use on_click callback to clear the input
            clear_button = st.button("Clear", on_click=clear_input, use_container_width=True)
        with col3:
            if st.session_state.history:
                st.download_button(
                    "Export History",
                    data=json.dumps(st.session_state.history, indent=2),
                    file_name=f"verborum_history_{datetime.datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json",
                    use_container_width=True
                )
            else:
                st.button("Export History", disabled=True, use_container_width=True)
    
    # Handle the translation process
    process_translation(translate_button, input_text, source_lang, target_lang, tone, selected_provider, output_container)

def clear_input():
    """Clear the input text area"""
    st.session_state.input_text = ""

def process_translation(translate_button, input_text, source_lang, target_lang, tone, selected_provider, output_container):
    """Process the translation request and display the result"""
    if translate_button and input_text:
        with st.spinner("Translating..."):
            output_text = ""
            provider_name = None
            error_message = None
            
            # Get API keys based on selected provider
            deepl_key = get_key("deepl_key") if selected_provider in ["auto", "deepl"] else None
            gemini_key = get_key("gemini_key") if selected_provider in ["auto", "gemini"] else None
            openai_key = get_key("openai_key") if selected_provider in ["auto", "openai"] else None
            
            # Check for required keys
            if selected_provider != "auto" and not locals().get(f"{selected_provider}_key"):
                st.error(f"API key for {PROVIDERS[selected_provider]} is missing")
            elif not (deepl_key or gemini_key or openai_key):
                st.error("Please add at least one API key in the sidebar")
            else:
                try:
                    # Perform translation with caching disabled for immediate results
                    result = smart_translate(
                        text=input_text,
                        target_lang=target_lang,
                        source_lang=source_lang,
                        tone=tone,
                        deepl_key=deepl_key,
                        gemini_key=gemini_key,
                        openai_key=openai_key,
                        use_cache=False  # Direct API call for fresh results
                    )
                    
                    output_text = result.get("translation", "")
                    provider_name = result.get("provider")
                    error_message = result.get("error")
                    
                    if output_text:
                        # Save last translation to session state
                        st.session_state.last_translation = {
                            "input_text": input_text,
                            "output_text": output_text,
                            "source_lang": source_lang,
                            "target_lang": target_lang,
                            "provider": provider_name
                        }
                        
                        # Update token usage counters
                        input_tokens = count_tokens(input_text)
                        output_tokens = count_tokens(output_text)
                        total_tokens = input_tokens + output_tokens
                        
                        st.session_state.token_usage["total"] += total_tokens
                        st.session_state.token_usage["today"] += total_tokens
                        
                        # Add to history
                        history_entry = {
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "provider": provider_name,
                            "source_lang": source_lang,
                            "target_lang": target_lang,
                            "tone": tone,
                            "input_text": input_text,
                            "output_text": output_text,
                            "estimated_tokens": total_tokens
                        }
                        st.session_state.history.insert(0, history_entry)  # Add at beginning for newest-first
                        
                        # Limit history size
                        if len(st.session_state.history) > 100:
                            st.session_state.history = st.session_state.history[:100]
                    
                    # Display success message
                    if output_text:
                        st.success(f"Translation complete using {provider_name.upper()}")
                    
                except TranslationError as e:
                    st.error(f"Translation failed: {str(e)}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    # Display the output
    with output_container:
        if translate_button and input_text:
            if output_text:
                st.text_area("Translation", value=output_text, height=300, disabled=True)
                st.caption(f"Translated with **{provider_name.upper() if provider_name else 'UNKNOWN'}** | ~{count_tokens(output_text)} output tokens")
            elif error_message:
                st.error(error_message)
        else:
            st.text_area("Translation", value="", height=300, disabled=True, 
                        placeholder="The translation will appear here...")