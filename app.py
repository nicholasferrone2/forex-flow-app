import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import numpy as np
import requests
import json

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="G8 Flow - TotalFX", layout="wide")

# 2. RECUPERO SECRETS E CONFIGURAZIONE API
try:
    TOKEN = st.secrets["TELEGRAM_TOKEN"]
    CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
    client_id = st.secrets["CTRADER_CLIENT_ID"]
    client_secret = st.secrets["CTRADER_CLIENT_SECRET"]
    account_id = st.secrets["CTRADER_ACCOUNT_ID"]
    
    # INDIRIZZO APP (Deve essere identico a quello su Spotware Connect)
    # Esempio: "https://nome-tua-app.streamlit.app/"
    redirect_uri = "https://forex-flow-app.streamlit.app" 
    
    auth_url = f"https://openapi.ctrader.com/apps/auth?client_id={client_id}&redirect_uri={redirect_uri}&scope=accounts,trading"
except Exception as e:
    st.error(f"⚠️ Errore nei Secrets o Configurazione: {e}")
    st.stop()

# 3. FUNZIONI TECNICHE (TOKEN ED ESECUZIONE)

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

def execute_trade(symbol, side, volume, tp_pips):
    if 'access_token' not in st.session_state:
        return {"error": "Broker non connesso"}
    
    # Adattamento simbolo per TotalFX
    clean_symbol = symbol.replace("=X", "")
    
    url = f"https://openapi.ctrader.com/apps/trade/v2/accounts/{account_id}/orders"
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    
    payload = {
        "symbolName": clean_symbol,
        "orderType": "MARKET",
        "tradeSide": side,
        "volume": int(volume * 100000), # 0.1 lotti = 10k unità
        "takeProfit": tp_pips
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def send_telegram_trade_signal(pair, action, lot, tp):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    messaggio = (
        f"🚀 **G8 FLOW ALERT**\n\n"
        f"🔹 Asset: **{pair}**\n"
        f"🔹 Direzione: **{action}**\n"
        f"🔹 Volume: **{lot} Lotti**\n"
        f"🔹 Take Profit: **{tp} Pips**\n"
        f"🔹 Stop Loss: **None**\n\n"
        f"Confermi l'invio dell'ordine?"
    )
    keyboard = {
        "inline_keyboard": [[
            {"text": f"✅ Esegui {action}", "callback_data": f"trade_{action}_{pair}_{lot}_{tp}"},
            {"text": "❌ Ignora", "callback_data": "ignore"}
        ]]
    }
    payload = {"chat_id": CHAT_ID, "text": messaggio, "reply_markup": json.dumps(keyboard), "parse_mode": "Markdown"}
    requests.post(url, data=payload)

# 4. LOGICA DI AUTENTICAZIONE NELLA SIDEBAR
st.sidebar.header("🔌 Connessione Broker")

# Gestione del ritorno dal login
if "code" in st.query_params:
    auth_code = st.query_params["code"]
    if 'access_token' not in st.session_state:
        with st.sidebar:
            with st.spinner("Connessione in corso..."):
                token_data = get_access_token(auth_code)
                if "access_token" in token_data:
                    st.session_state.access_token = token_data["access_token"]
                    st.success("✅ Broker Connesso!")
                else:
                    st.error("❌ Errore Token")

if 'access_token' not in st.session_state:
    st.sidebar.link_button("🔗 Connetti a TotalFX", auth_url)
else:
    st.sidebar.success("✅ Account TotalFX Attivo")

st.sidebar.divider()

# 5. PARAMETRI DI TRADING (Richiesti: 0.1 lot, 5 TP)
st.sidebar.subheader("🤖 Stato Bot")
bot_attivo = st.sidebar.toggle("Attiva Trading Automatico", value=False)

st.sidebar.subheader("⚙️ Parametri Ordine")
lotti = st.sidebar.number_input("Volume (Lotti):", min_value=0.01, value=0.10, step=0.01)
tp_pips = st.sidebar.number_input("Take Profit (Pips):", min_value=1, value=5, step=1)
st.sidebar.caption("Stop Loss: Disabilitato")

if st.sidebar.button("🧪 Simula Segnale G8"):
    send_telegram_trade_signal("EURUSD", "BUY", lotti, tp_pips)
    st.sidebar.info("Test inviato su Telegram")

# 6. ANALISI G8 E GRAFICO
st.title("📊 G8 Flow Monitor")

pairs = ['EURUSD=X','GBPUSD=X','USDJPY=X','AUDUSD=X','USDCAD=X','USDCHF=X','NZDUSD=X']

@st.cache_data(ttl=30)
def fetch_strength(tf):
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
