from typing import Any, Dict, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.crawler.spiders.generic_notice_spider import GenericNoticeSpider


class PaginatedNoticeSpider(GenericNoticeSpider):
    """
    Conservative spider for listing pages with simple pagination.

    It fetches the configured URL and follows explicit next-page links found in
    the returned HTML. This avoids blind URL permutations that are expensive on
    institutional portals and still supports ordinary paginated listings.
    """

    MAX_EXTRA_PAGES = 2

    def run(self) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        seen_items = set()
        seen_pages = {self.source_url}

        html = self.fetch(self.source_url)
        self._append_items(items, seen_items, self.extract(html))

        next_urls = self._extract_next_page_urls(html)
        for url in next_urls[: self.MAX_EXTRA_PAGES]:
            if url in seen_pages:
                continue
            seen_pages.add(url)
            try:
                page_html = self.fetch(url)
            except Exception:
                continue
            self._append_items(items, seen_items, self.extract(page_html))

        return items

    def _append_items(self, target: List[Dict[str, Any]], seen: set, items: List[Dict[str, Any]]) -> None:
        for item in items:
            key = item.get("url")
            if key and key not in seen:
                seen.add(key)
                target.append(item)

    def _extract_next_page_urls(self, html: str) -> List[str]:
        soup = BeautifulSoup(html, "html.parser")
        urls: List[str] = []

        for link in soup.find_all("a", href=True):
            rel = " ".join(link.get("rel", [])) if isinstance(link.get("rel"), list) else str(link.get("rel") or "")
            class_name = " ".join(link.get("class", [])) if isinstance(link.get("class"), list) else str(link.get("class") or "")
            text = self._normalize_for_match(link.get_text(" ", strip=True))
            title = self._normalize_for_match(link.get("title", ""))
            markers = " ".join([rel, class_name, text, title]).lower()

            if not any(token in markers for token in ("next", "proxima", "proximo", "seguinte")):
                continue

            absolute_url = urljoin(self.source_url, link["href"])
            if self._is_http_url(absolute_url) and absolute_url not in urls:
                urls.append(absolute_url)

        return urls
