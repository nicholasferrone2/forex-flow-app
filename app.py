import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Forex Volume Strength", layout="wide")

st.title("📊 Indice di Forza basato sul Volume")
st.markdown("Le linee mostrano l'afflusso di scambi (Volume) per ogni singola valuta nel tempo.")

# Coppie necessarie per isolare le valute principali
pairs = ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X', 'USDCAD=X', 'EURJPY=X', 'GBPJPY=X', 'EURGBP=X']

@st.cache_data(ttl=600)
def get_raw_volumes():
    data = yf.download(pairs, period="2d", interval="15m")['Volume']
    return data.dropna()

try:
    v_data = get_raw_volumes()
    
    if not v_data.empty:
        # Creiamo un nuovo DataFrame per la forza del volume delle singole valute
        v_strength = pd.DataFrame(index=v_data.index)
        
        # Calcolo Volume Isolato (Somma dei tick volume per ogni valuta)
        v_strength['USD'] = v_data['EURUSD=X'] + v_data['GBPUSD=X'] + v_data['USDJPY=X'] + v_data['USDCAD=X'] + v_data['AUDUSD=X']
        v_strength['EUR'] = v_data['EURUSD=X'] + v_data['EURJPY=X'] + v_data['EURGBP=X']
        v_strength['GBP'] = v_data['GBPUSD=X'] + v_data['GBPJPY=X'] + v_data['EURGBP=X']
        v_strength['JPY'] = v_data['USDJPY=X'] + v_data['EURJPY=X'] + v_data['GBPJPY=X']
        v_strength['AUD'] = v_data['AUDUSD=X']

        # Normalizzazione (per rendere le linee confrontabili tra loro)
        v_strength_norm = (v_strength - v_strength.mean()) / v_strength.std()

        # Trasformazione per Plotly (da colonne a righe)
        df_plot = v_strength_norm.reset_index().melt(id_vars='Datetime', var_name='Valuta', value_name='Intensità Volume')

        # GRAFICO CARTESIANO A LINEE
        fig = px.line(
            df_plot, 
            x='Datetime', 
            y='Intensità Volume', 
            color='Valuta',
            title="Flusso di Volume Relativo per Valuta (Z-Score)",
            template="plotly_dark",
            line_shape="spline" # Rende le linee più morbide
        )
        
        fig.update_layout(
            xaxis_title="Tempo (Sessione di trading)",
            yaxis_title="Deviazione Volume (Forza Scambi)",
            hovermode="x unified"
        )

        st.plotly_chart(fig, use_container_width=True)
        
        st.success(f"Dati analizzati correttamente. Ultimo segnale: {v_data.index[-1].strftime('%H:%M')}")
    else:
        st.warning("Mercato chiuso. Le linee dei volumi appariranno alla riapertura di stasera.")

except Exception as e:
    st.error(f"Errore nel calcolo dei flussi: {e}")
