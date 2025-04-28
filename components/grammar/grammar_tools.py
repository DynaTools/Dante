import streamlit as st
import re
import json
import nltk
import google.generativeai as genai

from .grammar_base import (
    safe_tokenize, 
    count_tokens
)

def render_grammar_analyzer(has_gemini):
    """Render the grammar analyzer tool"""
    st.header("Analizzatore Grammaticale 🔍")
    st.caption("Analizza il testo italiano con esempi pratici")

    # Check if there's a last translation available
    last_translation = st.session_state.get('last_translation')
    
    # Determine the initial value for the text area
    # This approach uses a callback pattern instead of modifying session_state after widget is created
    if 'use_last_translation' in st.session_state and st.session_state.use_last_translation:
        # Reset the flag after using it
        st.session_state.use_last_translation = False
        initial_text = last_translation['output_text'] if last_translation else ""
    else:
        initial_text = st.session_state.get('grammar_text_input', "")
    
    # Simple text input with auto-fill from last translation
    text_to_analyze = st.text_area(
        "Inserisci il testo italiano da analizzare:",
        value=initial_text,
        height=150,
        placeholder="Inserisci qui il tuo testo o usa l'ultima traduzione...",
        key="grammar_text_input"
    )
    
    # Add button to use last translation if available
    if last_translation and last_translation.get('target_lang') == 'it':
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Usa Ultima Traduzione"):
                # Set a flag to use last translation on next rerun
                st.session_state.use_last_translation = True
                st.rerun()
        with col2:
            if last_translation['output_text']:
                st.caption(f"Ultima traduzione disponibile ({len(last_translation['output_text'])} caratteri)")

    # Single analyze button
    if st.button("Analizza", type="primary"):
        if not text_to_analyze:
            st.warning("Inserisci del testo da analizzare")
            return

        with st.spinner("Analisi in corso..."):
            try:
                # Basic text statistics
                words = safe_tokenize(text_to_analyze, is_word=True)
                sentences = safe_tokenize(text_to_analyze, is_word=False)
                word_count = len(words)
                sentence_count = len(sentences)

                # Display statistics in columns
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Parole", word_count)
                with col2:
                    st.metric("Frasi", sentence_count)

                if has_gemini:
                    # Comprehensive analysis with Gemini
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # Create clear prompt for grammar analysis with examples
                    prompt = f"""Analizza questo testo italiano:

                    "{text_to_analyze}"

                    Fornisci:
                    1. Analisi grammaticale di base (tempo verbale principale, struttura)
                    2. La stessa frase in 3 tempi verbali diversi (presente, passato prossimo, futuro)
                    3. 4 esempi di frasi simili in contesti diversi ma usando la stessa struttura
                    4. Eventuali errori grammaticali e correzioni

                    Formatta la risposta in modo chiaro con sezioni distinte:
                    - "Analisi Base"
                    - "Variazioni Temporali"
                    - "Esempi Simili"
                    - "Correzioni" (se necessario)"""

                    response = model.generate_content(prompt)
                    st.markdown(response.text)
                    
                    # Track token usage
                    total_tokens = count_tokens(prompt) + count_tokens(response.text)
                    st.session_state.grammar_token_usage["total"] += total_tokens
                    st.session_state.grammar_token_usage["today"] += total_tokens
                    st.caption(f"Utilizzati circa {total_tokens} token")

                else:
                    st.info("Aggiungi una chiave API Gemini per un'analisi grammaticale completa.")
                    
            except Exception as e:
                st.error(f"Errore durante l'analisi: {str(e)}")

def render_pronunciation_practice():
    """Render the pronunciation practice tool"""
    st.header("Pratica di Pronuncia 🎤")
    st.caption("Esercita la tua pronuncia italiana con il riconoscimento vocale")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Parla Italiano")
        st.info("Registrati mentre parli in italiano e il nostro strumento trascriverà e fornirà feedback!")
        
        # Audio recording widget
        audio_file = st.file_uploader("Carica registrazione audio", type=["wav", "mp3", "m4a", "ogg"])
        
        record_col, example_col = st.columns(2)
        
        with record_col:
            st.audio(None, format="audio/wav")
        
        with example_col:
            st.markdown("#### Frasi di Esempio")
            st.markdown("""
            - "Buongiorno, come stai?"
            - "Mi chiamo Marco e vengo dall'Italia."
            - "Vorrei prenotare un tavolo per due persone."
            """)
    
    with col2:
        st.subheader("Analisi della Pronuncia")
        
        if audio_file is not None:
            with st.spinner("Trascrizione e analisi dell'audio in corso..."):
                try:
                    # If we have Gemini, provide pronunciation feedback
                    has_gemini = 'gemini_key' in st.session_state and st.session_state['gemini_key']
                    if has_gemini:
                        try:
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            
                            prompt = f"""Sei un esperto di pronuncia italiana. Analizza questo file audio in italiano.
                            
                            Fornisci:
                            1. Correttezza grammaticale (eventuali errori identificati)
                            2. Naturalezza delle espressioni (quanto suona nativo)
                            3. Suggerimenti per il miglioramento
                            
                            Mantieni il tuo feedback costruttivo, incoraggiante e conciso, in italiano.
                            """
                            
                            response = model.generate_content(prompt)
                            
                            st.markdown("### Feedback:")
                            st.markdown(response.text)
                            
                            # Update token usage
                            tokens = count_tokens(prompt) + count_tokens(response.text)
                            st.session_state.grammar_token_usage["total"] += tokens
                            st.session_state.grammar_token_usage["today"] += tokens
                            st.caption(f"Utilizzati circa {tokens} token")
                            
                        except Exception as e:
                            st.error(f"Errore nel fornire feedback sulla pronuncia: {str(e)}")
                    
                except Exception as e:
                    st.error(f"Errore durante l'analisi dell'audio: {str(e)}")
        else:
            st.info("Carica un file audio del tuo discorso in italiano per ottenere feedback")
            st.markdown("""
            ### Consigli per registrazioni chiare:
            - Parla chiaramente a un ritmo moderato
            - Usa un buon microfono se possibile
            - Riduci il rumore di fondo
            - Esercitati con la frase prima di registrare
            """)