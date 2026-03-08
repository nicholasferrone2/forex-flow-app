import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Forex Global Signal Pro", layout="wide", page_icon="⚡")

st.title("⚡ Forex Pair Signal System")
st.sidebar.header("⚙️ Configurazione")

tf_choice = st.sidebar.selectbox("Intervallo Temporale:", ("1 minuto", "15 minuti", "30 minuti", "1 ora"), index=1)
tf_map = {
    "1 minuto": {"int": "1m", "per": "1d"},
    "15 minuti": {"int": "15m", "per": "5d"},
    "30 minuti": {"int": "30m", "per": "5d"},
    "1 ora": {"int": "60m", "per": "60d"}
}
selected_tf = tf_map[tf_choice]

pairs = [
    'EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X', 'USDCAD=X', 'USDCHF=X', 'NZDUSD=X',
    'EURJPY=X', 'GBPJPY=X', 'EURGBP=X', 'AUDJPY=X', 'CHFJPY=X'
]

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
        
        # --- LOGICA DEI SEGNALI INCROCIATI (PAIR SIGNALS) ---
        st.subheader("🎯 Segnali Operativi Real-Time")
        
        last = v_strength_norm.iloc[-1]
        prev = v_strength_norm.iloc[-2]
        threshold = 1.3  # Soglia per iper-comprato/venduto
        
        bullish_rev = [] # Valute che stanno invertendo al rialzo
        bearish_rev = [] # Valute che stanno invertendo al ribasso

        for curr in v_strength_norm.columns:
            if prev[curr] < -threshold and last[curr] > prev[curr]:
                bullish_rev.append(curr)
            if prev[curr] > threshold and last[curr] < prev[curr]:
                bearish_rev.append(curr)

        # Generazione dei messaggi "Compra/Vendi" incrociati
        found_signal = False
        if bullish_rev and bearish_rev:
            for b_up in bullish_rev:
                for b_down in bearish_rev:
                    st.error(f"🔥 SEGNALE FORTE: **COMPRA {b_up}/{b_down}** o **VENDI {b_down}/{b_up}**")
                    st.toast(f"Segnale rilevato su {b_up}/{b_down}!")
                    found_signal = True
        
        if not found_signal:
            if bullish_rev or bearish_rev:
                st.warning("Segnali singoli rilevati, in attesa di una controtendenza speculare per confermare il Pair.")
            else:
                st.success("Analisi flussi: Trend attuali stabili, nessuna controtendenza rilevata.")

        # --- GRAFICO ---
        df_plot = v_strength_norm.reset_index().melt(
            id_vars='Datetime' if 'Datetime' in v_strength_norm.reset_index() else 'Date', 
            var_name='Valuta', value_name='Forza Volume'
        )
        fig = px.line(df_plot, x=df_plot.columns[0], y='Forza Volume', color='Valuta',
                     title="Monitoraggio Flussi G8", template="plotly_dark")
        fig.add_hline(y=threshold, line_dash="dot", line_color="red")
        fig.add_hline(y=-threshold, line_dash="dot", line_color="green")
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("I mercati riapriranno stasera alle 23:00.")

except Exception as e:
    st.error(f"Errore: {e}")
