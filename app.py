import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import numpy as np
import requests
import json

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="G8 Pro Trader", layout="wide")

# 2. RECUPERO SECRETS
try:
    TOKEN = st.secrets["TELEGRAM_TOKEN"]
    CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
    client_id = st.secrets["CTRADER_CLIENT_ID"]
    client_secret = st.secrets["CTRADER_CLIENT_SECRET"]
except Exception as e:
    st.error(f"⚠️ Errore nei Secrets: {e}")
    st.stop()

# 3. FUNZIONE INVIO TELEGRAM (POTENZIATA)
def send_telegram_trade_signal(pair, action, lot, tp):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    messaggio = (
        f"🚀 **G8 FLOW ALERT**\n\n"
        f"🔹 Asset: **{pair}**\n"
        f"🔹 Direzione: **{action}**\n"
        f"🔹 Volume: **{lot} Lotti**\n"
        f"🔹 Take Profit: **{tp} Pips**\n"
        f"🔹 Stop Loss: **NON IMPOSTATO**\n\n"
        f"Vuoi inviare l'ordine a Pepperstone?"
    )
    
    # I dati dell'ordine vengono "impacchettati" nel bottone
    keyboard = {
        "inline_keyboard": [[
            {"text": f"✅ Esegui {action} {pair}", "callback_data": f"trade_{action}_{pair}_{lot}_{tp}"},
            {"text": "❌ Ignora", "callback_data": "ignore"}
        ]]
    }
    
    payload = {
        "chat_id": CHAT_ID,
        "text": messaggio,
        "reply_markup": json.dumps(keyboard),
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=payload, timeout=5)
    except:
        pass

# 4. INTERFACCIA SIDEBAR
st.sidebar.header("🔌 Connessione Broker")

# Logica tasto connessione cTrader
redirect_uri = "https://tua-app.streamlit.app/" # Ricorda di aggiornare questo!
auth_url = f"https://openapi.ctrader.com/apps/auth?client_id={client_id}&redirect_uri={redirect_uri}&scope=accounts,trading"

if "code" in st.query_params:
    st.sidebar.success("✅ Autorizzazione Ricevuta!")
else:
    st.sidebar.link_button("🔗 Connetti a Pepperstone", auth_url)

st.sidebar.divider()

# --- CAMPI INPUT PER TRADING ---
st.sidebar.subheader("⚙️ Parametri Ordine")
lotti = st.sidebar.number_input("Volume (Lotti):", min_value=0.01, max_value=5.0, value=0.10, step=0.01)
tp_pips = st.sidebar.number_input("Take Profit (Pips):", min_value=0, max_value=500, value=20)
st.sidebar.info("Nota: Lo Stop Loss è disattivato.")

# Tasto Test
if st.sidebar.button("🧪 Simula Segnale G8"):
    send_telegram_trade_signal("EURUSD", "BUY", lotti, tp_pips)
    st.sidebar.success("Test inviato!")

st.sidebar.divider()
tf_main = st.sidebar.selectbox("Timeframe:", ("1m", "5m", "15m", "1h"), index=2)

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

# 6. GRAFICO E ANALISI SEGNALI REAL-TIME (AGGIORNATO CON FASCE)
try:
    v_final = fetch_strength(tf_main, "5d")
    
    if not v_final.empty:
        # --- GRAFICO PLOTLY CON FASCE ---
        v_plot = v_final.tail(80).reset_index()
        v_plot.columns.values[0] = 'Data' 
        df_p = v_plot.melt(id_vars='Data', var_name='Valuta', value_name='Forza')
        
        fig = px.line(df_p, x='Data', y='Forza', color='Valuta', template="plotly_dark")
        
        # AGGIUNTA FASCE IPER-COMPRATO / IPER-VENDUTO
        threshold = 35
        
        # Linea Ipercomprato (ROSSA)
        fig.add_hline(y=threshold, line_dash="dash", line_color="red", 
                      annotation_text="IPERCOMPRATO", annotation_position="top left")
        
        # Linea Ipervenduto (VERDE)
        fig.add_hline(y=-threshold, line_dash="dash", line_color="green", 
                      annotation_text="IPERVENDUTO", annotation_position="bottom left")
        
        # Opzionale: Fascia centrale neutra grigia
        fig.add_hrect(y0=-threshold, y1=threshold, fillcolor="gray", opacity=0.1, line_width=0)

        fig.update_layout(
            yaxis=dict(range=[-75, 75], title="Forza G8"), 
            height=600,
            title=f"Analisi G8 Flow - Timeframe: {tf_main}"
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # --- ANALISI SEGNALI E INVIO TELEGRAM ---
        last, prev = v_final.iloc[-1], v_final.iloc[-2]
        
        # Logica: se una valuta è oltre la fascia e inverte la direzione
        bulls = [c for c in v_final.columns if prev[c] < -threshold and last[c] > prev[c]]
        bears = [c for c in v_final.columns if prev[c] > threshold and last[c] < prev[c]]

        st.write("### 📢 Monitor Segnali Attivi")
        
        if bulls or bears:
            col1, col2 = st.columns(2)
            with col1: st.write("✅ Valute in recupero (Bull):", bulls)
            with col2: st.write("❌ Valute in stallo (Bear):", bears)

            if bulls and bears:
                for b_up in bulls:
                    for b_down in bears:
                        pair_name = f"{b_up}{b_down}"
                        st.success(f"🔥 Segnale rilevato: {pair_name}")
                        
                        # INVIO A TELEGRAM con i tuoi parametri fissi 0.1 e 5 (se impostati in sidebar)
                        # Nota: lotti e tp_pips vengono letti dalla sidebar sopra
                        send_telegram_trade_signal(pair_name, "BUY", lotti, tp_pips)
        else:
            st.info("🔎 Nessun incrocio nelle fasce di iper-estensione al momento.")

except Exception as e:
    st.error(f"Errore nel rendering del grafico o segnali: {e}")
