st.title("📊 G8 Flow Monitor & Execution")

# --- INIZIO BLOCCO CONNESSIONE ---
client_id = st.secrets["CTRADER_CLIENT_ID"]
client_secret = st.secrets["CTRADER_CLIENT_SECRET"]
# Sostituisci questo URL con quello della tua app!
redirect_uri = "https://tua-app.streamlit.app/" 

st.sidebar.header("🔌 Connessione Broker")

auth_url = (
    f"https://openapi.ctrader.com/apps/auth?client_id={client_id}"
    f"&redirect_uri={redirect_uri}&scope=accounts,trading"
)

# Controlla se siamo tornati dal login con il codice
if "code" in st.query_params:
    st.sidebar.success("✅ Autorizzazione Ricevuta!")
    st.sidebar.info("Il bot è pronto per generare il Token.")
else:
    st.sidebar.link_button("🔗 Connetti a Pepperstone", auth_url)
# --- FINE BLOCCO CONNESSIONE ---

# Sotto questo, continua pure con la Sidebar precedente (Timeframe, ecc.)
tf_main = st.sidebar.selectbox("Timeframe:", ("1m", "5m", "15m", "1h"), index=2)
