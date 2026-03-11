import streamlit as st

# --- IMPOSTAZIONI FISSE RICHIESTE ---
LOTS = 0.1
VOLUME_CTRADE = 10000  # 0.1 lotti nelle API = 10k unità
TAKE_PROFIT_PIPS = 5

st.set_page_config(page_title="G8 Flow - Signal Test", page_icon="⚡")

st.title("⚡ G8 Flow: Simulazione Segnale")
st.write(f"Configurazione attiva: **{LOTS} Lotti** | **{TAKE_PROFIT_PIPS} Pips TP**")

# --- INTERFACCIA TEST ---
st.divider()
st.subheader("📡 Pannello di Invio Falso Segnale")
st.write("Clicca il tasto sotto per simulare un segnale in arrivo.")

col1, col2 = st.columns(2)

with col1:
    if st.button("🔵 SIMULA BUY EURUSD", use_container_width=True):
        st.session_state.ultimo_segnale = {"side": "BUY", "symbol": "EURUSD"}

with col2:
    if st.button("🔴 SIMULA SELL GBPUSD", use_container_width=True):
        st.session_state.ultimo_segnale = {"side": "SELL", "symbol": "GBPUSD"}

# --- LOGICA DI ESECUZIONE (SIMULATA) ---
if "ultimo_segnale" in st.session_state:
    segnale = st.session_state.ultimo_segnale
    
    st.markdown("---")
    st.success(f"📩 **Segnale Ricevuto!** Direzione: {segnale['side']} su {segnale['symbol']}")
    
    # Costruiamo l'ordine esattamente come lo vorrebbe cTrader
    ordine_da_inviare = {
        "account_id": "1234567 (Esempio)",
        "symbol": segnale['symbol'],
        "tradeSide": segnale['side'],
        "volume": VOLUME_CTRADE,
        "takeProfit": TAKE_PROFIT_PIPS,
        "type": "MARKET"
    }
    
    st.write("### 🛠️ Costruzione Ordine:")
    st.json(ordine_da_inviare)
    
    st.info(f"⚙️ L'app sta tentando di inviare {VOLUME_CTRADE} unità con TP a {TAKE_PROFIT_PIPS} pips...")
    
    # Simulazione ritardo esecuzione
    import time
    with st.spinner("Invio al broker in corso..."):
        time.sleep(1.5)
        st.balloons()
        st.success(f"✅ OPERAZIONE ESEGUITA: {segnale['side']} {LOTS} lotti su {segnale['symbol']}")
        st.write(f"📈 Take Profit impostato a +{TAKE_PROFIT_PIPS} pips.")

st.divider()
st.caption("Nota: Questo è un test della logica. L'ordine sarà reale solo dopo il login riuscito.")
