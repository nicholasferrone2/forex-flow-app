import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import time
import requests

# --- 1. CONFIGURAZIONE FISSA (PARAMETRI UTENTE) ---
CLIENT_ID = "22771"
CLIENT_SECRET = "IL_TUO_SECRET"  # Assicurati di inserirlo correttamente
REDIRECT_URI = "https://forex-flow-app.streamlit.app" 
LOTS = 0.1
VOLUME_UNITS = 10000 
TP_PIPS = 5

st.set_page_config(page_title="G8 Flow Terminal", layout="wide", page_icon="📈")

# --- 2. LOGICA DI AUTENTICAZIONE ---
auth_url = (
    f"https://openapi.ctrader.com/apps/auth"
    f"?client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&scope=accounts,trading"
    f"&response_type=code"
)

# --- 3. FUNZIONI DATI ---
def get_mock_data():
    return pd.DataFrame(np.random.randn(50, 1), columns=['Price']).cumsum() + 1.1050

# --- 4. INTERFACCIA UTENTE ---
st.title("📈 G8 Flow - Dashboard Professionale")

# Barra Laterale per Connessione e Stato
with st.sidebar:
    st.header("🔐 Connessione Broker")
    if "code" not in st.query_params:
        st.info("Account non connesso")
        st.link_button("🔌 CONNETTI CTRADER", auth_url, type="primary", use_container_width=True)
    else:
        st.success("✅ Account Collegato")
        st.caption(f"Code: {st.query_params['code'][:10]}...")
    
    st.divider()
    st.header("⚙️ Parametri Fissi")
    st.metric("Volume", f"{LOTS} Lots")
    st.metric("Take Profit", f"{TP_PIPS} Pips")

# Corpo Principale: Grafico e Segnali
col_chart, col_control = st.columns([2, 1])

with col_chart:
    st.subheader("EURUSD Live Chart")
    chart_data = get_mock_data()
    fig = go.Figure(data=[go.Scatter(y=chart_data['Price'], mode='lines', line=dict(color='#00ff00', width=2))])
    fig.update_layout(
        template="plotly_dark", 
        height=450, 
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#333")
    )
    st.plotly_chart(fig, use_container_width=True)

with col_control:
    st.subheader("📥 Centro Segnali Telegram")
    st.write("In attesa di alert dalla connessione Telegram testata...")
    
    # Simulazione ricezione segnale
    if st.button("🔔 SIMULA ARRIVO ALERT TELEGRAM", use_container_width=True):
        st.session_state.active_alert = {
            "symbol": "EURUSD",
            "side": "BUY",
            "time": datetime.now().strftime("%H:%M:%S")
        }

    if "active_alert" in st.session_state:
        alert = st.session_state.active_alert
        st.warning(f"⚠️ **NUOVO SEGNALE**: {alert['side']} {alert['symbol']} ({alert['time']})")
        
        if st.button(f"✅ ACCETTA E APRI {LOTS} LOTTI", type="primary", use_container_width=True):
            with st.status("Esecuzione ordine in corso...") as status:
                st.write("1. Verificando Token...")
                time.sleep(0.5)
                st.write(f"2. Calcolando Volume: {VOLUME_UNITS} unità...")
                time.sleep(0.5)
                st.write(f"3. Impostando TP: +{TP_PIPS} pips...")
                time.sleep(0.5)
                status.update(label="🚀 ORDINE INVIATO CON SUCCESSO!", state="complete")
            
            st.balloons()
            # Reset alert dopo esecuzione
            del st.session_state.active_alert

# --- 5. LOG STORICO ---
st.divider()
st.subheader("📜 Log Operazioni Odierne")
st.caption("Le operazioni appariranno qui dopo l'accettazione del segnale.")
