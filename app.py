import streamlit as st

# --- DATI DA CONTROLLARE CON CURA ---
CLIENT_ID = "22771" 
CLIENT_SECRET = "o5nz4SfbkWJ3CPXAVkyf57EkgF8wUIP8OUKOKVliamqpeCZaFb"
REDIRECT_URI = "https://forex-flow-app.streamlit.app/"

st.set_page_config(page_title="G8 Flow - Login Fix")
st.title("🔑 G8 Flow: Attivazione Permessi")

# Costruzione URL di autorizzazione (Pulito)
auth_url = (
    f"https://openapi.ctrader.com/apps/auth"
    f"?client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&scope=accounts%20trading"
    f"&response_type=code"
)

# Se non abbiamo ancora il codice di autorizzazione nell'URL
if "code" not in st.query_params:
    st.warning("Stato: Non Connesso")
    st.write("Clicca il tasto sotto. Se dopo il login vedi errore, guarda l'URL in alto.")
    st.link_button("🔓 APRI AUTORIZZAZIONE CTRADER", auth_url, type="primary")
else:
    # Se il codice appare nell'URL, abbiamo vinto
    auth_code = st.query_params["code"]
    st.success("✅ ABBIAMO IL CODICE!")
    st.code(auth_code)
    st.write("Ora il bot può ricevere i segnali da Telegram e aprire 0.1 lotti.")
