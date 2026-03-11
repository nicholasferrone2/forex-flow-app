import streamlit as st
import requests
import json
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px

# --- CONFIGURAZIONE E SECRETS ---
st.set_page_config(page_title="G8 Flow - TotalFX", layout="wide")

try:
    client_id = st.secrets["CTRADER_CLIENT_ID"].strip()
    client_secret = st.secrets["CTRADER_CLIENT_SECRET"].strip()
    account_id = st.secrets["CTRADER_ACCOUNT_ID"].strip()
    TOKEN = st.secrets["TELEGRAM_TOKEN"].strip()
    CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"].strip()
    
    # URL di Redirect (Deve essere IDENTICO a quello nel portale Spotware)
    redirect_uri = "https://forex-flow-app.streamlit.app/" 
    
    auth_url = (
        f"https://openapi.ctrader.com/apps/auth"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=accounts%20trading"
    )
except Exception as e:
    st.error(f"Configurazione incompleta: {e}")
    st.stop()

# --- FUNZIONI API ---

def get_access_token(auth_code):
    url = "https://openapi.ctrader.com/apps/token"
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri
    }
    return requests.post(url, data=data).json()

# --- INTERFACCIA ---
st.sidebar.header("🔌 Connessione Broker")

# Cattura il codice di ritorno da cTrader
if "code" in st.query_params:
    auth_code = st.query_params["code"]
    if 'access_token' not in st.session_state:
        token_data = get_access_token(auth_code)
        if "access_token" in token_data:
            st.session_state.access_token = token_data["access_token"]
            st.sidebar.success("✅ Connesso!")
        else:
            st.sidebar.error("Errore nel recupero del Token")

if 'access_token' not in st.session_state:
    st.sidebar.link_button("🔗 Connetti a cTrader", auth_url)
else:
    st.sidebar.success("✅ Account Attivo")

# ... (Qui puoi aggiungere il resto del codice G8 Flow che avevi prima) ...
st.title("📊 G8 Flow Monitor")
st.info("App pronta per il collegamento. Clicca sul tasto nella sidebar.")

# 6. ANALISI G8 E GRAFICO
st.title("📊 G8 Flow Monitor")

pairs = ['EURUSD=X','GBPUSD=X','USDJPY=X','AUDUSD=X','USDCAD=X','USDCHF=X','NZDUSD=X']

@st.cache_data(ttl=30)
def fetch_strength(tf):
    period_map = {"1m": "1d", "5m": "5d", "15m": "5d", "1h": "60d"}
    try:
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
    except:
        return pd.DataFrame()

try:
    v_final = fetch_strength("15m")
    if not v_final.empty:
        v_plot = v_final.tail(80).reset_index()
        v_plot.columns.values[0] = 'Data' 
        df_p = v_plot.melt(id_vars='Data', var_name='Valuta', value_name='Forza')
        fig = px.line(df_p, x='Data', y='Forza', color='Valuta', template="plotly_dark")
        fig.update_layout(yaxis=dict(range=[-75, 75]), height=600)
        
        # Fasce di Threshold
        fig.add_hrect(y0=35, y1=75, fillcolor="green", opacity=0.1, line_width=0)
        fig.add_hrect(y0=-35, y1=-75, fillcolor="red", opacity=0.1, line_width=0)
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        st.plotly_chart(fig, use_container_width=True)

        # Logica Segnale
        last, prev = v_final.iloc[-1], v_final.iloc[-2]
        bulls = [c for c in v_final.columns if prev[c] < -35 and last[c] > prev[c]]
        bears = [c for c in v_final.columns if prev[c] > 35 and last[c] < prev[c]]

        if bulls and bears and bot_attivo:
            send_telegram_trade_signal(f"{bulls[0]}{bears[0]}", "BUY", lotti, tp_pips)

except Exception as e:
    st.error(f"Errore Analisi: {e}")
