import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="IncaForex G8 Flow", layout="wide")

# --- 2. CONFIGURAZIONE CREDENZIALI ---
try:
    client_id = st.secrets["CTRADER_CLIENT_ID"]
    client_secret = st.secrets["CTRADER_CLIENT_SECRET"]
    telegram_token = st.secrets["TELEGRAM_TOKEN"]
    telegram_chat_id = st.secrets["TELEGRAM_CHAT_ID"]
    account_id = st.secrets["CTRADER_ACCOUNT_ID"]
    
    # Carichiamo i token se presenti
    if "access_token" not in st.session_state:
        st.session_state.access_token = st.secrets.get("CTRADER_ACCESS_TOKEN")
    if "refresh_token" not in st.session_state:
        st.session_state.refresh_token = st.secrets.get("CTRADER_REFRESH_TOKEN")
        
    redirect_uri = "https://forex-flow-app.streamlit.app/"
except Exception as e:
    st.error(f"Errore Secrets: {e}")

# --- 3. PARAMETRI TECNICI E OPERATIVI ---
tf_main = "H1"          
tf_filter = "M15"       
check_interval = 60     
lot_size = 0.1          # Come richiesto
take_profit_pips = 5    # Come richiesto

SYMBOLS = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'NZDUSD', 'USDCAD', 'EURGBP']

# --- 4. FUNZIONI CORE ---

def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        data = {"chat_id": telegram_chat_id, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        st.error(f"Errore Telegram: {e}")

def send_test_order():
    # URL specifico per il Proxy di Pepperstone/cTrader
    # Questo indirizzo è quello che solitamente risolve l'errore 404 HTML
    url = "https://live-api.ctrader.com/v2/symbols/1/order"
    
    headers = {
        "Authorization": f"Bearer {st.session_state.get('access_token')}",
        "Content-Type": "application/json"
    }
    
    # Pulizia Account ID: rimuove virgolette e converte in numero
    acc_id_clean = str(account_id).replace('"', '').replace("'", "").strip()
    
    payload = {
        "payloadType": "PROTO_OA_NEW_ORDER_REQ",
        "ctidTraderAccountId": int(acc_id_clean),
        "symbolId": 1,           # 1 = EURUSD
        "orderType": "MARKET",
        "tradeSide": "BUY",
        "volume": 10000,         # 0.10 lotti
        "takeProfit": 50,        # 5 pips
        "timeInForce": "GOOD_TILL_CANCEL"
    }
    
    try:
        # Aumentiamo il timeout a 30 secondi
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        return response
    except Exception as e:
        return None

# --- 5. INTERFACCIA SIDEBAR E CONNESSIONE ---
st.sidebar.header("🔌 Connessione Broker")

auth_url = f"https://openapi.ctrader.com/apps/auth?client_id={client_id}&redirect_uri={redirect_uri}&scope=accounts,trading"

# Tasto di connessione
st.sidebar.link_button("🔗 Connetti a Pepperstone", auth_url, use_container_width=True)

# Gestione del ritorno dal Login
if "code" in st.query_params:
    if "access_token" not in st.session_state:
        code = st.query_params["code"]
        # Assicurati che manage_tokens sia definita nella sezione precedente (2)
        data = manage_tokens(auth_code=code)
        if data and "accessToken" in data:
            st.session_state.access_token = data["accessToken"]
            st.sidebar.success("✅ Connesso!")
            st.rerun()

# --- 6. LOGICA DI MONITORAGGIO ---
st.title("📈 IncaForex G8 Flow Dashboard")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"Monitoraggio Segnali ({tf_main})")
    st.info(f"Analisi attiva su {len(SYMBOLS)} coppie. Lot: {lot_size} | TP: {take_profit_pips} pips.")

with col2:
    st.subheader("Stato Bot")
    if "access_token" in st.session_state and st.session_state.access_token:
        st.write("🟢 Trading Automatico Pronto")
        st.divider()
        
        # Tasto per inviare l'ordine di test
        if st.sidebar.button("🧪 Invia Ordine Test (0.1 lot)"):
            risultato = send_test_order()
            if risultato is not None:
                if risultato.status_code == 200:
                    st.sidebar.success("🚀 Ordine inviato!")
                    send_telegram_msg(f"✅ Eseguito ordine test 0.1 lot su Pepperstone ({account_id})")
                else:
                    st.sidebar.error(f"❌ Errore Broker: {risultato.status_code}")
                    st.sidebar.code(risultato.text[:150])
            else:
                st.sidebar.error("❌ Connessione fallita")
    else:
        st.write("🔴 Attesa Connessione")

st.write(f"Ultimo aggiornamento: {datetime.now().strftime('%H:%M:%S')}")
