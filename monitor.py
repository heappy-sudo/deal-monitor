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
import os

LOG_FILE = "bot_logs.txt"

def bot_log(msg: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {msg}\n"
    print(line.strip())
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
        # Mantieni solo le ultime 200 righe per non appesantire
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) > 200:
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.writelines(lines[-100:])
    except Exception:
        pass

def run_monitoring_cycle(force: bool = False):
    bot_log(f"🏁 Inizio ciclo di monitoraggio... (Forzato: {force})")
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
                    continue
            except ValueError:
                pass
                
        total_new_deals_for_task = 0
        platforms = task.platforms.split(',')
        
        for plat in platforms:
            scraper = scrapers_map.get(plat.strip().lower())
            if not scraper:
                continue
                
            bot_log(f"⏳ Cerco '{task.keyword}' su {plat.upper()}...")
            try:
                raw_results = scraper.search(task)
                bot_log(f"🔍 [{plat.upper()}] Trovati {len(raw_results)} annunci in totale sulla pagina.")
                
                # Filtriamo i risultati in base al prezzo qui nel monitor
                valid_results = []
                for listing in raw_results:
                    if scraper.is_price_valid(listing.price, task):
                        valid_results.append(listing)
                
                bot_log(f"✅ [{plat.upper()}] Di questi, {len(valid_results)} rientrano nella tua tolleranza di prezzo.")
                
                new_deals = 0
                for listing in valid_results:
                    if not database.is_listing_seen(listing.id):
                        send_telegram_notification(listing, task)
                        database.mark_listing_seen(listing.id, listing.platform)
                        new_deals += 1
                        
                total_new_deals_for_task += new_deals
                if new_deals > 0:
                    bot_log(f"📤 [{plat.upper()}] Inviate {new_deals} nuove notifiche su Telegram.")
                else:
                    if len(valid_results) > 0:
                        bot_log(f"💤 [{plat.upper()}] I deal validi erano già stati inviati in passato.")
                    else:
                        bot_log(f"💤 [{plat.upper()}] Nessun deal da inviare.")
            except Exception as e:
                bot_log(f"❌ [{plat.upper()}] Errore durante lo scraping: {e}")
                
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        database.increment_search_stats(task.id, total_new_deals_for_task, now_str)
                    
    bot_log("💤 Ciclo completato.\n-----------------------")

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
