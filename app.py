import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import numpy as np
import requests

# --- CONFIGURAZIONE TELEGRAM ---
TOKEN = "IL_TUO_TOKEN_QUI"
CHAT_ID = "IL_TUO_CHAT_ID_QUI"

def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
        requests.get(url, timeout=5)
    except: pass

st.set_page_config(page_title="G8 Multi-TF Flow", layout="wide", page_icon="📊")

if 'signal_history' not in st.session_state:
    st.session_state.signal_history = pd.DataFrame(columns=['Orario', 'Segnale', 'TF'])

st.title("📊 G8 Professional Strength Monitor")

# --- SIDEBAR ---
st.sidebar.header("Impostazioni Grafico")
tf_main = st.sidebar.selectbox("Timeframe Grafico:", ("1m", "5m", "15m", "1h"), index=2)
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
        
        # --- GRAFICO STILE MT4 (FIX ERRORE INDEX) ---
        # Resettiamo l'indice e diamogli un nome esplicito 'Data'
        v_plot = v_final.tail(80).reset_index()
        v_plot.columns.values[0] = 'Data' 
        
        df_p = v_plot.melt(id_vars='Data', var_name='Valuta', value_name='Forza')
        
        fig = px.line(df_p, x='Data', y='Forza', color='Valuta', 
                     template="plotly_dark", line_shape='spline')
        
        for trace in fig.data:
            trace.line.width = 5 if abs(last[trace.name]) >= threshold else 2
        
        fig.add_hrect(y0=threshold, y1=threshold+20, fillcolor="red", opacity=0.1)
        fig.add_hrect(y0=-threshold-20, y1=-threshold, fillcolor="green", opacity=0.1)
        fig.update_layout(yaxis=dict(range=[-75, 75]), hovermode="x unified", height=500)
        st.plotly_chart(fig, use_container_width=True)

        # --- MATRICE MULTI-TIMEFRAME ---
        st.subheader("🏁 Multi-Timeframe Strength Matrix")
        
        tf_list = ["1m", "5m", "15m", "1h"]
        matrix_data = {}
        for tf in tf_list:
            d = fetch_strength(tf, period_map[tf])
            if not d.empty:
                matrix_data[tf] = d.iloc[-1]

        if matrix_data:
            matrix_df = pd.DataFrame(matrix_data).round(1)
            
            def color_strength(val):
                if val > 15: return 'background-color: #006400; color: white' # Verde scuro
                if val > 5: return 'background-color: #90ee90; color: black'  # Verde chiaro
                if val < -15: return 'background-color: #8b0000; color: white' # Rosso scuro
                if val < -5: return 'background-color: #ffcccb; color: black'  # Rosso chiaro
                return ''

            st.table(matrix_df.style.applymap(color_strength))

        # --- ALERT LOGIC ---
        bulls = [c for c in v_final.columns if prev[c] < -threshold and last[c] > prev[c]]
        bears = [c for c in v_final.columns if prev[c] > threshold and last[c] < prev[c]]

        if bulls and bears:
            for b_up in bulls:
                for b_down in bears:
                    msg = f"🚀 SEGNALE: COMPRA {b_up} / VENDI {b_down} ({tf_main})"
                    if st.session_state.signal_history.empty or st.session_state.signal_history.iloc[0]['Segnale'] != msg:
                        st.error(msg)
                        send_telegram_msg(msg)
                        new_entry = {'Orario': v_final.index[-1].strftime('%H:%M'), 'Segnale': msg, 'TF': tf_main}
                        st.session_state.signal_history = pd.concat([pd.DataFrame([new_entry]), st.session_state.signal_history], ignore_index=True)

        with st.expander("📜 Visualizza Storico Segnali"):
            st.dataframe(st.session_state.signal_history, use_container_width=True)

except Exception as e:
    st.info(f"In attesa di dati freschi o mercati chiusi... (Nota: {e})")
