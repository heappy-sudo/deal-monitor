from abc import ABC, abstractmethod
from typing import List
from models import Listing, SearchTask

class BaseScraper(ABC):
    @property
    @abstractmethod
    def platform_name(self) -> str:
        pass

    @abstractmethod
    def search(self, task: SearchTask) -> List[Listing]:
        """
        Esegue la ricerca per il task specificato e restituisce
        una lista di Listing che rientrano nel range di prezzo desiderato.
        """
        pass

    def is_price_valid(self, price: float, task: SearchTask) -> bool:
        """
        Verifica se il prezzo trovato rispetta la variazione (tolleranza) massima dal target.
        Es. se target_price è 100 e tolerance_percent è 20, 
        il prezzo deve essere tra 80 e 120 (o tipicamente inferiore a 100+20%).
        """
        variation = task.target_price * (task.tolerance_percent / 100)
        min_price = task.target_price - variation
        max_price = task.target_price + variation
        return min_price <= price <= max_price
