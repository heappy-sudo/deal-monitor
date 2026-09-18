from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class Listing(BaseModel):
    id: str
    title: str
    price: float
    url: str
    platform: str
    image_url: Optional[str] = None
    created_at: datetime = datetime.now()

class SearchTask(BaseModel):
    id: Optional[int] = None
    keyword: str
    target_price: float
    tolerance_percent: float  # e.g., 20 for 20%
    platforms: str  # comma separated: "ebay,subito,vinted"
    active: bool = True
    run_count: int = 0
    results_found: int = 0
    check_interval: int = 5
    last_checked: Optional[str] = None
