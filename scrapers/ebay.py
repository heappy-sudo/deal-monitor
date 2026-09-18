import requests
from bs4 import BeautifulSoup
from typing import List
from models import Listing, SearchTask
from .base import BaseScraper
from fake_useragent import UserAgent

class EbayScraper(BaseScraper):
    @property
    def platform_name(self) -> str:
        return "ebay"

    def search(self, task: SearchTask) -> List[Listing]:
        listings = []
        ua = UserAgent()
        headers = {'User-Agent': ua.random}
        
        # Format the eBay search URL
        # We sort by 'Newly Listed' (_sop=10)
        url = f"https://www.ebay.it/sch/i.html?_nkw={task.keyword.replace(' ', '+')}&_sop=10"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            items = soup.find_all('div', class_='s-item__info')
            
            for item in items:
                title_elem = item.find('div', class_='s-item__title')
                if not title_elem or 'Altro da scoprire' in title_elem.text:
                    continue
                    
                title = title_elem.text.strip()
                link_elem = item.find('a', class_='s-item__link')
                url_item = link_elem['href'] if link_elem else ""
                
                # Prezzo
                price_elem = item.find('span', class_='s-item__price')
                if not price_elem:
                    continue
                
                # Cleanup price (e.g. "EUR 25,00" -> 25.0)
                price_text = price_elem.text.replace('EUR', '').replace('.', '').replace(',', '.').strip()
                # If there's a range (e.g. "25.0 a 30.0"), take the first
                if ' a ' in price_text:
                    price_text = price_text.split(' a ')[0]
                    
                try:
                    price = float(price_text)
                except ValueError:
                    continue
                    
                # Rimosso il filtro is_price_valid da qui, lo facciamo nel monitor!
                item_id = url_item.split('?')[0].split('/')[-1] if url_item else title
                
                listings.append(Listing(
                    id=f"ebay_{item_id}",
                    title=title,
                    price=price,
                    url=url_item,
                    platform=self.platform_name
                ))
                    
        except Exception as e:
            print(f"Error scraping eBay: {e}")
            
        return listings
