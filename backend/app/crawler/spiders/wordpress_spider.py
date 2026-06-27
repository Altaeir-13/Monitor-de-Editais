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

    STRONG_NOTICE_KEYWORDS = (
        "edital",
        "chamada",
        "selecao",
        "seletivo",
        "concurso",
        "licitacao",
        "pregao",
        "bolsa",
    )
    BROAD_NOTICE_KEYWORDS = (
        "resultado",
        "retificacao",
        "homologacao",
        "convocacao",
    )
    SEARCH_TERMS = STRONG_NOTICE_KEYWORDS + BROAD_NOTICE_KEYWORDS

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
                if not self._is_relevant_rest_item(searchable):
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

    def _is_relevant_rest_item(self, text: str) -> bool:
        normalized = self._normalize_for_match(text)
        if any(keyword in normalized for keyword in self.STRONG_NOTICE_KEYWORDS):
            return True

        if not any(keyword in normalized for keyword in self.BROAD_NOTICE_KEYWORDS):
            return False

        return bool(
            "edital" in normalized
            or "processo seletivo" in normalized
            or "processos seletivos" in normalized
            or "chamada publica" in normalized
        )

    def _site_base_url(self) -> str:
        parsed = urlparse(self.source_url)
        return f"{parsed.scheme}://{parsed.netloc}/"