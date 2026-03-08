import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# 1. Configurazione Iniziale
st.set_page_config(page_title="Forex Flow Pro", layout="wide")

if 'signal_history' not in st.session_state:
    st.session_state.signal_history = pd.DataFrame(columns=['Orario', 'Segnale', 'Timeframe'])

st.title("⚡ Forex Global Flow & Alert System")

# 2. Selezione Timeframe
tf_choice = st.sidebar.selectbox("Intervallo:", ("1 minuto", "15 minuti", "30 minuti", "1 ora"), index=1)
tf_map = {"1 minuto": "1m", "15 minuti": "15m", "30 minuti": "30m", "1 ora": "60m"}
period_map = {"1m": "1d", "15m": "5d", "30m": "5d", "60m": "60d"}

pairs = ['EURUSD=X','GBPUSD=X','USDJPY=X','AUDUSD=X','USDCAD=X','USDCHF=X','NZDUSD=X','EURJPY=X','GBPJPY=X','EURGBP=X','AUDJPY=X','CHFJPY=X']

@st.cache_data(ttl=60)
def get_data(interval, period):
    return yf.download(pairs, period=period, interval=interval)['Volume'].dropna()

try:
    v_data = get_data(tf_map[tf_choice], period_map[tf_map[tf_choice]])
    
    if not v_data.empty:
        v_s = pd.DataFrame(index=v_data.index)
        v_s['USD'] = v_data[['EURUSD=X','GBPUSD=X','USDJPY=X','AUDUSD=X','USDCAD=X','USDCHF=X','NZDUSD=X']].sum(axis=1)
        v_s['EUR'] = v_data[['EURUSD=X','EURJPY=X','EURGBP=X']].sum(axis=1)
        v_s['GBP'] = v_data[['GBPUSD=X','GBPJPY=X','EURGBP=X']].sum(axis=1)
        v_s['JPY'] = v_data[['USDJPY=X','EURJPY=X','GBPJPY=X','AUDJPY=X','CHFJPY=X']].sum(axis=1)
        v_s['AUD'] = v_data[['AUDUSD=X','AUDJPY=X']].sum(axis=1)
        v_s['CHF'] = v_data[['USDCHF=X','CHFJPY=X']].sum(axis=1)
        v_s['CAD'] = v_data['USDCAD=X']
        v_s['NZD'] = v_data['NZDUSD=X']

        # Normalizzazione (Z-Score)
        v_norm = (v_s - v_s.mean()) / v_s.std()
        
        # 3. Logica Alert
        last, prev, threshold = v_norm.iloc[-1], v_norm.iloc[-2], 1.3
        bulls = [c for c in v_norm.columns if prev[c] < -threshold and last[c] > prev[c]]
        bears = [c for c in v_norm.columns if prev[c] > threshold and last[c] < prev[c]]

        if bulls and bears:
            for b_up in bulls:
                for b_down in bears:
                    msg = f"COMPRA {b_up}/{b_down}"
                    st.error(f"🔥 **{msg}**")
                    new_entry = {'Orario': v_data.index[-1].strftime('%H:%M'), 'Segnale': msg, 'Timeframe': tf_choice}
                    if st.session_state.signal_history.empty or st.session_state.signal_history.iloc[0]['Segnale'] != msg:
                        st.session_state.signal_history = pd.concat([pd.DataFrame([new_entry]), st.session_state.signal_history], ignore_index=True)

        # 4. Grafico Ottimizzato
        df_p = v_norm.reset_index().melt(id_vars=v_norm.reset_index().columns[0], var_name='Valuta', value_name='Forza')
        fig = px.line(df_p, x=df_p.columns[0], y='Forza', color='Valuta', template="plotly_dark")
        
        for trace in fig.data:
            trace.line.width = 6 if abs(last[trace.name]) >= threshold else 1.5

        fig.add_hrect(y0=threshold, y1=3.5, fillcolor="red", opacity=0.1)
        fig.add_hrect(y0=-3.5, y1=-threshold, fillcolor="green", opacity=0.1)
        st.plotly_chart(fig, use_container_width=True)

        # 5. Storico
        st.subheader("📜 Storico")
        st.dataframe(st.session_state.signal_history, use_container_width=True)
        if st.button("Reset"):
            st.session_state.signal_history = pd.DataFrame(columns=['Orario', 'Segnale', 'Timeframe'])
            st.rerun()
    else:
        st.info("Mercati chiusi. Riapertura ore 23:00.")
except Exception as e:
    st.error(f"Errore: {e}")
