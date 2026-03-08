# --- GRAFICO OTTIMIZZATO ---
df_plot = v_strength_norm.reset_index().melt(
    id_vars=v_strength_norm.reset_index().columns[0], 
    var_name='Valuta', 
    value_name='Forza Volume'
)

fig = px.line(
    df_plot, 
    x=df_plot.columns[0], 
    y='Forza Volume', 
    color='Valuta',
    title="Monitoraggio Flussi G8 (Clicca sulla legenda per isolare)",
    template="plotly_dark",
    category_orders={"Valuta": ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "NZD"]}
)

# Miglioramento visivo: linee più spesse e interattività
fig.update_traces(line=dict(width=2), hovertemplate='<b>%{fullData.name}</b><br>Forza: %{y:.2f}<br>Ora: %{x}<extra></extra>')

fig.update_layout(
    hovermode="x unified",
    yaxis=dict(range=[-3, 3]), # Blocca l'asse Y per evitare salti visivi
    legend=dict(itemclick="toggle", itemdoubleclick="toggleothers") # Comandi isolamento
)

# Linee di soglia iper-comprato/venduto
fig.add_hrect(y0=1.3, y1=3, fillcolor="red", opacity=0.1, line_width=0, annotation_text="AREA REVERSAL SHORT")
fig.add_hrect(y0=-3, y1=-1.3, fillcolor="green", opacity=0.1, line_width=0, annotation_text="AREA REVERSAL LONG")

st.plotly_chart(fig, use_container_width=True)
