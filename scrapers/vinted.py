from typing import List
from models import Listing, SearchTask
from .base import BaseScraper
from playwright.sync_api import sync_playwright
import time

class VintedScraper(BaseScraper):
    @property
    def platform_name(self) -> str:
        return "vinted"

    def search(self, task: SearchTask) -> List[Listing]:
        listings = []
        url = f"https://www.vinted.it/vetrina?search_text={task.keyword.replace(' ', '+')}&order=newest_first"
        
        try:
            with sync_playwright() as p:
                # Modalità più furtiva per superare i blocchi base di Cloudflare
                browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={'width': 1920, 'height': 1080}
                )
                page = context.new_page()
                page.goto(url, wait_until='domcontentloaded', timeout=15000)
                time.sleep(2) # Piccola pausa per far renderizzare la pagina
                
                items = page.query_selector_all('div.feed-grid__item')
                
                for item in items:
                    url_elem = item.query_selector('a.new-item-box__overlay')
                    if not url_elem:
                        continue
                    
                    url_item = url_elem.get_attribute('href')
                    title = url_elem.get_attribute('title') or "Oggetto Vinted"
                    
                    price_elem = item.query_selector('div[data-testid*="price"]') or item.query_selector('h4')
                    if not price_elem:
                        continue
                        
                    price_text = price_elem.inner_text().replace('€', '').replace(',', '.').strip()
                    price_text = price_text.split(' ')[0] # Rimuove testi extra come " incl. prot."
                    
                    try:
                        price = float(price_text)
                    except ValueError:
                        continue
                        
                    if self.is_price_valid(price, task):
                        # L'ID in Vinted è spesso all'inizio dell'URL dell'oggetto
                        item_id = url_item.split('-')[0].split('/')[-1] if url_item else title
                        
                        listings.append(Listing(
                            id=f"vinted_{item_id}",
                            title=title,
                            price=price,
                            url=url_item,
                            platform=self.platform_name
                        ))
                browser.close()
        except Exception as e:
            print(f"Error scraping Vinted: {e}")
            
        return listings
