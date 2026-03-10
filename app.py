import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import timedelta
import requests

# --- CONFIGURAZIONE TELEGRAM ---
TOKEN = "IL_TUO_TOKEN_QUI"
CHAT_ID = "IL_TUO_CHAT_ID_QUI"

def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
        requests.get(url, timeout=5)
    except: pass

st.set_page_config(page_title="G8 Strength Pro", layout="wide", page_icon="📊")

if 'signal_history' not in st.session_state:
    st.session_state.signal_history = pd.DataFrame(columns=['Orario', 'Segnale', 'TF'])

st.title("📊 G8 Advanced Strength Monitor")

# --- SIDEBAR ---
st.sidebar.header("Impostazioni")
tf_main = st.sidebar.selectbox("Timeframe Grafico:", ("1m", "5m", "15m", "1h"), index=2)
# Spazio vuoto sulla destra (in numero di candele)
right_margin_candles = st.sidebar.slider("Margine Destra (Candele):", 5, 50, 20)

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
        last, threshold = v_final.iloc[-1], 40
        
        # --- PREPARAZIONE GRAFICO ---
        v_plot = v_final.tail(80).reset_index()
        v_plot.columns.values[0] = 'Data' 
        df_p = v_plot.melt(id_vars='Data', var_name='Valuta', value_name='Forza')
        
        fig = px.line(df_p, x='Data', y='Forza', color='Valuta', 
                     template="plotly_dark", line_shape='spline')
        
        # Calcolo del margine destro (Chart Shift)
        last_date = v_plot['Data'].max()
        first_date = v_plot['Data'].min()
        # Calcoliamo la durata media di una candela per estendere l'asse
        time_delta = (v_plot['Data'].iloc[1] - v_plot['Data'].iloc[0])
        future_limit = last_date + (time_delta * right_margin_candles)

        for trace in fig.data:
            trace.line.width = 5 if abs(last[trace.name]) >= threshold else 2
        
        fig.add_hrect(y0=threshold, y1=threshold+20, fillcolor="red", opacity=0.1)
        fig.add_hrect(y0=-threshold-20, y1=-threshold, fillcolor="green", opacity=0.1)
        
        # --- FIX: RANGE ASSE X PER LO SPAZIO VUOTO ---
        fig.update_layout(
            xaxis=dict(range=[first_date, future_limit], showgrid=False, tickformat="%H:%M"),
            yaxis=dict(range=[-75, 75]),
            hovermode="x unified", 
            height=550,
            margin=dict(r=50) # Margine fisico del contenitore
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- MATRICE MULTI-TF (STILE MT4) ---
        st.subheader("🏁 Multi-Timeframe Strength Matrix")
        tf_list = ["1m", "5m", "15m", "1h"]
        matrix_data = {tf: fetch_strength(tf, period_map[tf]).iloc[-1] for tf in tf_list}
        matrix_df = pd.DataFrame(matrix_data).round(1)
        
        def color_strength(val):
            if val > 15: return 'background-color: #006400; color: white'
            if val > 5: return 'background-color: #90ee90; color: black'
            if val < -15: return 'background-color: #8b0000; color: white'
            if val < -5: return 'background-color: #ffcccb; color: black'
            return ''
        st.table(matrix_df.style.applymap(color_strength))

except Exception as e:
    st.info(f"Ricezione dati... ({e})")
