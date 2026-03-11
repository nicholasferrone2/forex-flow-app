import streamlit as st

# --- CONFIGURAZIONE ---
# Usa l'ID numerico che abbiamo visto nella foto
client_id = "22771" 
# Il redirect deve essere identico a quello nel portale (con la barra finale)
redirect_uri = "https://forex-flow-app.streamlit.app/?login=true"

st.title("🔌 Connessione G8 Flow")

# Costruzione URL seguendo la documentazione ufficiale v2
# Abbiamo aggiunto response_type e rimosso spazi extra
auth_url = (
    "https://openapi.ctrader.com/apps/auth"
    f"?client_id={client_id}"
    f"&redirect_uri={redirect_uri}"
    "&scope=accounts%20trading"
    "&response_type=code"
)

st.info("Configurazione rilevata: ID 22771")

# Tasto di collegamento
st.link_button("🔗 ACCEDI A CTRADER", auth_url)

# Sezione di emergenza
with st.expander("🆘 Se vedi ancora Errore"):
    st.write("Verifica questi 3 punti nel portale Spotware Connect:")
    st.write("1. **Application Type:** Deve essere 'Web Application'.")
    st.write("2. **Status:** Deve essere 'Active' (Verde).")
    st.write("3. **Redirect URI:** Assicurati che non ci sia una doppia barra // finale.")
    st.divider()
    st.write("Prova a copiare questo link e aprirlo in una scheda 'In incognito':")
    st.code(auth_url)
