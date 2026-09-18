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

def run_monitoring_cycle():
    print("Inizio ciclo di monitoraggio...")
    active_searches = database.get_active_searches()
    
    scrapers_map = {
        "ebay": EbayScraper(),
        "subito": SubitoScraper(),
        "vinted": VintedScraper(),
        "wallapop": WallapopScraper()
    }
    
    for task in active_searches:
        platforms = task.platforms.split(',')
        for plat in platforms:
            scraper = scrapers_map.get(plat.strip().lower())
            if not scraper:
                continue
                
            print(f"Cerco '{task.keyword}' su {plat}...")
            results = scraper.search(task)
            
            for listing in results:
                if not database.is_listing_seen(listing.id):
                    # Nuovo annuncio!
                    send_telegram_notification(listing, task)
                    database.mark_listing_seen(listing.id, listing.platform)
                    
    print("Ciclo completato. Attesa prima del prossimo controllo...")

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
