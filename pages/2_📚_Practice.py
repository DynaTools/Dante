import streamlit as st

st.set_page_config(
    page_title="Verborum - Practice",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Practice")
st.markdown("---")

st.markdown("""
## Coming Soon!

The Practice section will help you improve your language skills:

- **Vocabulary Exercises**: Expand your word knowledge
- **Translation Practice**: Compare your translations with professional ones
- **Reading Comprehension**: Practice with texts at various difficulty levels
- **Custom Quizzes**: Generate personalized exercises based on your interests

Check back soon for these interactive learning features!

*Verborum: Qui quaerit, inveniet; pulsanti aperietur*
""")

st.info("This feature is currently under development. Please check back later for updates.")

# Placeholder for a future interactive element
with st.expander("Sneak Peek"):
    st.write("We're working on interactive exercises that will help you improve your language skills. Stay tuned!")