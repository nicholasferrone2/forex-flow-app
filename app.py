import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURAZIONE FISSA ---
LOTS = 0.1
TP_PIPS = 5
MONETE = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF', 'NZDUSD', 'EURJPY']

st.set_page_config(page_title="G8 Flow - Dashboard", layout="wide")

st.title("📊 G8 Flow: Monitoraggio Ipercomprato/Ipervenduto")
st.write(f"Configurazione Operativa: **{LOTS} Lotti** | **{TP_PIPS} Pips TP**")

# --- GENERAZIONE DATI SIMULATI G8 ---
def get_g8_data():
    data = []
    for m in MONETE:
        rsi = np.random.randint(20, 80)
        stato = "Neutro"
        color = "white"
        if rsi > 70:
            stato = "🔴 IPERCOMPRATO (SELL)"
            color = "#ff4b4b"
        elif rsi < 30:
            stato = "🟢 IPERVENDUTO (BUY)"
            color = "#00ff00"
        data.append({"Coppia": m, "RSI (14)": rsi, "Stato": stato, "Color": color})
    return pd.DataFrame(data)

df_g8 = get_g8_data()

# --- LAYOUT DASHBOARD ---
col_table, col_chart = st.columns([1, 1])

with col_table:
    st.subheader("Stato di Forza G8")
    for _, row in df_g8.iterrows():
        st.markdown(f"""
        <div style="padding:10px; border-radius:5px; border:1px solid #444; margin-bottom:5px; background-color:#1e1e1e">
            <span style="font-weight:bold; font-size:18px;">{row['Coppia']}</span> 
            <span style="float:right; color:{row['Color']}; font-weight:bold;">{row['Stato']} | RSI: {row['RSI (14)']}</span>
        </div>
        """, unsafe_allow_html=True)

with col_chart:
    st.subheader("Distribuzione RSI")
    fig_bar = go.Figure(data=[go.Bar(
        x=df_g8['Coppia'], 
        y=df_g8['RSI (14)'],
        marker_color=['red' if x > 70 else 'green' if x < 30 else 'gray' for x in df_g8['RSI (14)']]
    )])
    fig_bar.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
    fig_bar.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
    fig_bar.update_layout(template="plotly_dark", height=400, yaxis_range=[0, 100])
    st.plotly_chart(fig_bar, use_container_width=True)

# --- AREA ESECUZIONE (DA TELEGRAM/MANUALE) ---
st.divider()
st.subheader("⚡ Esecuzione Rapida")
col_sel, col_btn = st.columns([1, 1])

with col_sel:
    scelta = st.selectbox("Seleziona Coppia dal Segnale", MONETE)

with col_btn:
    if st.button(f"ESEGUI {scelta} (0.1 Lots / 5 Pips TP)", type="primary", use_container_width=True):
        st.balloons()
        st.success(f"Ordine inviato su {scelta}: BUY/SELL 0.1 lotti con TP 5 pips.")

st.caption(f"Aggiornato alle {datetime.now().strftime('%H:%M:%S')}")
