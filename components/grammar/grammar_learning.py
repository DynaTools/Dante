import streamlit as st
import re
import json
import requests
import datetime
import logging
from bs4 import BeautifulSoup
import google.generativeai as genai
import nltk
from nltk.metrics.distance import edit_distance

from .grammar_base import (
    GRAMMAR_TOPICS,
    count_tokens
)

# Configure logging
logger = logging.getLogger(__name__)

def get_similar_words(word: str, word_list: list, max_suggestions: int = 2) -> list:
    """Get similar words based on edit distance"""
    try:
        if not word or not word_list:
            return []
        # Calculate edit distances and filter out empty/invalid words
        distances = []
        for w in word_list:
            if w and isinstance(w, str):
                try:
                    distance = edit_distance(word.lower(), w.lower())
                    distances.append((w, distance))
                except Exception as e:
                    logger.warning(f"Error calculating distance for word '{w}': {e}")
                    continue
        
        # Sort by edit distance and return top suggestions
        if distances:
            similar_words = sorted(distances, key=lambda x: x[1])
            # Skip first word if it's exactly the same
            start_idx = 1 if similar_words and similar_words[0][1] == 0 else 0
            return [w for w, d in similar_words[start_idx:start_idx + max_suggestions]]
        return []
    except Exception as e:
        logger.error(f"Error in get_similar_words: {e}")
        return []

def render_grammar_lessons(has_gemini):
    """Render the grammar lessons tool"""
    st.header("Lezioni di Grammatica 📚")
    st.caption("Impara i fondamenti della grammatica italiana")
    
    # Topic selection
    selected_topic = st.selectbox(
        "Seleziona argomento grammaticale:", 
        options=list(GRAMMAR_TOPICS.keys()), 
        format_func=lambda x: GRAMMAR_TOPICS[x]
    )
    
    # Generate lesson content
    if has_gemini:
        try:
            with st.spinner("Caricamento contenuto lezione..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"""Crea una lezione di grammatica italiana chiara e informativa su {GRAMMAR_TOPICS[selected_topic]}.
                
                Includi:
                1. Spiegazione di base del concetto
                2. Regole chiave con esempi
                3. Pattern comuni ed eccezioni
                4. Esercizi pratici (almeno 3 esempi)
                
                Formatta con titoli chiari, spiegazioni concise e molti esempi.
                La lezione deve essere interamente in italiano.
                """
                
                response = model.generate_content(prompt)
                
                st.markdown(response.text)
                
                # Add interactive quiz at the end
                st.markdown("---")
                st.subheader("Verifica la tua comprensione")
                
                # Generate a simple quiz
                quiz_prompt = f"""Basandoti sulla lezione su {GRAMMAR_TOPICS[selected_topic]}, crea 3 semplici domande quiz.
                
                Per ogni domanda:
                1. Una domanda a scelta multipla su {GRAMMAR_TOPICS[selected_topic]}
                2. Fornisci 3 opzioni (a, b, c)
                3. Indica la risposta corretta
                
                Formatta come un oggetto JSON con questa struttura:
                {{
                    "questions": [
                        {{
                            "question": "...",
                            "options": ["...", "...", "..."],
                            "correct_index": 0/1/2,
                            "explanation": "Breve spiegazione della risposta corretta in italiano"
                        }},
                        ...
                    ]
                }}
                
                Restituisci SOLO il JSON senza testo aggiuntivo."""
                
                quiz_response = model.generate_content(quiz_prompt)
                
                # Extract JSON from response
                json_match = re.search(r'{[\s\S]*}', quiz_response.text)
                if json_match:
                    quiz_data = json.loads(json_match.group(0))
                    
                    for i, q in enumerate(quiz_data.get("questions", [])):
                        with st.container():
                            st.markdown(f"### Domanda {i+1}: {q['question']}")
                            
                            # Radio buttons for options
                            key = f"quiz_{selected_topic}_{i}"
                            answer = st.radio(
                                "Seleziona la tua risposta:",
                                options=q["options"],
                                key=key,
                                horizontal=True
                            )
                            
                            # Check answer button
                            check_col, _ = st.columns([1, 3])
                            with check_col:
                                if st.button("Verifica Risposta", key=f"check_{i}"):
                                    selected_index = q["options"].index(answer)
                                    if selected_index == q["correct_index"]:
                                        st.success("Corretto! " + q["explanation"])
                                    else:
                                        st.error(f"Non proprio. La risposta corretta è: {q['options'][q['correct_index']]}. {q['explanation']}")
                
                # Update token usage
                tokens = count_tokens(prompt) + count_tokens(response.text) + count_tokens(quiz_prompt) + count_tokens(quiz_response.text)
                st.session_state.grammar_token_usage["total"] += tokens
                st.session_state.grammar_token_usage["today"] += tokens
                st.caption(f"Utilizzati circa {tokens} token")
                
        except Exception as e:
            st.error(f"Errore nel caricamento del contenuto della lezione: {str(e)}")
    else:
        # Static content for a few basic grammar topics
        if selected_topic == "articles":
            st.markdown("""
            ## Articoli Italiani (Gli Articoli)
            
            L'italiano ha articoli determinativi e indeterminativi che devono concordare con il genere e il numero del sostantivo.
            
            ### Articoli Determinativi
            
            **Maschile**:
            - **il** (davanti alla maggior parte dei sostantivi maschili singolari): *il libro*
            - **lo** (davanti a sostantivi maschili singolari che iniziano con s+consonante, z, ps, gn, y, x): *lo studente*, *lo zaino*
            - **l'** (davanti a sostantivi maschili singolari che iniziano con vocale): *l'amico*
            - **i** (plurale di il): *i libri*
            - **gli** (plurale di lo, anche davanti a sostantivi maschili plurali che iniziano con vocale o s+cons, z, etc.): *gli studenti*, *gli amici*, *gli zaini*
            
            **Femminile**:
            - **la** (davanti alla maggior parte dei sostantivi femminili singolari): *la casa*
            - **l'** (davanti a sostantivi femminili singolari che iniziano con vocale): *l'amica*
            - **le** (plurale femminile): *le case*, *le amiche*
            
            ### Esercizi Pratici
            1. Completa con l'articolo corretto:
               - ____ zaino (m.)
               - ____ finestra (f.)
               - ____ studenti (m.)
            
            Risposte: lo, la, gli
            """)
        elif selected_topic == "verb_tenses":
            st.markdown("""
            ## Tempi Verbali Italiani (I Tempi Verbali)
            
            I verbi italiani sono coniugati secondo tempo, persona e modo.
            
            ### Presente Indicativo
            
            Il presente indicativo si usa per parlare di:
            - Azioni attuali
            - Verità generali
            - Eventi futuri vicini
            
            #### Verbi regolari in -are (es., parlare)
            - Io parl**o**
            - Tu parl**i**
            - Lui/Lei parl**a**
            - Noi parl**iamo**
            - Voi parl**ate**
            - Loro parl**ano**
            
            #### Verbi regolari in -ere (es., vedere)
            - Io ved**o**
            - Tu ved**i**
            - Lui/Lei ved**e**
            - Noi ved**iamo**
            - Voi ved**ete**
            - Loro ved**ono**
            
            #### Verbi regolari in -ire (es., dormire)
            - Io dorm**o**
            - Tu dorm**i**
            - Lui/Lei dorm**e**
            - Noi dorm**iamo**
            - Voi dorm**ite**
            - Loro dorm**ono**
            
            ### Esercizi Pratici
            1. Coniuga "mangiare" per "noi"
            2. Coniuga "scrivere" per "tu"
            3. Coniuga "aprire" per "loro"
            
            Risposte: mangiamo, scrivi, aprono
            """)
        else:
            st.info("Aggiungi una chiave API Gemini per lezioni di grammatica dinamiche su tutti gli argomenti.")
            st.markdown("""
            ## Risorse Grammaticali Statiche
            
            Per lezioni di grammatica complete, aggiungi una chiave API Gemini nelle impostazioni principali.
            
            Nel frattempo, ecco alcune ottime risorse gratuite per imparare la grammatica italiana:
            
            - [Duolingo Corso di Italiano](https://www.duolingo.com/course/it/en/Learn-Italian)
            - [Imparare l'Italiano Rai Scuola](https://www.raiscuola.rai.it/italianoperstranieri)
            - [One World Italiano](https://oneworlditaliano.com/italiano/grammatica-italiana.htm)
            - [Online Italian Club](https://onlineitalianclub.com/free-italian-exercises-and-resources/)
            """)

def render_dictionary(has_gemini):
    """Render the dictionary tool"""
    st.header("Dizionario Italiano 📕")
    st.caption("Cerca parole ed espressioni italiane")
    
    search_col, filter_col = st.columns([3, 1])
    
    with search_col:
        search_term = st.text_input("Inserisci una parola o frase italiana:", placeholder="ciao")
    with filter_col:
        search_type = st.radio("Tipo di ricerca:", ["Parola", "Frase"])
    
    if st.button("Cerca nel Dizionario", type="primary") and search_term:
        with st.spinner("Ricerca nel dizionario in corso..."):
            try:
                # Use free WordReference dictionary for lookups
                if search_type == "Parola":
                    # Construct URL for word lookup
                    lookup_url = f"https://www.wordreference.com/iten/{search_term.strip()}"
                    
                    # Send the request and get the response
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    }
                    response = requests.get(lookup_url, headers=headers)
                    
                    if response.status_code == 200:
                        # Parse the HTML content with BeautifulSoup
                        soup = BeautifulSoup(response.content, "html.parser")
                        
                        # Extract the definition table
                        result_table = soup.find("table", class_="WRD")
                        
                        # Store found words for similarity suggestions
                        found_words = []
                        
                        if result_table:
                            # Display the word and its type
                            word_info = soup.find("h3", class_="headerWord")
                            if word_info:
                                st.subheader(f"Definizione per: {word_info.text.strip()}")
                            
                            # Extract definitions
                            st.markdown("### Significati")
                            
                            translations = []
                            rows = result_table.find_all("tr")
                            for row in rows:
                                if row.find("td", class_="FrWrd"):
                                    italian = row.find("td", class_="FrWrd").strong.text.strip() if row.find("td", class_="FrWrd").strong else row.find("td", class_="FrWrd").text.strip()
                                    if italian:
                                        found_words.append(italian)
                                    pos = row.find("em", class_="POS2")
                                    pos_text = pos.text.strip() if pos else ""
                                    english = row.find("td", class_="ToWrd")
                                    english_text = english.contents[0].strip() if english and english.contents else ""
                                    
                                    if italian and english_text:
                                        translations.append({
                                            "italian": italian,
                                            "pos": pos_text,
                                            "english": english_text
                                        })
                            
                            if translations:
                                for idx, trans in enumerate(translations[:10], 1):
                                    st.markdown(f"**{idx}. {trans['italian']}** _{trans['pos']}_ → {trans['english']}")
                            else:
                                st.warning(f"Nessuna traduzione diretta trovata per '{search_term}'")
                                
                                # Get similar word suggestions
                                if found_words:
                                    similar_words = get_similar_words(search_term, found_words)
                                    if similar_words:
                                        st.info("🤔 Forse cercavi una di queste parole?")
                                        for suggestion in similar_words:
                                            st.markdown(f"- **{suggestion}**")
                                
                                # Look for grammar or usage notes
                                notes = soup.find_all("span", class_="notePubl")
                                if notes:
                                    st.markdown("### Note d'uso")
                                    for note in notes[:5]:
                                        st.info(note.text.strip())
                        else:
                            st.warning(f"Nessun risultato trovato nel dizionario per '{search_term}'")
                            
                            # If we have Gemini, try to get suggestions
                            if has_gemini:
                                st.markdown("### Suggerimenti tramite AI...")
                                try:
                                    model = genai.GenerativeModel('gemini-1.5-flash')
                                    
                                    prompt = f"""Suggerisci parole italiane simili a "{search_term}".
                                    
                                    Includi:
                                    1. Parole con ortografia simile
                                    2. Possibili correzioni ortografiche
                                    
                                    Rispondi con un elenco di 2-3 suggerimenti, ciascuno con una breve spiegazione del significato.
                                    Formatta in italiano.
                                    """
                                    
                                    response = model.generate_content(prompt)
                                    st.markdown(response.text)
                                    
                                    # Update token usage
                                    tokens = count_tokens(prompt) + count_tokens(response.text)
                                    st.session_state.grammar_token_usage["total"] += tokens
                                    st.session_state.grammar_token_usage["today"] += tokens
                                    st.caption(f"Utilizzati circa {tokens} token")
                                    
                                except Exception as e:
                                    st.error(f"Errore durante la generazione dei suggerimenti: {str(e)}")
                    else:
                        st.error(f"Errore nell'accesso al dizionario: HTTP {response.status_code}")
                
                # Phrase lookup using Gemini if available, otherwise simple suggestions
                else:  # search_type == "Frase"
                    if has_gemini:
                        try:
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            
                            prompt = f"""Analizza questa frase italiana: "{search_term}"
                            
                            Fornisci:
                            1. Traduzione in inglese
                            2. Significato letterale (se diverso dalla traduzione)
                            3. Contesto d'uso (formale/informale, regionale, ecc.)
                            4. Espressioni simili
                            
                            Formatta come un'analisi chiara e concisa in italiano.
                            """
                            
                            response = model.generate_content(prompt)
                            
                            st.markdown("### Analisi Frase")
                            st.markdown(response.text)
                            
                            # Update token usage
                            tokens = count_tokens(prompt) + count_tokens(response.text)
                            st.session_state.grammar_token_usage["total"] += tokens
                            st.session_state.grammar_token_usage["today"] += tokens
                            st.caption(f"Utilizzati circa {tokens} token")
                            
                        except Exception as e:
                            st.error(f"Errore durante l'analisi della frase: {str(e)}")
                    else:
                        st.info("Aggiungi una chiave API Gemini per un'analisi completa delle frasi.")
                        st.markdown(f"### Ricerca per: '{search_term}'")
                        st.markdown("""
                        Per la ricerca di frasi senza AI, prova queste risorse:
                        - [Reverso Context](https://context.reverso.net/translation/italian-english/)
                        - [WordReference Forums](https://forum.wordreference.com/forums/italian.38/)
                        - [Tatoeba](https://tatoeba.org/it/) - cerca frasi di esempio
                        """)
                        
            except Exception as e:
                st.error(f"Errore durante la ricerca nel dizionario: {str(e)}")
    
    # Word of the day section
    with st.expander("Parola del Giorno"):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        if "word_of_day" not in st.session_state or st.session_state.get("last_word_day") != today:
            # Only generate a new word once a day
            if has_gemini:
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    prompt = """Genera una 'Parola del Giorno' italiana con:
                    1. Una parola italiana di livello intermedio (B1-B2)
                    2. La sua parte del discorso
                    3. La sua traduzione in inglese
                    4. Una frase di esempio in italiano
                    5. Breve guida alla pronuncia (semplificata)
                    
                    Formatta come JSON:
                    {
                        "word": "...",
                        "pos": "...",
                        "translation": "...",
                        "example": "...",
                        "pronunciation": "..."
                    }
                    
                    Restituisci SOLO l'oggetto JSON.
                    """
                    
                    response = model.generate_content(prompt)
                    
                    # Extract JSON from response
                    json_match = re.search(r'{[\s\S]*}', response.text)
                    if json_match:
                        word_data = json.loads(json_match.group(0))
                        st.session_state.word_of_day = word_data
                        st.session_state.last_word_day = today
                        
                        # Update token usage
                        tokens = count_tokens(prompt) + count_tokens(response.text)
                        st.session_state.grammar_token_usage["total"] += tokens
                        st.session_state.grammar_token_usage["today"] += tokens
                    else:
                        st.session_state.word_of_day = {
                            "word": "caffè",
                            "pos": "sostantivo maschile",
                            "translation": "coffee",
                            "example": "Prendo un caffè ogni mattina.",
                            "pronunciation": "kaf-FEH"
                        }
                        st.session_state.last_word_day = today
                        
                except Exception:
                    st.session_state.word_of_day = {
                        "word": "caffè",
                        "pos": "sostantivo maschile",
                        "translation": "coffee",
                        "example": "Prendo un caffè ogni mattina.",
                        "pronunciation": "kaf-FEH"
                    }
                    st.session_state.last_word_day = today
            else:
                st.session_state.word_of_day = {
                    "word": "caffè",
                    "pos": "sostantivo maschile",
                    "translation": "coffee",
                    "example": "Prendo un caffè ogni mattina.",
                    "pronunciation": "kaf-FEH"
                }
                st.session_state.last_word_day = today
        
        # Display the word of the day
        word = st.session_state.word_of_day
        st.subheader(f"🌟 {word['word']}")
        st.markdown(f"**Parte del discorso:** {word['pos']}")
        st.markdown(f"**Traduzione:** {word['translation']}")
        st.markdown(f"**Esempio:** {word['example']}")
        st.markdown(f"**Pronuncia:** {word['pronunciation']}")