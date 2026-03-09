import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import timedelta

st.set_page_config(page_title="G8 Real-Time Monitor", layout="wide")

if 'signal_history' not in st.session_state:
    st.session_state.signal_history = pd.DataFrame(columns=['Orario', 'Segnale', 'TF'])

st.title("🔍 G8 Real-Time Monitor (Focus Ultima Sessione)")

# --- SIDEBAR ---
st.sidebar.header("⏱️ Controllo Tempo")
tf_choice = st.sidebar.selectbox("Frequenza Dati:", ("1 minuto", "15 minuti", "1 ora"), index=0)
tf_map = {"1 minuto": "1m", "15 minuti": "15m", "1 ora": "60m"}
# Scarichiamo un po' più di dati per la media, ma ne mostriamo pochi nel grafico
period_map = {"1m": "1d", "15m": "5d", "60m": "60d"}

pairs = ['EURUSD=X','GBPUSD=X','USDJPY=X','AUDUSD=X','USDCAD=X','USDCHF=X','NZDUSD=X']

@st.cache_data(ttl=30) # Aggiornamento ogni 30 secondi
def get_clean_data(tf, prd):
    data = yf.download(pairs, period=prd, interval=tf, group_by='ticker', progress=False)
    df_close = pd.DataFrame()
    for p in pairs:
        if p in data:
            df_close[p] = data[p]['Close']
    return df_close.ffill().dropna()

try:
    df_raw = get_clean_data(tf_map[tf_choice], period_map[tf_map[tf_choice]])
    
    if not df_raw.empty:
        # 1. Calcolo Forza Relativa
        rets = df_raw.pct_change().dropna()
        strength = pd.DataFrame(index=rets.index)
        strength['EUR'] = rets['EURUSD=X']
        strength['GBP'] = rets['GBPUSD=X']
        strength['JPY'] = -rets['USDJPY=X']
        strength['AUD'] = rets['AUDUSD=X']
        strength['CAD'] = -rets['USDCAD=X']
        strength['CHF'] = -rets['USDCHF=X']
        strength['NZD'] = rets['NZDUSD=X']
        strength['USD'] = -(strength.mean(axis=1))

        # 2. Normalizzazione Z-Score
        v_norm = (strength - strength.mean()) / strength.std()
        
        # --- ZOOM SULL'ULTIMO PERIODO ---
        # Filtriamo il dataframe per mostrare solo le ultime X ore nel grafico
        last_time = v_norm.index[-1]
        if tf_choice == "1 minuto":
            lookback = last_time - timedelta(hours=2) # Mostra le ultime 2 ore
        elif tf_choice == "15 minuti":
            lookback = last_time - timedelta(hours=6) # Mostra le ultime 6 ore
        else:
            lookback = last_time - timedelta(days=1)   # Mostra l'ultimo giorno
            
        v_norm_zoom = v_norm.loc[v_norm.index >= lookback]

        # --- LOGICA ALERT ---
        last, prev, threshold = v_norm.iloc[-1], v_norm.iloc[-2], 1.3
        bulls = [c for c in v_norm.columns if prev[c] < -threshold and last[c] > prev[c]]
        bears = [c for c in v_norm.columns if prev[c] > threshold and last[c] < prev[c]]

        if bulls and bears:
            for b_up in bulls:
                for b_down in bears:
                    msg = f"COMPRA {b_up}/{b_down}"
                    st.error(f"🔥 **{msg}**")
                    new_entry = {'Orario': v_norm.index[-1].strftime('%H:%M'), 'Segnale': msg, 'TF': tf_choice}
                    if st.session_state.signal_history.empty or st.session_state.signal_history.iloc[0]['Segnale'] != msg:
                        st.session_state.signal_history = pd.concat([pd.DataFrame([new_entry]), st.session_state.signal_history], ignore_index=True)

        # --- GRAFICO ZOOMATO ---
        df_p = v_norm_zoom.reset_index().melt(id_vars=v_norm_zoom.reset_index().columns[0], var_name='Valuta', value_name='Forza')
        
        fig = px.line(df_p, x=df_p.columns[0], y='Forza', color='Valuta', 
                     template="plotly_dark", title=f"Focus Real-Time ({tf_choice})")
        
        for trace in fig.data:
            trace.line.width = 6 if abs(last[trace.name]) >= threshold else 2

        fig.add_hrect(y0=threshold, y1=3.5, fillcolor="red", opacity=0.15)
        fig.add_hrect(y0=-3.5, y1=-threshold, fillcolor="green", opacity=0.15)
        
        # Formattazione asse X per mostrare solo ORE:MINUTI
        fig.update_xaxes(tickformat="%H:%M")
        fig.update_layout(hovermode="x unified", yaxis=dict(range=[-3.5, 3.5]))
        
        st.plotly_chart(fig, use_container_width=True)

        # --- STORICO ---
        st.subheader("📜 Storico Segnali")
        st.dataframe(st.session_state.signal_history, use_container_width=True)
        if st.sidebar.button("Svuota Storico"):
            st.session_state.signal_history = pd.DataFrame(columns=['Orario', 'Segnale', 'TF'])
            st.rerun()
            
    else:
        st.info("In attesa dei dati... Verifica connessione o apertura mercati.")

except Exception as e:
    st.warning(f"Ricezione dati in corso... ({e})")
