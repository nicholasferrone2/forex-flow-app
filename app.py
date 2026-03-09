import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="G8 Strength Meter", layout="wide")

if 'signal_history' not in st.session_state:
    st.session_state.signal_history = pd.DataFrame(columns=['Orario', 'Segnale', 'Timeframe'])

st.title("📈 G8 Currency Strength Meter")

# --- SIDEBAR ---
tf_choice = st.sidebar.selectbox("Seleziona Timeframe:", ("1 minuto", "15 minuti", "1 ora"), index=1)
tf_map = {"1 minuto": "1m", "15 minuti": "15m", "1 ora": "60m"}
period_map = {"1m": "1d", "15m": "5d", "60m": "60d"}

# Lista coppie necessarie per isolare le 8 valute
pairs = ['EURUSD=X','GBPUSD=X','USDJPY=X','AUDUSD=X','USDCAD=X','USDCHF=X','NZDUSD=X']

@st.cache_data(ttl=60)
def get_clean_data(tf, prd):
    # Scarichiamo i dati e forziamo la pulizia delle colonne
    data = yf.download(pairs, period=prd, interval=tf, group_by='ticker')
    df_close = pd.DataFrame()
    for p in pairs:
        if p in data:
            df_close[p] = data[p]['Close']
    return df_close.ffill().dropna()

try:
    df = get_clean_data(tf_map[tf_choice], period_map[tf_map[tf_choice]])
    
    if not df.empty:
        # Calcolo variazioni percentuali
        rets = df.pct_change().dropna()
        
        # Isiliamo le 8 valute (G8)
        strength = pd.DataFrame(index=rets.index)
        strength['EUR'] = rets['EURUSD=X']
        strength['GBP'] = rets['GBPUSD=X']
        strength['JPY'] = -rets['USDJPY=X']
        strength['AUD'] = rets['AUDUSD=X']
        strength['CAD'] = -rets['USDCAD=X']
        strength['CHF'] = -rets['USDCHF=X']
        strength['NZD'] = rets['NZDUSD=X']
        # Il dollaro è l'inverso della forza media delle altre
        strength['USD'] = -(strength.mean(axis=1))

        # Normalizzazione (Z-Score) per far oscillare le linee tra -3 e +3
        v_norm = (strength - strength.mean()) / strength.std()
        
        # --- LOGICA ALERT ---
        last, prev, threshold = v_norm.iloc[-1], v_norm.iloc[-2], 1.3
        bulls = [c for c in v_norm.columns if prev[c] < -threshold and last[c] > prev[c]]
        bears = [c for c in v_norm.columns if prev[c] > threshold and last[c] < prev[c]]

        if bulls and bears:
            for b_up in bulls:
                for b_down in bears:
                    msg = f"COMPRA {b_up}/{b_down}"
                    st.error(f"🔥 **{msg}**")
                    new_entry = {'Orario': rets.index[-1].strftime('%H:%M'), 'Segnale': msg, 'Timeframe': tf_choice}
                    if st.session_state.signal_history.empty or st.session_state.signal_history.iloc[0]['Segnale'] != msg:
                        st.session_state.signal_history = pd.concat([pd.DataFrame([new_entry]), st.session_state.signal_history], ignore_index=True)

        # --- GRAFICO DELLE 8 LINEE ---
        df_p = v_norm.reset_index().melt(id_vars=v_norm.reset_index().columns[0], var_name='Valuta', value_name='Forza')
        fig = px.line(df_p, x=df_p.columns[0], y='Forza', color='Valuta', template="plotly_dark")
        
        # Inspessisce la linea se è in zona Alert
        for trace in fig.data:
            trace.line.width = 6 if abs(last[trace.name]) >= threshold else 1.5

        fig.add_hrect(y0=threshold, y1=3.5, fillcolor="red", opacity=0.15, annotation_text="IPER-COMPRATO")
        fig.add_hrect(y0=-3.5, y1=-threshold, fillcolor="green", opacity=0.15, annotation_text="IPER-VENDUTO")
        fig.update_layout(hovermode="x unified", yaxis=dict(range=[-3.5, 3.5]))
        st.plotly_chart(fig, use_container_width=True)

        # --- STORICO ---
        st.subheader("📜 Storico Segnali")
        st.dataframe(st.session_state.signal_history, use_container_width=True)
        if st.sidebar.button("Svuota Storico"):
            st.session_state.signal_history = pd.DataFrame(columns=['Orario', 'Segnale', 'Timeframe'])
            st.rerun()
            
    else:
        st.info("In attesa dei dati... (I mercati aprono alle 23:00)")

except Exception as e:
    st.warning(f"Configurazione in corso... Se vedi questo messaggio, attendi l'apertura dei mercati o ricarica la pagina. (Dettaglio: {e})")
