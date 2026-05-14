from bs4 import BeautifulSoup
from typing import List, Dict, Any
from app.crawler.base import BaseScraper

class TestSpider(BaseScraper):
    """
    A test spider that looks for <a> tags within a specific container.
    This simulates extracting notice links from a standard HTML page.
    """
    def extract(self, html: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        items = []
        
        # Suppose the notices are in <div class="notice-item"> with an <a> tag
        containers = soup.find_all("div", class_="notice-item")
        
        for container in containers:
            a_tag = container.find("a")
            if a_tag and a_tag.get("href"):
                title = a_tag.get_text()
                url = a_tag.get("href")
                
                # Optionally, find a date or description if present
                date_tag = container.find("span", class_="date")
                pub_date = date_tag.get_text() if date_tag else None
                
                items.append({
                    "title": title,
                    "url": url,
                    "notice_type": "edital", # default type for test
                    "publication_date": pub_date
                })
        
        return items
