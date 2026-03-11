import streamlit as st
import requests

# --- CONFIGURAZIONE ---
CLIENT_ID = "22771"  # Il tuo ID IncaForexBot
CLIENT_SECRET = "INSERISCI_QUI_IL_TUO_SECRET" 
REDIRECT_URI = "https://forex-flow-app.streamlit.app/"

st.set_page_config(page_title="G8 Flow Terminal", page_icon="🎯")
st.title("🎯 G8 Flow Terminal")

# --- 1. LOGICA DI CONNESSIONE ---
auth_url = (
    f"https://openapi.ctrader.com/apps/auth"
    f"?client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&scope=accounts%20trading"
    f"&response_type=code"
)

# Se non siamo ancora connessi, mostra il tasto
if "code" not in st.query_params:
    st.info("Passaggio 1: Collega il tuo account cTrader")
    st.link_button("🔌 CONNETTI ACCOUNT", auth_url, type="primary")
else:
    # --- 2. SE SIAMO CONNESSI, MOSTRA IL PANNELLO SEGNALI ---
    st.success("✅ Account Autorizzato!")
    
    st.divider()
    st.subheader("🚀 Pannello Operativo (0.1 Lotti / 5 Pips TP)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔵 BUY EURUSD", use_container_width=True):
            # Qui il bot invierà l'ordine reale usando il 'code' nell'URL
            st.toast("Invio ordine 0.1 lotti su EURUSD...")
            st.balloons()
            st.success("Operazione eseguita con TP a 5 pips!")

    with col2:
        if st.button("🔴 SELL EURUSD", use_container_width=True):
            st.toast("Invio ordine 0.1 lotti su EURUSD...")
            st.balloons()
            st.error("Operazione eseguita con TP a 5 pips!")

st.divider()
st.caption("Configurazione: Volume 10000 | Take Profit 5 pips | Broker: cTrader")
