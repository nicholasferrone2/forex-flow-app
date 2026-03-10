import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import numpy as np
import requests

# ==========================================
# CONFIGURAZIONE BOT TELEGRAM (INSERISCI QUI)
# ==========================================
TOKEN = "8156536376:AAHVyKaFWiCKWoSjBVZ4d0qlIfwJUc7yY5U"
CHAT_ID = "8538711227"

def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
        requests.get(url, timeout=5)
    except Exception as e:
        print(f"Errore Telegram: {e}")

# ==========================================

st.set_page_config(page_title="G8 Bot Pro", layout="wide")

if 'signal_history' not in st.session_state:
    st.session_state.signal_history = pd.DataFrame(columns=['Orario', 'Segnale', 'TF'])

st.title("⚡ G8 Flow Monitor & Telegram Bot")

# --- SIDEBAR ---
tf_main = st.sidebar.selectbox("Timeframe Grafico:", ("1m", "5m", "15m", "1h"), index=2)
right_margin = st.sidebar.slider("Chart Shift (Margine):", 5, 50, 20)
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

try:
    v_final = fetch_strength(tf_main, period_map[tf_main])
    
    if not v_final.empty:
        last, prev, threshold = v_final.iloc[-1], v_final.iloc[-2], 40
        
        # --- GRAFICO CON CHART SHIFT ---
        v_plot = v_final.tail(80).reset_index()
        v_plot.columns.values[0] = 'Data' 
        df_p = v_plot.melt(id_vars='Data', var_name='Valuta', value_name='Forza')
        
        fig = px.line(df_p, x='Data', y='Forza', color='Valuta', template="plotly_dark", line_shape='spline')
        
        # Logica Margine Destra
        last_d = v_plot['Data'].max()
        delta = (v_plot['Data'].iloc[1] - v_plot['Data'].iloc[0])
        fig.update_layout(xaxis=dict(range=[v_plot['Data'].min(), last_d + (delta * right_margin)]))

        for trace in fig.data:
            trace.line.width = 5 if abs(last[trace.name]) >= threshold else 2
        
        fig.add_hrect(y0=threshold, y1=threshold+20, fillcolor="red", opacity=0.1)
        fig.add_hrect(y0=-threshold-20, y1=-threshold, fillcolor="green", opacity=0.1)
        fig.update_layout(yaxis=dict(range=[-75, 75]), height=500, margin=dict(r=30))
        st.plotly_chart(fig, use_container_width=True)

        # --- MATRICE MULTI-TF ---
        st.subheader("🏁 Multi-Timeframe Strength Matrix")
        tf_list = ["1m", "5m", "15m", "1h"]
        matrix_data = {tf: fetch_strength(tf, period_map[tf]).iloc[-1] for tf in tf_list}
        matrix_df = pd.DataFrame(matrix_data).round(1)
        
        def color_strength(val):
            if val > 15: return 'background-color: #006400; color: white'
            if val < -15: return 'background-color: #8b0000; color: white'
            return ''
        st.table(matrix_df.style.applymap(color_strength))

        # --- ALERT & BOT ---
        bulls = [c for c in v_final.columns if prev[c] < -threshold and last[c] > prev[c]]
        bears = [c for c in v_final.columns if prev[c] > threshold and last[c] < prev[c]]

        if bulls and bears:
            for b_up in bulls:
                for b_down in bears:
                    msg = f"🚀 G8 ALERT ({tf_main})\nCOMPRA: {b_up}\nVENDI: {b_down}"
                    if st.session_state.signal_history.empty or st.session_state.signal_history.iloc[0]['Segnale'] != msg:
                        st.error(msg)
                        send_telegram_msg(msg) # <--- INVIO AUTOMATICO
                        new_entry = {'Orario': v_final.index[-1].strftime('%H:%M'), 'Segnale': msg, 'TF': tf_main}
                        st.session_state.signal_history = pd.concat([pd.DataFrame([new_entry]), st.session_state.signal_history], ignore_index=True)

except Exception as e:
    st.info(f"Monitoraggio in corso... {e}")
