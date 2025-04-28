import streamlit as st
from .config import LANGUAGES, count_tokens

def render_history():
    """Render the translation history interface"""
    with st.expander("Translation History"):
        if not st.session_state.history:
            st.info("Your translation history will appear here")
        else:
            # History controls
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"History ({len(st.session_state.history)} entries)")
            with col2:
                if st.button("Clear History"):
                    st.session_state.history = []
                    st.rerun()
            
            # Show history entries with tabs for clean organization
            for i, entry in enumerate(st.session_state.history[:10]):  # Show only recent 10 entries
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.subheader(f"{LANGUAGES.get(entry['source_lang'])} → {LANGUAGES.get(entry['target_lang'])}")
                    with col2:
                        st.caption(f"{entry['timestamp']} • {entry['provider'].upper()} • ~{entry['estimated_tokens']} tokens")
                    
                    tabs = st.tabs(["Input", "Output"])
                    with tabs[0]:
                        st.text_area("", value=entry['input_text'], height=100, disabled=True, key=f"hist_in_{i}")
                    with tabs[1]:
                        st.text_area("", value=entry['output_text'], height=100, disabled=True, key=f"hist_out_{i}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Reuse this translation", key=f"reuse_{i}"):
                            st.session_state.input_text = entry['input_text']
                            st.session_state.source_lang = entry['source_lang']
                            st.session_state.target_lang = entry['target_lang']
                            if entry['provider'] in ["auto", "deepl", "gemini", "openai"]:
                                st.session_state.selected_provider = entry['provider']
                            st.rerun()
                    
                    st.divider()
            
            if len(st.session_state.history) > 10:
                st.caption(f"Showing 10 of {len(st.session_state.history)} entries. Export full history using the button above.")