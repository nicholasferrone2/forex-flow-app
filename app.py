import streamlit as st
import requests
import json
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="G8 Flow - TotalFX", layout="wide")

# 2. RECUPERO SECRETS E PULIZIA DATI
try:
    # Usiamo .strip() per eliminare spazi invisibili che causano l'errore 400
    client_id = st.secrets["CTRADER_CLIENT_ID"].strip()
    client_secret = st.secrets["CTRADER_CLIENT_SECRET"].strip()
    account_id = st.secrets["CTRADER_ACCOUNT_ID"].strip()
    telegram_token = st.secrets["TELEGRAM_TOKEN"].strip()
    telegram_chat_id = st.secrets["TELEGRAM_CHAT_ID"].strip()
    
    # Questo deve essere IDENTICO a quello nel portale Spotware Connect
    redirect_uri = "https://forex-flow-app.streamlit.app/" 
    
    # Costruzione URL con separatore %20 per gli scopes (standard ufficiale)
    auth_url = (
        f"https://openapi.ctrader.com/apps/auth"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=accounts%20trading"
    )
except Exception as e:
    st.error(f"⚠️ Errore nei Secrets: {e}")
    st.stop()

# 3. FUNZIONI TECNICHE
def get_access_token(auth_code):
    url = "https://openapi.ctrader.com/apps/token"
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri
    }
    response = requests.post(url, data=data)
    return response.json()

def send_telegram_signal(pair, action, lot, tp):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    text = f"🚀 **G8 FLOW ALERT**\n\nAsset: {pair}\nAction: {action}\nVolume: {lot}\nTP: {tp} pips"
    keyboard = {"inline_keyboard": [[
        {"text": "✅ Esegui", "callback_data": f"exec_{pair}_{action}"},
        {"text": "❌ Ignora", "callback_data": "ignore"}
    ]]}
    payload = {"chat_id": telegram_chat_id, "text": text, "reply_markup": json.dumps(keyboard), "parse_mode": "Markdown"}
    requests.post(url, data=payload)

# 4. SIDEBAR E AUTENTICAZIONE
st.sidebar.header("🔌 Broker Connection")

# Gestione del ritorno dal Login
query_params = st.query_params
if "code" in query_params:
    auth_code = query_params["code"]
    if 'access_token' not in st.session_state:
        with st.sidebar:
            with st.spinner("Scambio codice con Token..."):
                res = get_access_token(auth_code)
                if "access_token" in res:
                    st.session_state.access_token = res["access_token"]
                    st.success("✅ Connesso!")
                else:
                    st.error(f"Errore Token: {res.get('error_description', 'Rifiutato')}")

# Tasto di Connessione
if 'access_token' not in st.session_state:
    st.sidebar.link_button("🔗 Connetti a TotalFX", auth_url, help="Clicca per autorizzare l'app su cTrader")
    
    # SEZIONE DEBUG (Solo se non connesso)
    with st.sidebar.expander("🔍 Debug Configurazione"):
        st.write("**Verifica questi dati col Portale Spotware:**")
        st.code(f"Client ID: {client_id}")
        st.code(f"Redirect URI: {redirect_uri}")
        st.write("**URL Completo inviato:**")
        st.code(auth_url)
else:
    st.sidebar.success(f"✅ Account {account_id} Attivo")
    if st.sidebar.button("Esci / Log out"):
        del st.session_state.access_token
        st.rerun()

st.sidebar.divider()

# 5. PARAMETRI TRADING (Personalizzati: 0.1 lot, 5 TP)
st.sidebar.subheader("⚙️ Parametri")
lotti = st.sidebar.number_input("Lotti", value=0.1, step=0.01)
tp_pips = st.sidebar.number_input("Take Profit (pips)", value=5)
bot_attivo = st.sidebar.toggle("Bot Attivo", value=False)

if st.sidebar.button("🧪 Test Telegram"):
    send_telegram_signal("EURUSD", "BUY", lotti, tp_pips)

# 6. LOGICA ANALISI G8
st.title("📊 G8 Flow Monitor")

pairs = ['EURUSD=X','GBPUSD=X','USDJPY=X','AUDUSD=X','USDCAD=X','USDCHF=X','NZDUSD=X']

@st.cache_data(ttl=60)
def get_g8_data():
    data = yf.download(pairs, period="5d", interval="15m", group_by='ticker', progress=False)
    df_close = pd.DataFrame()
    for p in pairs:
        if p in data: df_close[p] = data[p]['Close']
    df_close = df_close.ffill().dropna()
    rets = np.log(df_close / df_close.shift(1)).dropna()
    s = pd.DataFrame(index=rets.index)
    s['EUR'] = rets['EURUSD=X']; s['GBP'] = rets['GBPUSD=X']; s['JPY'] = -rets['USDJPY=X']
    s['AUD'] = rets['AUDUSD=X']; s['CAD'] = -rets['USDCAD=X']; s['CHF'] = -rets['USDCHF=X']
    s['NZD'] = rets['NZDUSD=X']; s['USD'] = -s.mean(axis=1)
    strength = s.cumsum()
    return (strength - strength.mean()) / strength.std() * 20

try:
    v_final = get_g8_data()
    if not v_final.empty:
        # Grafico
        v_plot = v_final.tail(100).reset_index()
        df_p = v_plot.melt(id_vars='Date' if 'Date' in v_plot.columns else v_plot.columns[0], var_name='Valuta', value_name='Forza')
        fig = px.line(df_p, x=df_p.columns[0], y='Forza', color='Valuta', template="plotly_dark")
        fig.add_hline(y=35, line_dash="dash", line_color="green")
        fig.add_hline(y=-35, line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True)
        
        # Logica Segnale
        last = v_final.iloc[-1]
        st.write("### Forza Attuale")
        st.dataframe(last.to_frame().T)
except Exception as e:
    st.error(f"Errore nel calcolo G8: {e}")
