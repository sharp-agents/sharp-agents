"""Base scraper class for all data scrapers."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import logging


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"scraper.{name}")
    
    @abstractmethod
    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape data from the source."""
        pass
    
    @abstractmethod
    def parse_data(self, raw_data: Any) -> List[Dict[str, Any]]:
        """Parse raw data into structured format."""
        pass
    
    def validate_data(self, data: List[Dict[str, Any]]) -> bool:
        """Validate scraped data."""
        if not data:
            return False
        return True
