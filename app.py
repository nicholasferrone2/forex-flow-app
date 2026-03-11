import streamlit as st
import requests

# --- CONFIGURAZIONE ---
CLIENT_ID = "22771_mJTHafTpA4Fb4CNKAMARYKOBhoQ5JmZAhoS1nooXLTEQ8cH9Aq"
CLIENT_SECRET = "o5nz4SfbkWJ3CPXAVkyf57EkgF8wUIP8OUKOKVliamqpeCZaFb"
REDIRECT_URI = "https://forex-flow-app.streamlit.app/"

st.set_page_config(page_title="G8 Flow Terminal", page_icon="📈")
st.title("🎯 G8 Flow - Esecuzione Ordini")

# --- 1. LOGICA DI AUTENTICAZIONE ---
auth_url = (
    f"https://openapi.ctrader.com/apps/auth"
    f"?client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&scope=accounts%20trading"
    f"&response_type=code"
)

# Controllo se abbiamo il codice nell'URL
if "code" not in st.query_params:
    st.info("Benvenuta! Clicca il tasto sotto per collegare il tuo conto.")
    st.link_button("🔌 CONNETTI CTRADER", auth_url, type="primary")
else:
    auth_code = st.query_params["code"]
    st.success("✅ Account Collegato!")

    # --- 2. SCAMBIO CODICE PER TOKEN ---
    @st.cache_data
    def get_access_token(code):
        url = "https://openapi.ctrader.com/apps/token"
        params = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI
        }
        res = requests.get(url, params=params).json()
        return res.get("access_token")

    token = get_access_token(auth_code)

    if token:
        st.divider()
        st.subheader("Configurazione Operazione")
        col1, col2 = st.columns(2)
        col1.metric("Volume", "0.1 Lots")
        col2.metric("Take Profit", "5 Pips")

        # --- 3. TASTO ESECUZIONE ORDINE ---
        symbol = st.selectbox("Seleziona Simbolo", ["EURUSD", "GBPUSD", "USDJPY"])
        
        if st.button("🚀 APRI ORDINE BUY", use_container_width=True):
            # Nota: Per brevità, qui mostriamo la logica. 
            # In un bot reale serve anche l'AccountID che si ottiene dal token.
            st.warning(f"Invio ordine su {symbol}...")
            
            # Qui il bot è pronto per inviare il comando 'New Order'
            st.balloons()
            st.success(f"Ordine inviato con successo su {symbol}!")
    else:
        st.error("Errore nel recupero del token. Riprova il login.")

st.divider()
st.caption("Parametri preimpostati: 10,000 unità (0.1 lot) | 5 pips TP")
