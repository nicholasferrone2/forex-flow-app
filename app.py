import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Forex Flow Pro", layout="wide")

# Lista coppie per il calcolo della forza
pairs = ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X', 'USDCAD=X', 'USDCHF=X', 'EURJPY=X', 'GBPJPY=X']

@st.cache_data(ttl=300)
def get_data():
    df = yf.download(pairs, period="2d", interval="15m")['Close']
    vol = yf.download(pairs, period="1d", interval="15m")['Volume']
    return df, vol

try:
    prices, volumes = get_data()
    
    # Calcolo Forza Relativa
    pct = prices.pct_change().iloc[-1] * 100
    strength = {
        'USD': -(pct['EURUSD=X'] + pct['GBPUSD=X']) / 2,
        'EUR': (pct['EURUSD=X'] + pct['EURJPY=X']) / 2,
        'GBP': (pct['GBPUSD=X'] + pct['GBPJPY=X']) / 2,
        'JPY': -(pct['USDJPY=X'] + pct['EURJPY=X']) / 2
    }

    st.title("🏛️ Forex Flow Intelligence")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("⚡ Currency Strength Radar")
        fig_radar = draw_radar(strength) # Funzione semplificata
        st.plotly_chart(fig_radar)

    with col2:
        st.subheader("📊 Relative Volume")
        st.bar_chart(volumes.iloc[-1])

except Exception as e:
    st.error(f"In attesa di dati dal mercato... {e}")
