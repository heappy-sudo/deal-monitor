import time
import requests
import database
from scrapers.ebay import EbayScraper
from scrapers.subito import SubitoScraper
from scrapers.vinted import VintedScraper
from scrapers.wallapop import WallapopScraper
from models import SearchTask, Listing

# CONFIGURA IL TUO BOT TELEGRAM QUI
TELEGRAM_BOT_TOKEN = "8724609100:AAEQfXpGFmPtn4gSdYPPgtkiqZiwyu4k5Lo"
TELEGRAM_CHAT_ID = "8728823654"

def send_telegram_notification(listing: Listing, task: SearchTask):
    if TELEGRAM_BOT_TOKEN == "IL_TUO_TOKEN_BOT" or TELEGRAM_CHAT_ID == "IL_TUO_CHAT_ID":
        print(f"[{listing.platform.upper()}] NUOVO DEAL TROVATO: {listing.title} a {listing.price}€ - {listing.url}")
        return

    text = (
        f"🚨 <b>Nuovo Deal per {task.keyword}!</b>\n"
        f"🏷 {listing.title}\n"
        f"💶 <b>{listing.price}€</b>\n"
        f"🌐 Piattaforma: {listing.platform.capitalize()}\n\n"
        f"🔗 <a href='{listing.url}'>Vedi Annuncio</a>"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Errore invio Telegram: {e}")

from datetime import datetime, timedelta

def run_monitoring_cycle(force: bool = False):
    print(f"Inizio ciclo di monitoraggio... (Forzato: {force})")
    active_searches = database.get_active_searches()
    
    scrapers_map = {
        "ebay": EbayScraper(),
        "subito": SubitoScraper(),
        "vinted": VintedScraper(),
        "wallapop": WallapopScraper()
    }
    
    now = datetime.now()
    
    for task in active_searches:
        if not force and task.last_checked:
            try:
                last_checked_dt = datetime.strptime(task.last_checked, "%Y-%m-%d %H:%M:%S")
                if now < last_checked_dt + timedelta(minutes=task.check_interval):
                    # Salta, non è ancora il momento di ricontrollare questa ricerca
                    continue
            except ValueError:
                pass # Formato data errato, eseguiamo comunque
                
        total_new_deals_for_task = 0
        platforms = task.platforms.split(',')
        
        for plat in platforms:
            scraper = scrapers_map.get(plat.strip().lower())
            if not scraper:
                continue
                
            print(f"\n⏳ [DEBUG] Avvio ricerca '{task.keyword}' su {plat.upper()}...")
            try:
                results = scraper.search(task)
                print(f"✅ [DEBUG {plat.upper()}] Estratti {len(results)} annunci validi (che rispettano il filtro di prezzo).")
                
                new_deals = 0
                for listing in results:
                    if not database.is_listing_seen(listing.id):
                        # Nuovo annuncio!
                        send_telegram_notification(listing, task)
                        database.mark_listing_seen(listing.id, listing.platform)
                        new_deals += 1
                        
                total_new_deals_for_task += new_deals
                print(f"📤 [DEBUG {plat.upper()}] Trovati {new_deals} nuovi deal non ancora visti. (Notifiche inviate)")
            except Exception as e:
                print(f"❌ [DEBUG {plat.upper()}] Errore durante lo scraping: {e}")
                
        # Alla fine delle piattaforme per questo task, aggiorniamo il contatore e l'orario
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        database.increment_search_stats(task.id, total_new_deals_for_task, now_str)
                    
    print("\n🏁 [DEBUG] Ciclo completato.\n" + "-"*40)

if __name__ == "__main__":
    database.init_db()
    print("Monitor avviato. Premi Ctrl+C per terminare.")
    while True:
        try:
            run_monitoring_cycle()
            time.sleep(300) # Attende 5 minuti tra un controllo e l'altro
        except KeyboardInterrupt:
            print("Monitor fermato.")
            break
        except Exception as e:
            print(f"Errore generico nel loop di monitoraggio: {e}")
            time.sleep(60)
