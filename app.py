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
    st.set_page_config(page_title="Deal Monitor", page_icon="🛒", layout="wide")
    
    # CSS Personalizzato
    st.markdown("""
    <style>
    .stApp header {background-color: transparent;}
    .main-title {font-size: 3rem; color: #00FFAA; text-align: center; margin-bottom: 0px;}
    .sub-title {text-align: center; color: #888; font-size: 1.2rem; margin-bottom: 30px;}
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<p class="main-title">🛒 Marketplace Deal Monitor</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Il tuo segugio personale per gli affari online</p>', unsafe_allow_html=True)
    
    database.init_db()
    start_background_monitor()
    
    active_searches = database.get_active_searches()
    
    # Metriche riassuntive
    col1, col2, col3 = st.columns(3)
    col1.metric("Ricerche Attive", len(active_searches))
    col2.metric("Piattaforme Supportate", 2) # eBay, Subito
    col3.metric("Stato Bot", "🟢 Online")
    
    st.divider()
    
    # Layout a schede (Tabs) per un'interfaccia più pulita
    tab1, tab2 = st.tabs(["📋 Le tue Ricerche", "➕ Aggiungi Nuova"])
    
    with tab1:
        st.subheader("Gestione Ricerche")
        if not active_searches:
            st.info("Non hai ancora nessuna ricerca attiva. Vai nella scheda 'Aggiungi Nuova'!")
        else:
            st.write("Modifica i valori direttamente nella tabella e spunta la casella per eliminare, poi clicca Salva.")
            table_data = [{"ID": s.id, "Parola Chiave": s.keyword, "Target (€)": s.target_price, "Tolleranza (%)": s.tolerance_percent, "Piattaforme": s.platforms, "Cicli": s.run_count, "Annunci Trovati": s.results_found, "Elimina 🗑️": False} for s in active_searches]
            
            edited_data = st.data_editor(
                table_data, 
                width="stretch", 
                hide_index=True,
                column_config={
                    "ID": None, # Nascondiamo l'ID perché non serve all'utente
                    "Target (€)": st.column_config.NumberColumn(min_value=1.0, step=1.0),
                    "Tolleranza (%)": st.column_config.NumberColumn(min_value=1, max_value=50, step=1),
                    "Cicli": st.column_config.NumberColumn("Cicli", disabled=True, help="Quante volte il bot ha eseguito la ricerca"),
                    "Annunci Trovati": st.column_config.NumberColumn("Annunci Trovati", disabled=True, help="Totale annunci inviati per questa ricerca")
                }
            )
            
            if st.button("💾 Salva Modifiche", type="primary"):
                for row in edited_data:
                    if row["Elimina 🗑️"]:
                        database.delete_search(row["ID"])
                    else:
                        database.update_search(row["ID"], row["Target (€)"], row["Tolleranza (%)"], row["Piattaforme"])
                st.success("Modifiche salvate con successo!")
                time.sleep(1)
                st.rerun()

    with tab2:
        st.subheader("Nuovo Incarico")
        with st.form("new_search"):
            c1, c2 = st.columns(2)
            with c1:
                keyword = st.text_input("Parola Chiave", placeholder="es. iPhone 15 Pro")
                target_price = st.number_input("Prezzo Target (€)", min_value=1.0, value=500.0, step=10.0)
            with c2:
                tolerance = st.slider("Tolleranza / Variazione (%)", 1, 50, 20)
                platforms = st.multiselect("Piattaforme", ["ebay", "subito", "vinted", "wallapop"], default=["ebay", "subito"])
                
            if st.form_submit_button("🚀 Avvia Ricerca", type="primary"):
                if keyword and platforms:
                    database.add_search(keyword, target_price, float(tolerance), ",".join(platforms))
                    st.success("Ricerca aggiunta! Il bot è già al lavoro in background.")
                    st.rerun()
                else:
                    st.error("Compila tutti i campi.")

if __name__ == "__main__":

    main()
