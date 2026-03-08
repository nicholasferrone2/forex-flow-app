import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Forex Global Flow Pro", layout="wide", page_icon="📈")

st.title("🌍 Global Volume Flow Analyzer")
st.sidebar.header("⚙️ Configurazione")

tf_choice = st.sidebar.selectbox(
    "Intervallo Temporale:",
    ("1 minuto", "15 minuti", "30 minuti", "1 ora"),
    index=1
)

tf_map = {
    "1 minuto": {"int": "1m", "per": "1d"},
    "15 minuti": {"int": "15m", "per": "5d"},
    "30 minuti": {"int": "30m", "per": "5d"},
    "1 ora": {"int": "60m", "per": "60d"}
}

selected_tf = tf_map[tf_choice]

# Paniere esteso: 8 valute principali (G8)
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
        
        # Calcolo Volume Isolato (Ponderato per le coppie disponibili)
        v_strength['USD'] = v_data[['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X', 'USDCAD=X', 'USDCHF=X', 'NZDUSD=X']].sum(axis=1)
        v_strength['EUR'] = v_data[['EURUSD=X', 'EURJPY=X', 'EURGBP=X']].sum(axis=1)
        v_strength['GBP'] = v_data[['GBPUSD=X', 'GBPJPY=X', 'EURGBP=X']].sum(axis=1)
        v_strength['JPY'] = v_data[['USDJPY=X', 'EURJPY=X', 'GBPJPY=X', 'AUDJPY=X', 'CHFJPY=X']].sum(axis=1)
        v_strength['AUD'] = v_data[['AUDUSD=X', 'AUDJPY=X']].sum(axis=1)
        v_strength['CHF'] = v_data[['USDCHF=X', 'CHFJPY=X']].sum(axis=1)
        v_strength['CAD'] = v_data['USDCAD=X']
        v_strength['NZD'] = v_data['NZDUSD=X']

        # Normalizzazione Z-Score
        v_strength_norm = (v_strength - v_strength.mean()) / v_strength.std()

        df_plot = v_strength_norm.reset_index().melt(
            id_vars='Datetime' if 'Datetime' in v_strength_norm.reset_index() else 'Date', 
            var_name='Valuta', value_name='Forza Volume'
        )

        fig = px.line(
            df_plot, 
            x=df_plot.columns[0], 
            y='Forza Volume', 
            color='Valuta',
            title=f"Flusso Volume Globale G8 - {tf_choice}",
            template="plotly_dark",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        
        fig.update_layout(
            hovermode="x unified",
            xaxis_title="Tempo",
            yaxis_title="Intensità Flussi (Z-Score)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, use_container_width=True)
        
        # Dashboard delle metriche
        st.divider()
        st.subheader("📊 Stato Real-Time Valute")
        m_cols = st.columns(8)
        currs = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'NZD']
        
        for i, c in enumerate(currs):
            val = v_strength_norm[c].iloc[-1]
            status = "🔥 ALTO" if val > 1.5 else "❄️ BASSO" if val < -1.5 else "⚪ MEDIO"
            m_cols[i].metric(c, f"{val:.2f}", status)

    else:
        st.info("I mercati apriranno stasera alle 23:00. Attualmente vengono mostrati i dati dell'ultima chiusura.")

except Exception as e:
    st.error(f"Errore tecnico: {e}")
