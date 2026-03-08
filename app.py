import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Forex Global Signal Pro", layout="wide", page_icon="⚡")

# --- INIZIALIZZAZIONE STORICO ---
if 'signal_history' not in st.session_state:
    st.session_state.signal_history = pd.DataFrame(columns=['Orario', 'Segnale', 'Valuta Up', 'Valuta Down', 'Timeframe'])

st.title("⚡ Forex Pair Signal System & History")

# --- SIDEBAR CONFIG ---
st.sidebar.header("⚙️ Configurazione")
tf_choice = st.sidebar.selectbox("Intervallo Temporale:", ("1 minuto", "15 minuti", "30 minuti", "1 ora"), index=1)
tf_map = {
    "1 minuto": {"int": "1m", "per": "1d"},
    "15 minuti": {"int": "15m", "per": "5d"},
    "30 minuti": {"int": "30m", "per": "5d"},
    "1 ora": {"int": "60m", "per": "60d"}
}
selected_tf = tf_map[tf_choice]

pairs = ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X', 'USDCAD=X', 'USDCHF=X', 'NZDUSD=X',
         'EURJPY=X', 'GBPJPY=X', 'EURGBP=X', 'AUDJPY=X', 'CHFJPY=X']

@st.cache_data(ttl=60)
def get_global_flow(interval, period):
    data = yf.download(pairs, period=period, interval=interval)['Volume']
    return data.dropna()

try:
    v_data = get_global_flow(selected_tf["int"], selected_tf["per"])
    
    if not v_data.empty:
        v_strength = pd.DataFrame(index=v_data.index)
        v_strength['USD'] = v_data[['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X', 'USDCAD=X', 'USDCHF=X', 'NZDUSD=X']].sum(axis=1)
        v_strength['EUR'] = v_data[['EURUSD=X', 'EURJPY=X', 'EURGBP=X']].sum(axis=1)
        v_strength['GBP'] = v_data[['GBPUSD=X', 'GBPJPY=X', 'EURGBP=X']].sum(axis=1)
        v_strength['JPY'] = v_data[['USDJPY=X', 'EURJPY=X', 'GBPJPY=X', 'AUDJPY=X', 'CHFJPY=X']].sum(axis=1)
        v_strength['AUD'] = v_data[['AUDUSD=X', 'AUDJPY=X']].sum(axis=1)
        v_strength['CHF'] = v_data[['USDCHF=X', 'CHFJPY=X']].sum(axis=1)
        v_strength['CAD'] = v_data['USDCAD=X']
        v_strength['NZD'] = v_data['NZDUSD=X']

        v_strength_norm = (v_strength - v_strength.mean()) / v_strength.std()
        
        # --- LOGICA DEI SEGNALI ---
        st.subheader("🎯 Segnali Operativi Real-Time")
        last = v_strength_norm.iloc[-1]
        prev = v_strength_norm.iloc[-2]
        threshold = 1.3
        
        bullish_rev, bearish_rev = [], []
        for curr in v_strength_norm.columns:
            if prev[curr] < -threshold and last[curr] > prev[curr]: bullish_rev.append(curr)
            if prev[curr] > threshold and last[curr] < prev[curr]: bearish_rev.append(curr)

        if bullish_rev and bearish_rev:
            for b_up in bullish_rev:
                for b_down in bearish_rev:
                    signal_text = f"COMPRA {b_up}/{b_down}"
                    st.error(f"🔥 **{signal_text}** (o VENDI {b_down}/{b_up})")
                    
                    # Aggiunta allo storico se non è già l'ultimo inserito
                    new_entry = {
                        'Orario': v_data.index[-1].strftime('%H:%M:%S'),
                        'Segnale': signal_text,
                        'Valuta Up': b_up,
                        'Valuta Down': b_down,
                        'Timeframe': tf_choice
                    }
                    # Evita duplicati identici consecutivi
                    if st.session_state.signal_history.empty or st.session_state.signal_history.iloc[0]['Segnale'] != signal_text:
                        st.session_state.signal_history = pd.concat([pd.DataFrame([new_entry]), st.session_state.signal_history], ignore_index=True)

        # --- GRAFICO ---
        df_plot = v_strength_norm.reset_index().melt(id_vars=v_strength_norm.reset_index().columns[0], var_name='Valuta', value_name='Forza Volume')
        fig = px.line(df_plot, x=df_plot.columns[0], y='Forza Volume', color='Valuta', template="plotly_dark")
        fig.add_hline(y=threshold, line_dash="dot", line_color="red")
        fig.add_hline(y=-threshold, line_dash="dot", line_color="green")
        st.plotly_chart(fig, use_container_width=True)

        # --- TABELLA STORICO ---
        st.divider()
        st.subheader("📜 Storico Segnali della Sessione")
        if not st.session_state.signal_history.empty:
            st.dataframe(st.session_state.signal_history, use_container_width=True)
            if st.button("Pulisci Storico"):
                st.session_state.signal_history = pd.DataFrame(columns=['Orario', 'Segnale', 'Valuta Up', 'Valuta Down', 'Timeframe'])
                st.rerun()
        else:
            st.info("Nessun segnale registrato finora in questa sessione.")

    else:
        st.info("In attesa dell'apertura dei mercati (Stasera ore 23:00).")

except Exception as e:
    st.error(f"Errore: {e}")
