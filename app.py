import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import json

# Recupero configurazioni dai Secrets
TOKEN = st.secrets["8156536376:AAHVyKaFWiCKWoSjBVZ4d0qlIfwJUc7yY5U"]
CHAT_ID = st.secrets["8538711227"]

# Funzione per inviare messaggi con BOTTONI
def send_telegram_trade_signal(pair, action):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    # Creazione dei bottoni
    keyboard = {
        "inline_keyboard": [[
            {"text": f"✅ Esegui {action} {pair}", "callback_data": f"trade_{action}_{pair}"},
            {"text": "❌ Ignora", "callback_data": "ignore"}
        ]]
    }
    
    payload = {
        "chat_id": CHAT_ID,
        "text": f"🚨 **G8 SIGNAL DETECTED**\n\nOperazione consigliata: **{action} {pair}**\nVuoi inviare l'ordine a Pepperstone?",
        "reply_markup": json.dumps(keyboard),
        "parse_mode": "Markdown"
    }
    
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        st.error(f"Errore invio Telegram: {e}")

# --- PARTE DEL MONITOR (Logica G8 già esistente) ---
# ... (Inserisci qui la logica di calcolo forza che abbiamo usato finora) ...

# Esempio di come chiamiamo la funzione nell'app:
# Se EUR è forte e USD è debole:
# send_telegram_trade_signal("EURUSD", "BUY")
