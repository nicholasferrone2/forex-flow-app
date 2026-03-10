import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import numpy as np
import requests
import json

# --- CONFIGURAZIONE SICURA ---
# Assicurati di aver inserito questi nomi nei "Secrets" di Streamlit Cloud!
try:
    TOKEN = st.secrets["TELEGRAM_TOKEN"]
    CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except:
    st.error("⚠️ Configurazione Secrets mancante! Inserisci TELEGRAM_TOKEN e TELEGRAM_CHAT_ID nelle impostazioni di Streamlit.")
    st.stop()

# --- FUNZIONE INVIO SEGNALI CON BOTTONI ---
def send_telegram_trade_signal(pair, action):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    keyboard = {
        "inline_keyboard": [[
            {"text": f"✅ Esegui {action} {pair}", "callback_data": f"trade_{action}_{pair}"},
            {"text": "❌ Ignora", "callback_data": "ignore"}
        ]]
    }
    payload = {
        "chat_id": CHAT_ID,
        "text": f"🚀 **G8 FLOW ALERT**\n\nDirezione: **{action}**\nAsset: **{pair}**\n\nVuoi inviare l'ordine a Pepperstone?",
        "reply_markup": json.dumps(keyboard),
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=payload, timeout=5)
    except: pass

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="G8 Pro Trader", layout="wide")
st.title("📊 G8 Flow Monitor & Execution")
# --- LOGICA CTRADER OAUTH2 ---
client_id = st.secrets["CTRADER_CLIENT_ID"]
client_secret = st.secrets["CTRADER_CLIENT_SECRET"]
redirect_uri = "https://tua-app.streamlit.app/" # <--- METTI IL TUO URL REALE QUI

st.sidebar.header("🔌 Connessione Broker")

# Creazione dell'URL di autorizzazione
auth_url = (
    f"https://openapi.ctrader.com/apps/auth?client_id={client_id}"
    f"&redirect_uri={redirect_uri}&scope=accounts,trading"
)

# Se l'URL contiene un codice di ritorno dopo il login su cTrader
query_params = st.query_params
if "code" in query_params:
    auth_code = query_params["code"]
    st.sidebar.success("✅ Codice di autorizzazione ricevuto!")
    
    # Qui il bot scambia il codice con un Token (lo faremo nel prossimo step)
    if st.sidebar.button("Finalizza Connessione"):
        st.sidebar.info("Generazione Access Token in corso...")
else:
    st.sidebar.link_button("🔗 Connetti a Pepperstone", auth_url)

# ---------------------------------------------------------

# Sidebar
tf_main = st.sidebar.selectbox("Timeframe:", ("1m", "5m", "15m", "1h"), index=2)
right_margin = st.sidebar.slider("Chart Shift:", 5, 50, 20)
period_map = {"1m": "1d", "5m": "5d", "15m": "5d", "1h": "60d"}

pairs = ['EURUSD=X','GBPUSD=X','USDJPY=X','AUDUSD=X','USDCAD=X','USDCHF=X','NZDUSD=X']

@st.cache_data(ttl=30)
def fetch_strength(tf, prd):
    data = yf.download(pairs, period=prd, interval=tf, group_by='ticker', progress=False)
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

# --- LOGICA PRINCIPALE ---
try:
    v_final = fetch_strength(tf_main, period_map[tf_main])
    
    if not v_final.empty:
        # Grafico
        v_plot = v_final.tail(80).reset_index()
        v_plot.columns.values[0] = 'Data' 
        df_p = v_plot.melt(id_vars='Data', var_name='Valuta', value_name='Forza')
        
        fig = px.line(df_p, x='Data', y='Forza', color='Valuta', template="plotly_dark")
        
        # Chart Shift
        last_d = v_plot['Data'].max()
        delta = (v_plot['Data'].iloc[1] - v_plot['Data'].iloc[0])
        fig.update_layout(xaxis=dict(range=[v_plot['Data'].min(), last_d + (delta * right_margin)]))
        fig.update_layout(yaxis=dict(range=[-75, 75]), height=550)
        
        st.plotly_chart(fig, use_container_width=True)

        # Analisi Segnali
        last, prev = v_final.iloc[-1], v_final.iloc[-2]
        threshold = 40
        
        bulls = [c for c in v_final.columns if prev[c] < -threshold and last[c] > prev[c]]
        bears = [c for c in v_final.columns if prev[c] > threshold and last[c] < prev[c]]

        if bulls and bears:
            for b_up in bulls:
                for b_down in bears:
                    pair_name = f"{b_up}{b_down}"
                    st.success(f"Segnale rilevato: {pair_name}")
                    # Invio segnale con bottoni
                    send_telegram_trade_signal(pair_name, "BUY")

except Exception as e:
    st.error(f"Errore caricamento dati: {e}")
