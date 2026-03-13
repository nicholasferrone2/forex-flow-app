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
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    data = {"chat_id": telegram_chat_id, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=data)

def send_test_order():
    # URL specifico per ordini tramite Open API v2
    # Nota: 'live' o 'training' dipende dal tuo tipo di conto Pepperstone
    url = f"https://openapi.ctrader.com/tradingapi/v2/training/accounts/{account_id}/orders"

    headers = {
        "Authorization": f"Bearer {st.session_state.get('access_token')}",
        "Content-Type": "application/json"
    }
    
    # Struttura del payload corretta per cTrader Open API
    payload = {
        "payloadType": "PROTO_OA_NEW_ORDER_REQ",
        "ctidTraderAccountId": account_id,
        "symbolId": 1, 
        "orderType": "MARKET",
        "tradeSide": "BUY",
        "volume": int(lot_size * 100000), # 0.1 lotti = 10.000 unità
        "takeProfit": take_profit_pips
    }
    
    try:
        # Usiamo un timeout per evitare che l'app resti appesa
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        return response
    except Exception as e:
        return None

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    data = {"chat_id": telegram_chat_id, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=data)

def send_test_order():
    url = f"https://openapi.ctrader.com/tradingapi/v2/symbols/1/order" # 1 solitamente è EURUSD
    headers = {
        "Authorization": f"Bearer {st.session_state.access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "payloadType": "PROTO_OA_NEW_ORDER_REQ",
        "ctidTraderAccountId": account_id,
        "symbolId": 1, 
        "orderType": "MARKET",
        "tradeSide": "BUY",
        "volume": int(lot_size * 100000), # Converte 0.1 lotti in unità
        "takeProfit": take_profit_pips
    }
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        st.sidebar.success("🚀 Ordine inviato con successo!")
    else:
        st.sidebar.error(f"❌ Errore invio: {response.text}")

# --- 5. INTERFACCIA SIDEBAR E CONNESSIONE ---
st.sidebar.header("🔌 Connessione Broker")

auth_url = f"https://openapi.ctrader.com/apps/auth?client_id={client_id}&redirect_uri={redirect_uri}&scope=accounts,trading"

# Tasto di connessione Streamlit nativo
st.sidebar.link_button("🔗 Connetti a Pepperstone", auth_url, use_container_width=True)

# Gestione del ritorno dal Login
if "code" in st.query_params:
    if "access_token" not in st.session_state:
        code = st.query_params["code"]
        data = manage_tokens(auth_code=code)
        if data and "accessToken" in data:
            st.session_state.access_token = data["accessToken"]
            st.sidebar.success("✅ Connesso!")
            st.rerun()

# --- 6. LOGICA DI MONITORAGGIO (Esempio visivo) ---
st.title("📈 IncaForex G8 Flow Dashboard")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"Monitoraggio Segnali ({tf_main})")
    # Qui il codice caricherà i grafici
    st.info(f"Analisi attiva su {len(SYMBOLS)} coppie. Lot: {lot_size} | TP: {take_profit_pips} pips.")

with col2:
    st.subheader("Stato Bot")
    if "access_token" in st.session_state:
        st.write("🟢 Trading Automatico Pronto")
        
        # Tasto per inviare l'ordine di test
       # --- BLOCCO AGGIORNATO NELLA SEZIONE 6 ---
        if st.sidebar.button("🧪 Invia Ordine Test (0.1 lot)"):
            risultato = send_test_order()
            
            # Controlliamo se la risposta esiste prima di leggere lo status_code
            if risultato is not None:
                if risultato.status_code == 200:
                    st.sidebar.success("🚀 Ordine inviato!")
                    send_telegram_msg("✅ Bot: Eseguito ordine test 0.1 lot.")
                else:
                    # Se il broker risponde con un errore (es. 404 o 401)
                    st.sidebar.error(f"❌ Errore Broker: {risultato.status_code}")
                    # Questo mostra il motivo tecnico dell'errore (molto utile ora)
                    st.sidebar.code(risultato.text[:100])
            else:
                # Se la funzione send_test_order è andata in crash (Exception)
                st.sidebar.error("❌ Errore di connessione al server cTrader")
    else:
        st.write("🔴 Attesa Connessione Broker")

# Placeholder per i dati
st.write(f"Ultimo aggiornamento: {datetime.now().strftime('%H:%M:%S')} - Timeframe: {tf_main}")
