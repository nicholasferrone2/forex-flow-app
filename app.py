import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Forex Volume Flow Pro", layout="wide", page_icon="📈")

# --- CONFIGURAZIONE INTERFACCIA ---
st.title("📊 Volume Flow Analyzer")
st.sidebar.header("⚙️ Impostazioni Analisi")

# Selezione Timeframe
tf_choice = st.sidebar.selectbox(
    "Seleziona l'intervallo temporale:",
    ("1 minuto", "15 minuti", "30 minuti", "1 ora"),
    index=1
)

# Mappatura dei parametri per Yahoo Finance
tf_map = {
    "1 minuto": {"int": "1m", "per": "1d"},
    "15 minuti": {"int": "15m", "per": "5d"},
    "30 minuti": {"int": "30m", "per": "5d"},
    "1 ora": {"int": "60m", "per": "720d"} # Fino a 2 anni di storico per l'orario
}

selected_tf = tf_map[tf_choice]

# Coppie valutarie per isolare i flussi
pairs = ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X', 'USDCAD=X', 'EURJPY=X', 'GBPJPY=X', 'EURGBP=X']

@st.cache_data(ttl=60)
def get_volume_flow(interval, period):
    data = yf.download(pairs, period=period, interval=interval)['Volume']
    return data.dropna()

try:
    v_data = get_volume_flow(selected_tf["int"], selected_tf["per"])
    
    if not v_data.empty:
        # Calcolo Volume Isolato per singola valuta
        v_strength = pd.DataFrame(index=v_data.index)
        v_strength['USD'] = v_data['EURUSD=X'] + v_data['GBPUSD=X'] + v_data['USDJPY=X'] + v_data['USDCAD=X'] + v_data['AUDUSD=X']
        v_strength['EUR'] = v_data['EURUSD=X'] + v_data['EURJPY=X'] + v_data['EURGBP=X']
        v_strength['GBP'] = v_data['GBPUSD=X'] + v_data['GBPJPY=X'] + v_data['EURGBP=X']
        v_strength['JPY'] = v_data['USDJPY=X'] + v_data['EURJPY=X'] + v_data['GBPJPY=X']
        v_strength['AUD'] = v_data['AUDUSD=X']

        # Normalizzazione (Z-Score) per rendere i dati leggibili sul grafico cartesiano
        v_strength_norm = (v_strength - v_strength.mean()) / v_strength.std()

        # Preparazione dati per Plotly
        df_plot = v_strength_norm.reset_index().melt(id_vars='Datetime' if 'Datetime' in v_strength_norm.reset_index() else 'Date', 
                                                   var_name='Valuta', value_name='Intensità Volume')

        # GRAFICO CARTESIANO A LINEE
        fig = px.line(
            df_plot, 
            x=df_plot.columns[0], # Usa automaticamente Datetime o Date
            y='Intensità Volume', 
            color='Valuta',
            title=f"Flusso Volume Relativo - Timeframe: {tf_choice}",
            template="plotly_dark",
            line_shape="linear"
        )
        
        fig.update_layout(
            xaxis_title="Tempo",
            yaxis_title="Deviazione Volume (Forza)",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, use_container_width=True)
        
        # Statistiche rapide sotto il grafico
        st.divider()
        cols = st.columns(5)
        for i, curr in enumerate(['USD', 'EUR', 'GBP', 'JPY', 'AUD']):
            last_val = v_strength_norm[curr].iloc[-1]
            color = "green" if last_val > 0 else "red"
            cols[i].metric(curr, f"{last_val:.2f}", delta="Volume High" if last_val > 1 else "Normal")

    else:
        st.warning(f"Nessun dato trovato per il timeframe {tf_choice}. Potrebbe essere dovuto alla chiusura del mercato.")

except Exception as e:
    st.error(f"Errore durante l'analisi: {e}")
