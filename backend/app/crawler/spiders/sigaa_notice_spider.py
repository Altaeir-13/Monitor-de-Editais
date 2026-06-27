import re
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup, Tag

from app.crawler.spiders.generic_notice_spider import GenericNoticeSpider


class SigaaNoticeSpider(GenericNoticeSpider):
    """
    Spider for public SIGAA/JSF process-selection listings.

    SIGAA detail pages are commonly POST-only through JSF callbacks. For those
    rows, `url` stays as the public listing page users can open in a browser,
    while `dedupe_url` receives a stable process id query parameter.
    """

    def extract(self, html: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        if self._is_login_page(soup):
            return []

        items = self._extract_sigaa_listing(soup)
        if items:
            return items

        if self._is_empty_listing(soup):
            return []

        return self._extract_generic_tables(soup)

    def _extract_sigaa_listing(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        table = soup.find("table", class_=lambda value: value and "listagem" in value.split())
        if not isinstance(table, Tag):
            return []

        items: List[Dict[str, Any]] = []
        rows = [row for row in table.find_all("tr") if isinstance(row, Tag)]
        for index, row in enumerate(rows):
            group_cell = row.find("td", class_=lambda value: value and "agrupador" in value.split())
            if not isinstance(group_cell, Tag):
                continue

            link = group_cell.find("a")
            if not isinstance(link, Tag):
                continue

            title = self._extract_title(link)
            if not title:
                continue

            process_id = self._extract_process_id(link)
            detail_row = self._next_data_row(rows, index + 1)
            details = self._extract_details(detail_row)
            description = self._description_for(title, details)
            dedupe_token = process_id or self._fallback_dedupe_token(title, details)
            searchable = " ".join([title, description or ""])

            items.append(
                {
                    "title": title,
                    "url": self._listing_url(),
                    "dedupe_url": self._dedupe_url(dedupe_token),
                    "notice_type": self._infer_notice_type(searchable),
                    "description": self._truncate(description, 600),
                }
            )

        return self._dedupe_items(items)

    def _extract_generic_tables(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for row in soup.find_all("tr"):
            if not isinstance(row, Tag):
                continue
            row_text = self._clean_text(row.get_text(" ", strip=True))
            if not self._has_notice_keyword(row_text):
                continue

            links = [link for link in row.find_all("a", href=True) if isinstance(link, Tag)]
            link = self._best_row_link(links)
            if not link:
                continue

            href = self._clean_text(link.get("href", ""))
            if self._should_ignore_href(href):
                continue

            absolute_url = urljoin(self.source_url, href)
            if not self._is_http_url(absolute_url) or self._should_ignore_absolute_url(absolute_url):
                continue

            link_text = self._clean_text(link.get_text(" ", strip=True))
            title = link_text if link_text and not self._is_generic_link_text(self._normalize_for_match(link_text)) else row_text
            if not title or self._is_generic_listing_title(title, absolute_url):
                continue

            items.append(
                {
                    "title": self._truncate(title, 240),
                    "url": absolute_url,
                    "notice_type": self._infer_notice_type(row_text),
                    "description": self._truncate(row_text if row_text != title else None, 600),
                }
            )

        return self._dedupe_items(items)

    def _best_row_link(self, links: List[Tag]) -> Optional[Tag]:
        for link in links:
            text = self._normalize_for_match(link.get_text(" ", strip=True))
            href = self._clean_text(link.get("href", ""))
            if href and href != "#" and (not text or self._is_generic_link_text(text)):
                return link
        for link in links:
            href = self._clean_text(link.get("href", ""))
            if href and href != "#":
                return link
        return None

    def _extract_title(self, link: Tag) -> str:
        title = self._clean_text(link.get_text(" ", strip=True))
        if not title:
            title = self._clean_text(link.get("title", ""))
        return re.sub(r"\s*\*+$", "", title).strip()

    def _extract_process_id(self, link: Tag) -> Optional[str]:
        onclick = str(link.get("onclick") or "")
        match = re.search(r"['\"]id['\"]\s*:\s*['\"]([^'\"]+)['\"]", onclick)
        if match:
            return match.group(1).strip()
        return None

    def _next_data_row(self, rows: List[Tag], start: int) -> Optional[Tag]:
        for row in rows[start:]:
            if row.find("td", class_=lambda value: value and "agrupador" in value.split()):
                return None
            cells = row.find_all("td")
            if not cells:
                continue
            cell_texts = [self._clean_text(cell.get_text(" ", strip=True)) for cell in cells]
            if any(text for text in cell_texts):
                return row
        return None

    def _extract_details(self, row: Optional[Tag]) -> Dict[str, Optional[str]]:
        details: Dict[str, Optional[str]] = {
            "curso": None,
            "vagas": None,
            "periodo": None,
            "situacao": None,
        }
        if not isinstance(row, Tag):
            return details

        cells = row.find_all("td")
        texts = [self._clean_text(cell.get_text(" ", strip=True)) for cell in cells]
        meaningful = [text for text in texts if text and text != "*"]
        if meaningful:
            details["curso"] = meaningful[0]
        if len(meaningful) >= 2 and re.fullmatch(r"\d+", meaningful[1]):
            details["vagas"] = meaningful[1]

        for cell, text in zip(cells, texts):
            if re.search(r"\d{2}/\d{2}/\d{4}", text):
                details["periodo"] = text
                class_names = cell.get("class") or []
                if isinstance(class_names, str):
                    class_names = class_names.split()
                details["situacao"] = "Fechado" if "fechado" in class_names else "Aberto"
                break

        return details

    def _description_for(self, title: str, details: Dict[str, Optional[str]]) -> str:
        parts = []
        if details.get("curso"):
            parts.append(f"Curso: {details['curso']}")
        if details.get("vagas"):
            parts.append(f"Vagas: {details['vagas']}")
        if details.get("periodo"):
            parts.append(f"Periodo de inscricoes: {details['periodo']}")
        if details.get("situacao"):
            parts.append(f"Situacao: {details['situacao']}")
        if parts:
            return "; ".join(parts)
        return title

    def _fallback_dedupe_token(self, title: str, details: Dict[str, Optional[str]]) -> str:
        raw = "|".join(
            part or ""
            for part in [title, details.get("curso"), details.get("periodo"), details.get("vagas")]
        )
        return self._normalize_for_match(raw).replace(" ", "-")[:160]

    def _listing_url(self) -> str:
        parsed = urlparse(self.source_url)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", parsed.query, ""))

    def _dedupe_url(self, token: str) -> str:
        parsed = urlparse(self._listing_url())
        pairs = parse_qsl(parsed.query, keep_blank_values=True)
        pairs = [(key, value) for key, value in pairs if key.lower() not in {"id", "processo_id"}]
        pairs.append(("id", token))
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", urlencode(pairs), ""))

    def _is_login_page(self, soup: BeautifulSoup) -> bool:
        text = self._normalize_for_match(soup.get_text(" ", strip=True))
        return "acesso ao sistema" in text and ("entrar com gov.br" in text or "formusuario" in text)

    def _is_empty_listing(self, soup: BeautifulSoup) -> bool:
        text = self._normalize_for_match(soup.get_text(" ", strip=True))
        return "nenhum processo seletivo encontra-se aberto" in text

    def _dedupe_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        deduped: List[Dict[str, Any]] = []
        seen = set()
        for item in items:
            key = item.get("dedupe_url") or item.get("url")
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped