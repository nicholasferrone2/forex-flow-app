import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Forex Strength G8", layout="wide", page_icon="📈")

if 'signal_history' not in st.session_state:
    st.session_state.signal_history = pd.DataFrame(columns=['Orario', 'Segnale', 'Timeframe'])

# --- GUIDA ---
with st.expander("📖 Legenda e Guida"):
    st.markdown("""
    * **8 Linee:** Ogni linea rappresenta la forza di una valuta G8 rispetto al paniere globale.
    * **Sopra 1.3 (Area Rossa):** Valuta molto forte, possibile inversione al ribasso (Short).
    * **Sotto -1.3 (Area Verde):** Valuta molto debole, possibile inversione al rialzo (Long).
    * **Segnale:** Appare quando una linea "rossa" scende e una "verde" sale contemporaneamente.
    """)

st.title("📈 G8 Currency Strength Meter")

# --- CONFIGURAZIONE ---
tf_choice = st.sidebar.selectbox("Timeframe:", ("1 minuto", "15 minuti", "1 ora"), index=1)
tf_map = {"1 minuto": "1m", "15 minuti": "15m", "1 ora": "60m"}
period_map = {"1m": "1d", "15m": "5d", "60m": "60d"}

# Usiamo i prezzi di chiusura (Adj Close) che sono sempre disponibili
pairs = ['EURUSD=X','GBPUSD=X','USDJPY=X','AUDUSD=X','USDCAD=X','USDCHF=X','NZDUSD=X']

@st.cache_data(ttl=60)
def get_forex_data(interval, period):
    data = yf.download(pairs, period=period, interval=interval)['Adj Close']
    return data.ffill().dropna()

try:
    df = get_forex_data(tf_map[tf_choice], period_map[tf_map[tf_choice]])
    
    if not df.empty:
        # Calcolo variazioni percentuali cumulate per isolare le valute
        returns = df.pct_change().dropna()
        
        v_s = pd.DataFrame(index=returns.index)
        v_s['EUR'] = returns['EURUSD=X']
        v_s['GBP'] = returns['GBPUSD=X']
        v_s['JPY'] = -returns['USDJPY=X']
        v_s['AUD'] = returns['AUDUSD=X']
        v_s['CAD'] = -returns['USDCAD=X']
        v_s['CHF'] = -returns['USDCHF=X']
        v_s['NZD'] = returns['NZDUSD=X']
        v_s['USD'] = -(returns.mean(axis=1)) # Il dollaro come controparte media

        # Normalizzazione Z-Score per avere le linee che oscillano tra -3 e +3
        v_norm = (v_s - v_s.mean()) / v_s.std()
        
        # --- ALERT ---
        last, prev, threshold = v_norm.iloc[-1], v_norm.iloc[-2], 1.3
        bulls = [c for c in v_norm.columns if prev[c] < -threshold and last[c] > prev[c]]
        bears = [c for c in v_norm.columns if prev[c] > threshold and last[c] < prev[c]]

        st.subheader("🎯 Segnali Operativi")
        if bulls and bears:
            for b_up in bulls:
                for b_down in bears:
                    msg = f"COMPRA {b_up}/{b_down}"
                    st.error(f"🔥 **{msg}**")
                    new_entry = {'Orario': returns.index[-1].strftime('%H:%M'), 'Segnale': msg, 'Timeframe': tf_choice}
                    if st.session_state.signal_history.empty or st.session_state.signal_history.iloc[0]['Segnale'] != msg:
                        st.session_state.signal_history = pd.concat([pd.DataFrame([new_entry]), st.session_state.signal_history], ignore_index=True)
        else:
            st.success("✅ Flussi in equilibrio. Nessun incrocio di controtendenza.")

        # --- GRAFICO DELLE 8 LINEE ---
        df_p = v_norm.reset_index().melt(id_vars=v_norm.reset_index().columns[0], var_name='Valuta', value_name='Forza')
        fig = px.line(df_p, x=df_p.columns[0], y='Forza', color='Valuta', template="plotly_dark", title="Movimento Real-Time Valute G8")
        
        for trace in fig.data:
            trace.line.width = 6 if abs(last[trace.name]) >= threshold else 1.5

        fig.add_hrect(y0=threshold, y1=3.5, fillcolor="red", opacity=0.15, annotation_text="IPER-COMPRATO")
        fig.add_hrect(y0=-3.5, y1=-threshold, fillcolor="green", opacity=0.15, annotation_text="IPER-VENDUTO")
        fig.update_layout(hovermode="x unified", yaxis=dict(range=[-3.5, 3.5]))
        st.plotly_chart(fig, use_container_width=True)

        # --- STORICO ---
        st.subheader("📜 Storico")
        st.dataframe(st.session_state.signal_history, use_container_width=True)
        if st.sidebar.button("Reset Storico"):
            st.session_state.signal_history = pd.DataFrame(columns=['Orario', 'Segnale', 'Timeframe'])
            st.rerun()
            
    else:
        st.info("Dati non disponibili. I mercati aprono alle 23:00.")
except Exception as e:
    st.error(f"Errore: {e}")
