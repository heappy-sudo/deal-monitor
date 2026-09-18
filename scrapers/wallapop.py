from typing import List
from models import Listing, SearchTask
from .base import BaseScraper
from playwright.sync_api import sync_playwright

class WallapopScraper(BaseScraper):
    @property
    def platform_name(self) -> str:
        return "wallapop"

    def search(self, task: SearchTask) -> List[Listing]:
        listings = []
        url = f"https://it.wallapop.com/app/search?keywords={task.keyword.replace(' ', '%20')}&filters_source=search_box"
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until='networkidle', timeout=15000)
                
                # Cerca i link che avvolgono le card dei prodotti
                items = page.query_selector_all('a.ItemCardList__item')
                
                for item in items:
                    title_elem = item.query_selector('.ItemCard__title') or item.query_selector('p[class*="title"]')
                    price_elem = item.query_selector('.ItemCard__price') or item.query_selector('span[class*="price"]')
                    
                    if not title_elem or not price_elem:
                        continue
                        
                    title = title_elem.inner_text().strip()
                    price_text = price_elem.inner_text().replace('€', '').replace('.', '').replace(',', '.').strip()
                    
                    try:
                        price = float(price_text)
                    except ValueError:
                        continue
                        
                    if self.is_price_valid(price, task):
                        url_item = item.get_attribute('href')
                        if url_item and not url_item.startswith('http'):
                            url_item = "https://it.wallapop.com" + url_item
                            
                        item_id = url_item.split('-')[-1] if url_item else title
                        
                        listings.append(Listing(
                            id=f"wallapop_{item_id}",
                            title=title,
                            price=price,
                            url=url_item or url,
                            platform=self.platform_name
                        ))
                browser.close()
        except Exception as e:
            print(f"Error scraping Wallapop: {e}")
            
        return listings
