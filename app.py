import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Forex Strength Analyzer", layout="wide")

st.title("🏛️ Analisi Cartesiana Forza Valute")
st.markdown("L'asse Y indica la forza relativa (%), l'asse X indica la valuta.")

# Configurazione coppie
pairs = ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X', 'USDCAD=X', 'EURJPY=X', 'GBPJPY=X']

@st.cache_data(ttl=600)
def get_data():
    # Scarichiamo gli ultimi 7 giorni per avere i dati di venerdì
    df = yf.download(pairs, period="7d", interval="15m")['Close']
    return df.dropna()

try:
    prices = get_data()
    
    if not prices.empty:
        # Calcolo forza relativa sull'ultimo movimento disponibile
        last_p = prices.iloc[-1]
        prev_p = prices.iloc[-2]
        pct = ((last_p - prev_p) / prev_p) * 100
        
        # Mappa della forza
        strength_data = {
            'Valuta': ['USD', 'EUR', 'GBP', 'JPY', 'AUD'],
            'Forza (%)': [
                float(-(pct['EURUSD=X'] + pct['GBPUSD=X'] + pct['AUDUSD=X']) / 3),
                float((pct['EURUSD=X'] + pct['EURJPY=X']) / 2),
                float((pct['GBPUSD=X'] + pct['GBPJPY=X']) / 2),
                float(-(pct['USDJPY=X'] + pct['EURJPY=X'] + pct['GBPJPY=X']) / 3),
                float(pct['AUDUSD=X'])
            ]
        }
        
        df_strength = pd.DataFrame(strength_data)

        # CREAZIONE DIAGRAMMA CARTESIANO
        fig = px.bar(
            df_strength, 
            x='Valuta', 
            y='Forza (%)',
            color='Forza (%)',
            color_continuous_scale='RdYlGn', # Verde per positivo, Rosso per negativo
            range_y=[-2, 2] # Limiti asse ordinate
        )
        
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="white",
            yaxis=dict(gridcolor='gray', zerolinecolor='white'),
            xaxis=dict(title="Valute (Ascisse)"),
            yaxis_title="Forza Relativa % (Ordinate)"
        )

        st.plotly_chart(fig, use_container_width=True)
        
        st.info(f"Dati riferiti all'ultima sessione attiva: {prices.index[-1].strftime('%d/%m %H:%M')}")
    else:
        st.warning("Mercati chiusi. Nessun dato disponibile per il diagramma.")

except Exception as e:
    st.error(f"Errore nel calcolo cartesiano: {e}")
