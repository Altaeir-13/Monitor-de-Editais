from typing import Any, Dict, List
from urllib.parse import urljoin, urlparse

import requests

from app.crawler.spiders.generic_notice_spider import GenericNoticeSpider


class WordPressNoticeSpider(GenericNoticeSpider):
    """
    Spider for WordPress-like institutional sites.

    It queries the public WP REST API when available and falls back to the
    generic HTML extractor for category/archive pages that disable the API.
    """

    SEARCH_TERMS = (
        "edital",
        "concurso",
        "selecao",
        "sele\u00e7\u00e3o",
        "bolsa",
        "licitacao",
        "licita\u00e7\u00e3o",
        "pregao",
        "preg\u00e3o",
        "resultado",
        "retificacao",
        "retifica\u00e7\u00e3o",
        "homologacao",
        "homologa\u00e7\u00e3o",
        "convocacao",
        "convoca\u00e7\u00e3o",
    )

    def run(self) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        seen = set()

        for item in self._extract_from_rest_api():
            key = item.get("url")
            if key and key not in seen:
                seen.add(key)
                items.append(item)

        try:
            for item in super().run():
                key = item.get("url")
                if key and key not in seen:
                    seen.add(key)
                    items.append(item)
        except Exception:
            if not items:
                raise

        return items

    def _extract_from_rest_api(self) -> List[Dict[str, Any]]:
        base = self._site_base_url()
        found: List[Dict[str, Any]] = []
        seen = set()

        endpoint = urljoin(base, "/wp-json/wp/v2/posts")
        api_timeout = min(self.timeout, 5)
        consecutive_failures = 0

        for term in self.SEARCH_TERMS:
            params = {
                "search": term,
                "per_page": 20,
                "_fields": "link,title,excerpt,date",
            }
            try:
                response = self.session.get(endpoint, params=params, timeout=api_timeout)
                if response.status_code >= 500:
                    consecutive_failures += 1
                    if consecutive_failures >= 2:
                        break
                    continue
                if response.status_code >= 400:
                    continue
                payload = response.json()
                consecutive_failures = 0
            except requests.RequestException:
                consecutive_failures += 1
                if consecutive_failures >= 2:
                    break
                continue
            except ValueError:
                continue

            if not isinstance(payload, list):
                continue

            for post in payload:
                link = post.get("link")
                title_data = post.get("title") or {}
                excerpt_data = post.get("excerpt") or {}
                title = self._clean_text(title_data.get("rendered", ""))
                description = self._clean_text(excerpt_data.get("rendered", ""))

                if not link or not title:
                    continue

                searchable = " ".join([title, link, description])
                if not self._has_notice_keyword(searchable):
                    continue

                absolute_url = urljoin(base, link)
                if absolute_url in seen:
                    continue
                seen.add(absolute_url)
                found.append(
                    {
                        "title": title,
                        "url": absolute_url,
                        "notice_type": self._infer_notice_type(searchable),
                        "description": self._truncate(description, 600),
                    }
                )

        return found

    def _site_base_url(self) -> str:
        parsed = urlparse(self.source_url)
        return f"{parsed.scheme}://{parsed.netloc}/"