import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import numpy as np
import requests
import json
import os
from datetime import datetime, timedelta

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="G8 Pro Trader", layout="wide")

# --- 2. CONFIGURAZIONE CREDENZIALI ---
# Carichiamo i dati dai Secrets di Streamlit usando i nomi esatti che hai nelle foto
try:
    client_id = st.secrets["CTRADER_CLIENT_ID"]
    client_secret = st.secrets["CTRADER_CLIENT_SECRET"]
    telegram_token = st.secrets["TELEGRAM_TOKEN"]
    telegram_chat_id = st.secrets["TELEGRAM_CHAT_ID"]
    account_id = st.secrets["CTRADER_ACCOUNT_ID"]
    
    # Definiamo l'URL di reindirizzamento
    redirect_uri = "https://forex-flow-app.streamlit.app/"
    
except Exception as e:
    st.error(f"Errore nel caricamento dei Secrets: {e}")
    st.stop()

# --- 3. FUNZIONI TELEGRAM E GESTIONE TOKEN ---

def send_telegram_trade_signal(pair, action, lot, tp):
    """Invia il segnale con i tasti operativi a Telegram"""
    token = st.secrets["TELEGRAM_TOKEN"]
    chat_id = st.secrets["TELEGRAM_CHAT_ID"]
    
    # Costruiamo l'URL per il comando del bot (il tuo "Esegui")
    # Questo URL deve puntare alla tua app per processare l'ordine
    base_url = "https://forex-flow-app.streamlit.app/"
    exec_url = f"{base_url}?pair={pair}&action={action}&lot={lot}&tp={tp}"
    
    msg = (
        f"🚀 **SEGNALE G8 FLOW (M15)**\n\n"
        f"📈 **Coppia:** {pair}\n"
        f"↕️ **Azione:** {action}\n"
        f"💰 **Size:** {lot} lotti\n"
        f"🎯 **TP:** {tp} pips\n\n"
        f"⚠️ *Verifica sempre sul grafico prima di operare.*"
    )
    
    payload = {
        "chat_id": chat_id,
        "text": msg,
        "parse_mode": "Markdown",
        "reply_markup": json.dumps({
            "inline_keyboard": [[
                {"text": "✅ Esegui Ordine", "url": exec_url}
            ]]
        })
    }
    
    try:
        url_tg = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url_tg, data=payload, timeout=10)
    except Exception as e:
        st.error(f"Errore invio Telegram: {e}")

def manage_tokens(auth_code=None, refresh_token=None):
    """Gestisce l'autenticazione cTrader via POST"""
    url = "https://openapi.ctrader.com/apps/token"
    
    # Dati base per la richiesta
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri
    }
    
    if auth_code:
        payload["grant_type"] = "authorization_code"
        payload["code"] = auth_code
    elif refresh_token:
        payload["grant_type"] = "refresh_token"
        payload["refresh_token"] = refresh_token
    else:
        return None

    try:
        # Usiamo POST per evitare l'errore 400 Bad Request
        response = requests.post(url, data=payload, timeout=15)
        
        if response.status_code == 200:
            return response.json()
        else:
            # Mostriamo l'errore specifico di cTrader se qualcosa fallisce
            st.sidebar.error(f"Errore cTrader: {response.text}")
            return None
    except Exception as e:
        st.sidebar.error(f"Errore di rete: {e}")
        return None

# --- 4. INTERFACCIA SIDEBAR ---
st.sidebar.header("🔌 Connessione Broker")

# Usiamo le variabili caricate nella Sezione 2
auth_url = f"https://openapi.ctrader.com/apps/auth?client_id={client_id}&redirect_uri={redirect_uri}&scope=accounts,trading"

# Mostriamo il tasto di connessione
st.sidebar.markdown(f'''
    <a href="{auth_url}" target="_self">
        <button style="width:100%; border-radius:5px; background-color:#007bff; color:white; border:none; padding:10px; cursor:pointer;">
            🔗 Connetti a Pepperstone
        </button>
    </a>
    ''', unsafe_allow_html=True)

# Gestione del ritorno da cTrader (il codice segreto)
if "code" in st.query_params:
    auth_code = st.query_params["code"]
    if "access_token" not in st.session_state:
        with st.sidebar.spinner("Autenticazione in corso..."):
            token_data = manage_tokens(auth_code=auth_code)
            if token_data:
                st.session_state.access_token = token_data["accessToken"]
                st.session_state.refresh_token = token_data["refreshToken"]
                st.sidebar.success("✅ Connesso a cTrader!")
                st.rerun()
                else:
                    st.error("❌ Errore durante l'accesso. Riprova.")

elif 'refresh_token' in st.session_state and 'access_token' not in st.session_state:
    res = manage_tokens(refresh_token=st.session_state.refresh_token)
    if res and "access_token" in res:
        st.session_state.access_token = res["access_token"]
        st.session_state.refresh_token = res.get("refresh_token")

# --- AGGIUNGI QUESTO: MOSTRA IL TASTO SE NON CONNESSO ---
elif 'access_token' not in st.session_state:
    st.sidebar.link_button("🔗 Connetti a cTrader", auth_url)

st.sidebar.divider()

# --- PARAMETRI STRATEGIA M15 (FISSI) ---
st.sidebar.subheader("⚙️ Parametri Strategia M15")
lotti = st.sidebar.number_input("Volume (Lotti):", value=0.10, step=0.01, key="lots_input")
tp_pips = st.sidebar.number_input("Take Profit (Pips):", value=15, key="tp_input")

st.sidebar.info(f"Configurazione Attiva: {lotti} Lots | {tp_pips} Pips TP")

# UNICO MENU TIMEFRAME
tf_main = st.sidebar.selectbox("Seleziona Timeframe:", ("1m", "5m", "15m", "1h"), index=2, key="tf_selector")

# Tasto Test
if st.sidebar.button("🧪 Simula Segnale G8", key="test_btn"):
    send_telegram_trade_signal("EURUSD", "BUY", lotti, tp_pips)
    st.sidebar.success("Test inviato!")

# 5. TITOLO E LOGICA G8
st.title("📊 G8 Flow Monitor & Execution")

pairs = ['EURUSD=X','GBPUSD=X','USDJPY=X','AUDUSD=X','USDCAD=X','USDCHF=X','NZDUSD=X']

@st.cache_data(ttl=30)
def fetch_strength(tf, prd):
    period_map = {"1m": "1d", "5m": "5d", "15m": "5d", "1h": "60d"}
    data = yf.download(pairs, period=period_map[tf], interval=tf, group_by='ticker', progress=False)
    df_close = pd.DataFrame()
    for p in pairs:
        if p in data: df_close[p] = data[p]['Close']
    df_close = df_close.ffill().dropna()
    if df_close.empty: return pd.DataFrame()
    
    rets = np.log(df_close / df_close.shift(1)).dropna()
    s = pd.DataFrame(index=rets.index)
    s['EUR'] = rets['EURUSD=X']; s['GBP'] = rets['GBPUSD=X']; s['JPY'] = -rets['USDJPY=X']
    s['AUD'] = rets['AUDUSD=X']; s['CAD'] = -rets['USDCAD=X']; s['CHF'] = -rets['USDCHF=X']
    s['NZD'] = rets['NZDUSD=X']; s['USD'] = -s.mean(axis=1)
    
    strength_cum = s.cumsum()
    return (strength_cum - strength_cum.mean()) / strength_cum.std() * 20

# 6. GRAFICO E ANALISI CON MEMORIA PERSISTENTE (Versione Definitiva)
try:
    v_final = fetch_strength(tf_main, "5d")
    
    # --- QUI INIZIA IL PEZZO DA SOSTITUIRE ---
    LOG_FILE = "sent_signals_log.json"
    
    def load_signals():
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, "r") as f:
                    return json.load(f)
            except: return {}
        return {}

    def save_session_data(sig_id=None):
        data = load_signals() 
        if sig_id:
            data[sig_id] = datetime.now().isoformat()
        if 'refresh_token' in st.session_state:
            data['stored_refresh_token'] = st.session_state.refresh_token
        with open(LOG_FILE, "w") as f:
            json.dump(data, f)

    # Recupero automatico del token al riavvio
    if 'refresh_token' not in st.session_state:
        saved_data = load_signals()
        if 'stored_refresh_token' in saved_data:
            st.session_state.refresh_token = saved_data['stored_refresh_token']

    if not v_final.empty:
        # --- GRAFICO CON FASCE COLORATE ---
        v_plot = v_final.tail(80).reset_index()
        v_plot.columns.values[0] = 'Data' 
        df_p = v_plot.melt(id_vars='Data', var_name='Valuta', value_name='Forza')
        fig = px.line(df_p, x='Data', y='Forza', color='Valuta', template="plotly_dark")
        
        threshold = 35
        fig.add_hrect(y0=threshold, y1=75, fillcolor="red", opacity=0.2, line_width=0, annotation_text="IPERCOMPRATO")
        fig.add_hrect(y0=-75, y1=-threshold, fillcolor="green", opacity=0.2, line_width=0, annotation_text="IPERVENDUTO")
        
        fig.update_layout(yaxis=dict(range=[-75, 75]), height=600)
        st.plotly_chart(fig, use_container_width=True)

        # --- ANALISI SEGNALI ---
        last, prev = v_final.iloc[-1], v_final.iloc[-2]
        bulls = [c for c in v_final.columns if prev[c] < -threshold and last[c] > prev[c]]
        bears = [c for c in v_final.columns if prev[c] > threshold and last[c] < prev[c]]

        # --- ANALISI SEGNALI E INVIO ---
        if bulls and bears:
            sent_signals = load_signals() # Carica i dati dal file JSON
            
            for b_up in bulls:
                for b_down in bears:
                    pair_name = f"{b_up}{b_down}"
                    signal_id = f"{pair_name}_BUY"
                    
                    # Controllo se il segnale è stato inviato meno di 60 minuti fa
                    can_send = True
                    if signal_id in sent_signals:
                        try:
                            last_sent = datetime.fromisoformat(sent_signals[signal_id])
                            if datetime.now() - last_sent < timedelta(minutes=60):
                                can_send = False
                        except: pass # Se l'orario è corrotto, invia comunque
                    
                    if can_send:
                        st.success(f"🚀 SEGNALE RILEVATO: {pair_name}")
                        
                        # Invia il segnale a Telegram con 0.1 lotti e 15 pips
                        send_telegram_trade_signal(pair_name, "BUY", lotti, tp_pips)
                        
                        # Salva l'orario del segnale E il Refresh Token nel file
                        save_session_data(signal_id) 
                        
                    else:
                        st.info(f"⏳ {pair_name} già inviato. Filtro 60min attivo.")
        else:
            st.info("🔎 Monitoraggio attivo: nessuna valuta in zona estrema al momento.")

except Exception as e:
    st.error(f"Errore nel monitoraggio segnali: {e}")
