import streamlit as st
import database
import threading
import time
from models import SearchTask
from monitor import run_monitoring_cycle
import os

@st.cache_resource
def start_background_monitor():
    # Installa chromium per playwright (necessario per Streamlit Cloud)
    os.system("playwright install chromium")
    
    def loop():
        while True:
            try:
                run_monitoring_cycle()
                time.sleep(300)
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(60)
                
    t = threading.Thread(target=loop, daemon=True)
    t.start()
    return t

def main():
    st.set_page_config(page_title="Deal Monitor", page_icon="🛒")
    st.title("🛒 Marketplace Deal Monitor")
    
    # Initialize DB and Background Thread
    database.init_db()
    start_background_monitor()
    
    st.header("Aggiungi Nuova Ricerca")
    
    with st.form("new_search"):
        col1, col2 = st.columns(2)
        with col1:
            keyword = st.text_input("Parola Chiave (es. iPhone 13)")
            target_price = st.number_input("Prezzo Target (€)", min_value=1.0, value=500.0, step=10.0)
        with col2:
            tolerance = st.slider("Tolleranza / Variazione (%)", min_value=1, max_value=50, value=20, 
                                  help="Se il prezzo è 100€ e la tolleranza è 20%, cercherà annunci tra 80€ e 120€.")
            platforms = st.multiselect("Piattaforme", ["ebay", "subito", "vinted", "wallapop"], default=["ebay"])
            
        submit = st.form_submit_button("Aggiungi Ricerca")
        
        if submit:
            if not keyword:
                st.error("Inserisci una parola chiave valida.")
            elif not platforms:
                st.error("Seleziona almeno una piattaforma.")
            else:
                plat_str = ",".join(platforms)
                database.add_search(keyword, target_price, float(tolerance), plat_str)
                st.success(f"Ricerca per '{keyword}' aggiunta con successo!")
                
    st.header("Ricerche Attive")
    active_searches = database.get_active_searches()
    
    if not active_searches:
        st.info("Nessuna ricerca attiva.")
    else:
        for s in active_searches:
            st.write(f"**{s.keyword}** - Target: {s.target_price}€ ±{s.tolerance_percent}% sulle piattaforme: {s.platforms}")
            
    st.sidebar.title("Come funziona")
    st.sidebar.info(
        "1. Imposta le ricerche qui.\n"
        "2. Avvia in background lo script `monitor.py` per ricevere notifiche su Telegram.\n"
        "3. L'app eviterà di mandarti più volte la stessa notifica."
    )

if __name__ == "__main__":
    main()
