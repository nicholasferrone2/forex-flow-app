# --- TEST RICEZIONE SEGNALE ESTERNO ---
st.divider()
st.subheader("📡 Test Ricezione Segnale (Simulazione Webhook)")

# Simuliamo un URL che riceve dati
if st.button("Simula Arrivo Segnale da TradingView"):
    # Dati che arriverebbero dall'esterno
    data_esterna = {
        "action": "BUY",
        "symbol": "EURUSD",
        "lots": 0.1,
        "tp_pips": 5
    }
    
    st.write("### 📥 Segnale Intercettato dal Web!")
    st.json(data_esterna)
    
    # La logica del bot trasforma i lotti in unità per cTrader
    volume_units = int(data_esterna["lots"] * 100000)
    
    st.success(f"Logica Pronta: Invierei un ordine {data_esterna['action']} di {volume_units} unità con TP {data_esterna['tp_pips']} pips.")
    st.balloons()
