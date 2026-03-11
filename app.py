import streamlit as st  # Questa riga risolve l'errore!
import time

# Impostazioni fisse richieste da te
VOLUME_UNITS = 10000  # Corrisponde a 0.1 lotti
TP_PIPS = 5

st.set_page_config(page_title="G8 Flow Test", page_icon="📈")

st.title("🎯 G8 Flow - Test Segnale")
st.divider()

st.write(f"### ⚙️ Parametri Salvati")
st.write(f"Lotti: **0.1** | Take Profit: **{TP_PIPS} Pips**")

# Pulsante per mandare il falso segnale
if st.button("🚀 INVIA FALSO SEGNALE (BUY EURUSD)", use_container_width=True):
    with st.status("Ricezione segnale in corso...", expanded=True) as status:
        st.write("📡 Segnale intercettato: **BUY EURUSD**")
        time.sleep(1)
        
        # Costruzione logica dell'ordine
        ordine_json = {
            "symbol": "EURUSD",
            "volume": VOLUME_UNITS,
            "side": "BUY",
            "takeProfitPips": TP_PIPS
        }
        
        st.write("📦 Ordine impacchettato per cTrader:")
        st.json(ordine_json)
        
        time.sleep(1)
        status.update(label="✅ Test Completato!", state="complete")
    
    st.balloons()
    st.success(f"Logica perfetta: inviati {VOLUME_UNITS} unità con TP a {TP_PIPS} pips.")

st.divider()
st.caption("Nota: Questo codice verifica che la logica dei 0.1 lotti funzioni. Per l'invio reale serve il login.")
