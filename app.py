import streamlit as st

# CONFIGURAZIONE ALLINEATA
CLIENT_ID = "22771"
CLIENT_SECRET = "o5nz4SfbkWJ3CPXAVkyf57EkgF8wUIP8OUKOKVliamqpeCZaFb" # Mettilo con cura
# Senza lo slash finale come su Spotware
REDIRECT_URI = "https://forex-flow-app.streamlit.app" 

st.title("🎯 G8 Flow - Final Login")

# URL con virgola negli scopes (più stabile)
auth_url = (
    f"https://openapi.ctrader.com/apps/auth"
    f"?client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&scope=accounts,trading"
    f"&response_type=code"
)

if "code" not in st.query_params:
    st.link_button("🔓 CLICCA PER CONSENTIRE", auth_url, type="primary")
else:
    st.success("✅ CONNESSIONE RIUSCITA!")
    st.balloons()
    # Da qui in poi il segnale da Telegram potrà aprire i 0.1 lotti
