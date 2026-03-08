import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Forex Flow Pro", layout="wide", page_icon="🏛️")

# 1. FUNZIONE RADAR (Indispensabile per evitare l'errore precedente)
def draw_radar(strength_dict):
    categories = list(strength_dict.keys())
    values = list(strength_dict.values())
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values, theta=categories, fill='toself', line_color='#00ffcc'
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[-1.5, 1.5]), bgcolor="#1e1e1e"),
        showlegend=False, paper_bgcolor="rgba(0,0,0,0)", font_color="white"
    )
    return fig

# 2. RECUPERO DATI (Con protezione per il weekend)
st.title("🏛️ Forex Flow Intelligence")
pairs = ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X', 'USDCAD=X', 'EURJPY=X', 'GBPJPY=X']

@st.cache_data(ttl=600)
def get_forex_data():
    # Scarichiamo 7 giorni per coprire sempre l'ultimo venerdì utile
    data = yf.download(pairs, period="7d", interval="15m")
    return data['Close'].dropna(), data['Volume'].dropna()

try:
    prices, volumes = get_forex_data()
    
    if not prices.empty:
        # Calcolo sulla base dell'ultima chiusura disponibile
        last_prices = prices.iloc[-1]
        prev_prices = prices.iloc[-2]
        pct = ((last_prices - prev_prices) / prev_prices) * 100
        
        strength = {
            'USD': float(-(pct['EURUSD=X'] + pct['GBPUSD=X'] + pct['AUDUSD=X']) / 3),
            'EUR': float((pct['EURUSD=X'] + pct['EURJPY=X']) / 2),
            'GBP': float((pct['GBPUSD=X'] + pct['GBPJPY=X']) / 2),
            'JPY': float(-(pct['USDJPY=X'] + pct['EURJPY=X'] + pct['GBPJPY=X']) / 3),
            'AUD': float(pct['AUDUSD=X'])
        }

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("⚡ Currency Strength Radar")
            st.plotly_chart(draw_radar(strength), use_container_width=True)
        with col2:
            st.subheader("📊 Volume Activity")
            st.bar_chart(volumes.iloc[-1].rename(lambda x: x.replace('=X', '')))
            
        st.info(f"Dati aggiornati al: {prices.index[-1].strftime('%d/%m %H:%M')}")
    else:
        st.warning("Dati non disponibili. Riprova tra poco.")

except Exception as e:
    st.error(f"Errore tecnico: {e}")
