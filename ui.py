import streamlit as st
import requests

# Pagina configuratie
st.set_page_config(
    page_title="ProvAssist - Lokale Economie",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialiseer session state voor data
if "action_state" not in st.session_state:
    st.session_state.action_state = None

if "rag_response" not in st.session_state:
    st.session_state.rag_response = {
        "answer": "Voor een vaste standplaats op de weekelijkse markt in Schoten dient de handelaar een schriftelijke aanvraag in bij de dienst Lokale Economie...",
        "source_title": "Marktreglement Gemeente Schoten",
        "article": "Artikel 13 §3",
        "pages": "5–6"
    }

# --- BOVENKANT: NIEUWE VRAAG ---
st.markdown("### Welke informatie heeft de ondernemer nodig?")
question_ = st.text_input(
    label="Vraag invoeren",
    value="",
    label_visibility="collapsed"
)

col_btn1, col_btn2 = st.columns([8, 1])
with col_btn2:
    ask_button = st.button("Vraag aan ProvAssist", type="primary", use_container_width=True)

# Wanneer op de knop wordt geklikt, stuur een verzoek naar je FastAPI backend
if ask_button:
    if not question_.strip():
        st.warning("Voer eerst een vraag in.")
    else:
        try:
            # URL van je lokaal draaiende FastAPI backend
            backend_url = "http://127.0.0.1:5000/process"
            
            # Stuur de vraag naar Python
            payload = {"question": question_, "municipality": "Schoten"}
            response = requests.post(backend_url, json=payload, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                # Sla het echte antwoord van de backend op in Streamlit state
                st.session_state.rag_response["answer"] = data.get("answer", "Geen antwoord ontvangen.")
                st.success("Verbinding met RAG-backend geslaagd!")
            else:
                st.error(f"Fout van backend: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            st.error("Kan geen verbinding maken met de Python FastAPI backend. Zorg ervoor dat deze draait op poort 5000.")

st.markdown("---")
st.markdown("##### ANTWOORD & VERIFICATIE")

# De rest van je layout gebruikt nu st.session_state.rag_response["answer"] ...