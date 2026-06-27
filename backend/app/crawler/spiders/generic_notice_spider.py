import re
import unicodedata
from typing import Any, Dict, List, Optional
from urllib.parse import unquote, urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from app.crawler.base import BaseScraper


class GenericNoticeSpider(BaseScraper):
    """
    Generic HTML crawler for notice pages.

    It does not depend on project-specific selectors. Instead, it evaluates
    link text, href/URL text, and nearby container text to discover notices.
    """

    KEYWORDS = (
        "edital",
        "chamada",
        "selecao",
        "seletivo",
        "concurso",
        "pregao",
        "resultado",
        "retificac",
        "homologac",
        "convocac",
        "bolsa",
    )
    GENERIC_LINK_TEXTS = {
        "acesse",
        "acesse aqui",
        "aqui",
        "clique",
        "clique aqui",
        "download",
        "baixar",
        "pdf",
        "arquivo",
        "anexo",
        "visualizar",
        "ver",
        "abrir",
        "link",
    }
    GENERIC_NOTICE_TITLES = {
        "edital",
        "editais",
        "concursos",
        "concurso",
        "processos seletivos",
        "processo seletivo",
        "selecao",
        "selecoes",
        "licitacoes",
        "licitacao",
        "pregoes",
        "pregao",
        "resultados",
        "resultado",
        "chamadas",
        "chamada publica",
        "chamadas publicas",
        "licitacoes e contratos",
        "noticias",
    }
    IGNORED_SCHEMES = {"mailto", "tel", "javascript", "data"}
    IGNORED_HOSTS = {
        "creative-tim.com",
        "www.creative-tim.com",
        "facebook.com",
        "www.facebook.com",
        "instagram.com",
        "www.instagram.com",
        "twitter.com",
        "x.com",
        "youtube.com",
        "www.youtube.com",
    }
    HEADING_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6")
    CONTAINER_TAGS = ("article", "li", "tr", "section", "div", "td", "p")

    def extract(self, html: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        items: List[Dict[str, Any]] = []
        seen_urls = set()

        for link in soup.find_all("a", href=True):
            href = self._clean_text(link.get("href", ""))
            if self._should_ignore_href(href):
                continue

            absolute_url = urljoin(self.source_url, href)
            if not self._is_http_url(absolute_url) or self._should_ignore_absolute_url(absolute_url):
                continue

            link_text = self._clean_text(link.get_text(" ", strip=True))
            context_text = self._find_context_text(link)
            parsed_absolute_url = urlparse(absolute_url)
            url_path_text = unquote(" ".join([parsed_absolute_url.path, parsed_absolute_url.query]))
            link_searchable_text = " ".join(
                part for part in (link_text, href, url_path_text) if part
            )
            context_searchable_text = context_text
            normalized_link_text = self._normalize_for_match(link_text)
            generic_link_text = self._is_generic_link_text(normalized_link_text)

            if self._has_notice_keyword(link_searchable_text):
                searchable_text = " ".join([link_searchable_text, context_searchable_text])
            elif (
                (not link_text or generic_link_text)
                and len(context_searchable_text) <= 420
                and self._has_notice_keyword(context_searchable_text)
            ):
                searchable_text = " ".join([link_searchable_text, context_searchable_text])
            else:
                continue

            title = self._choose_title(link_text, context_text, absolute_url)
            if not title:
                continue
            if self._is_generic_listing_title(title, absolute_url):
                continue

            normalized_url_key = self._normalize_for_match(absolute_url)
            if normalized_url_key in seen_urls:
                continue
            seen_urls.add(normalized_url_key)

            description = context_text if context_text and context_text != title else None
            items.append(
                {
                    "title": title,
                    "url": absolute_url,
                    "notice_type": self._infer_notice_type(searchable_text),
                    "description": self._truncate(description, 600),
                }
            )

        return items

    def _should_ignore_href(self, href: str) -> bool:
        if not href or href == "#" or href.startswith("#"):
            return True

        parsed = urlparse(href)
        return parsed.scheme.lower() in self.IGNORED_SCHEMES

    def _is_http_url(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    def _should_ignore_absolute_url(self, url: str) -> bool:
        host = urlparse(url).netloc.lower()
        return host in self.IGNORED_HOSTS

    def _is_generic_link_text(self, normalized_link_text: str) -> bool:
        return normalized_link_text in self.GENERIC_LINK_TEXTS or bool(re.fullmatch(r"\d+", normalized_link_text))

    def _find_context_text(self, link: Tag) -> str:
        for ancestor in link.parents:
            if not isinstance(ancestor, Tag) or ancestor.name in {"body", "html"}:
                break

            if ancestor.name in self.CONTAINER_TAGS:
                heading = ancestor.find(self.HEADING_TAGS)
                if heading:
                    heading_text = self._clean_text(heading.get_text(" ", strip=True))
                    if heading_text:
                        return self._truncate(heading_text, 240) or ""

                container_text = self._clean_text(ancestor.get_text(" ", strip=True))
                link_text = self._clean_text(link.get_text(" ", strip=True))
                if container_text and container_text != link_text:
                    return self._truncate(container_text, 600) or ""

        return ""

    def _choose_title(self, link_text: str, context_text: str, absolute_url: str) -> str:
        normalized_link_text = self._normalize_for_match(link_text)
        if link_text and not self._is_generic_link_text(normalized_link_text):
            return self._truncate(link_text, 240) or ""

        if context_text:
            return self._truncate(context_text, 240) or ""

        path = unquote(urlparse(absolute_url).path.rsplit("/", 1)[-1])
        path = re.sub(r"[-_]+", " ", path)
        path = re.sub(r"\.[A-Za-z0-9]{2,5}$", "", path)
        return self._truncate(self._clean_text(path), 240) or ""

    def _infer_notice_type(self, text: str) -> str:
        normalized = self._normalize_for_match(text)
        if "retificac" in normalized:
            return "retificacao"
        if "homologac" in normalized:
            return "homologacao"
        if "convocac" in normalized:
            return "convocacao"
        if "resultado" in normalized:
            return "resultado"
        if "pregao" in normalized:
            return "pregao"
        if self._has_licitacao_keyword(normalized):
            return "licitacao"
        if "concurso" in normalized:
            return "concurso"
        if "bolsa" in normalized:
            return "bolsa"
        if "seletivo" in normalized or "selecao" in normalized:
            return "processo_seletivo"
        return "edital"

    def _is_generic_listing_title(self, title: str, absolute_url: str) -> bool:
        normalized_title = self._normalize_for_match(title)
        normalized_title = re.sub(r"^[\W_]+|[\W_]+$", "", normalized_title)
        if normalized_title not in self.GENERIC_NOTICE_TITLES:
            return False

        return not self._looks_like_document_url(absolute_url)

    def _looks_like_document_url(self, absolute_url: str) -> bool:
        path = urlparse(absolute_url).path.lower()
        return bool(re.search(r"\.(pdf|doc|docx|odt|xls|xlsx|csv|zip)$", path))

    def _has_notice_keyword(self, text: str) -> bool:
        normalized = self._normalize_for_match(text)
        return any(keyword in normalized for keyword in self.KEYWORDS) or self._has_licitacao_keyword(normalized)

    def _has_licitacao_keyword(self, normalized: str) -> bool:
        return bool(re.search(r"\blicita(?:cao|coes|r|do|dos|da|das|nte|ntes)?\b", normalized))

    def _normalize_for_match(self, text: Optional[str]) -> str:
        if not text:
            return ""
        without_accents = unicodedata.normalize("NFKD", text)
        without_accents = "".join(
            char for char in without_accents if not unicodedata.combining(char)
        )
        without_accents = without_accents.lower()
        without_accents = re.sub(r"\s+", " ", without_accents)
        return without_accents.strip()

    def _clean_text(self, text: Optional[str]) -> str:
        if not text:
            return ""
        if "<" in text and ">" in text:
            text = BeautifulSoup(text, "html.parser").get_text(" ", strip=True)
        text = self._fix_mojibake(text)
        return re.sub(r"\s+", " ", text).strip()

    def _fix_mojibake(self, text: str) -> str:
        for _ in range(2):
            if "Ã" not in text and "Â" not in text:
                break
            try:
                repaired = text.encode("latin-1").decode("utf-8")
            except UnicodeError:
                break
            if repaired == text:
                break
            text = repaired
        return text

    def _truncate(self, text: Optional[str], max_length: int) -> Optional[str]:
        if not text:
            return None
        if len(text) <= max_length:
            return text
        return text[: max_length - 3].rstrip() + "..."
