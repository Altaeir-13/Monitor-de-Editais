import requests
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseScraper(ABC):
    """
    Abstract base class for all scrapers/crawlers.
    Provides common functionality like fetching HTML content safely.
    """
    def __init__(self, source_url: str):
        self.source_url = source_url
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "MonitorDeEditaisBot/1.0 (+https://seusite.com)"
        })
        self.timeout = 15

    def fetch(self, url: str) -> str:
        """
        Fetches the HTML content of the given URL.
        Raises an exception if the request fails.
        """
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    @abstractmethod
    def extract(self, html: str) -> List[Dict[str, Any]]:
        """
        Parses the HTML and extracts a list of raw notices.
        Must be implemented by subclasses.
        Returns a list of dicts with at least 'title' and 'url'.
        """
        pass

    def run(self) -> List[Dict[str, Any]]:
        """
        Executes the scraping process: fetch -> extract.
        """
        html = self.fetch(self.source_url)
        return self.extract(html)
