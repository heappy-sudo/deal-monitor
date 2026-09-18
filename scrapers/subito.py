from typing import List
from models import Listing, SearchTask
from .base import BaseScraper
from playwright.sync_api import sync_playwright

class SubitoScraper(BaseScraper):
    @property
    def platform_name(self) -> str:
        return "subito"

    def search(self, task: SearchTask) -> List[Listing]:
        listings = []
        url = f"https://www.subito.it/annunci-italia/vendita/usato/?q={task.keyword.replace(' ', '+')}&order=orddate"
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until='domcontentloaded')
                
                # Wait for listings to load
                page.wait_for_selector('div.items__item', timeout=5000)
                
                items = page.query_selector_all('div.items__item')
                for item in items:
                    title_elem = item.query_selector('h2')
                    if not title_elem:
                        continue
                    title = title_elem.inner_text()
                    
                    price_elem = item.query_selector('p[class*="price"]')
                    if not price_elem:
                        continue
                        
                    price_text = price_elem.inner_text().replace('€', '').replace('.', '').replace(',', '.').strip()
                    try:
                        price = float(price_text)
                    except ValueError:
                        continue
                        
                    if self.is_price_valid(price, task):
                        link_elem = item.query_selector('a')
                        url_item = link_elem.get_attribute('href') if link_elem else ""
                        item_id = url_item.split('/')[-1].split('.')[0] if url_item else title
                        
                        listings.append(Listing(
                            id=f"subito_{item_id}",
                            title=title,
                            price=price,
                            url=url_item,
                            platform=self.platform_name
                        ))
                
                browser.close()
        except Exception as e:
            print(f"Error scraping Subito: {e}")
            
        return listings
