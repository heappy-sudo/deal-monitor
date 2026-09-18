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
                
    st.header("Gestione Ricerche Attive")
    active_searches = database.get_active_searches()
    
    if not active_searches:
        st.info("Nessuna ricerca attiva.")
    else:
        # Crea la tabella (Lista di dizionari)
        table_data = []
        for s in active_searches:
            table_data.append({
                "ID": s.id,
                "Parola Chiave": s.keyword,
                "Target (€)": s.target_price,
                "Tolleranza (%)": s.tolerance_percent,
                "Piattaforme": s.platforms
            })
        
        st.dataframe(table_data, use_container_width=True)
        
        # Sezione Azioni
        st.subheader("Azioni: Modifica o Elimina")
        action = st.radio("Scegli un'azione:", ["Nessuna", "Modifica Ricerca", "Elimina Ricerca"], horizontal=True)
        
        if action == "Elimina Ricerca":
            del_id = st.selectbox("Seleziona l'ID della ricerca da eliminare:", [s.id for s in active_searches])
            if st.button("🗑️ Conferma Eliminazione"):
                database.delete_search(del_id)
                st.success(f"Ricerca ID {del_id} eliminata!")
                st.rerun()
                
        elif action == "Modifica Ricerca":
            mod_id = st.selectbox("Seleziona l'ID della ricerca da modificare:", [s.id for s in active_searches])
            
            # Trova i dati attuali
            current_task = next((s for s in active_searches if s.id == mod_id), None)
            if current_task:
                with st.form("edit_form"):
                    st.write(f"Stai modificando: **{current_task.keyword}**")
                    new_target = st.number_input("Nuovo Prezzo Target (€)", value=float(current_task.target_price))
                    new_tol = st.slider("Nuova Tolleranza (%)", min_value=1, max_value=50, value=int(current_task.tolerance_percent))
                    
                    # Ricostruisci la lista delle piattaforme selezionate
                    current_plats = current_task.platforms.split(',')
                    new_plats = st.multiselect("Piattaforme", ["ebay", "subito", "vinted", "wallapop"], default=current_plats)
                    
                    if st.form_submit_button("💾 Salva Modifiche"):
                        if not new_plats:
                            st.error("Seleziona almeno una piattaforma.")
                        else:
                            database.update_search(mod_id, new_target, float(new_tol), ",".join(new_plats))
                            st.success(f"Ricerca ID {mod_id} aggiornata!")
                            st.rerun()

    st.sidebar.title("Come funziona")
    st.sidebar.info(
        "1. Imposta le ricerche qui.\n"
        "2. Avvia in background lo script `monitor.py` per ricevere notifiche su Telegram.\n"
        "3. L'app eviterà di mandarti più volte la stessa notifica."
    )

if __name__ == "__main__":
    main()
