import streamlit as st

st.set_page_config(
    page_title="Verborum - Conversation",
    page_icon="💬",
    layout="wide"
)

st.title("💬 Conversation")
st.markdown("---")

st.markdown("""
## Coming Soon!

The Conversation section will allow you to practice your language skills in a conversational setting:

- **AI Conversation Partners**: Practice dialogues with AI language partners
- **Situational Dialogues**: Prepare for real-world conversations in different contexts
- **Pronunciation Feedback**: Get feedback on your spoken language skills
- **Cultural Context**: Learn idioms and cultural expressions

Check back soon for these interactive conversation features!

*Verborum: Qui quaerit, inveniet; pulsanti aperietur*
""")

st.info("This feature is currently under development. Please check back later for updates.")

# Placeholder for future chat interface
st.markdown("### Future Chat Interface Preview")
with st.container():
    st.write("Assistant: Hello! How can I help you practice your language skills today?")
    st.write("_The interactive chat interface will be available soon._")
    
    # Disabled input elements for preview
    disabled_input = st.text_input("Your message", disabled=True)
    col1, col2 = st.columns([4, 1])
    with col2:
        st.button("Send", disabled=True)