"""Conservative, rate-limited validation of official source landing pages.

This module intentionally audits one HTML landing page per source.  It never
opens document links, bypasses access controls, solves challenges, or crawls a
site.  Redirects are followed manually so every destination is DNS-checked
before a request is sent.
"""

from __future__ import annotations

import ipaddress
import re
import socket
import threading
import time
from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from email.message import Message
from types import TracebackType
from typing import Any, Protocol
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter


AUDIT_USER_AGENT = (
    "MonitorDeEditaisSourceAudit/1.0 "
    "(+https://github.com/Altaeir-13/Monitor-de-Editais)"
)
ROBOTS_USER_AGENT = "MonitorDeEditaisSourceAudit"
DOCUMENT_EXTENSIONS = {
    ".7z",
    ".csv",
    ".doc",
    ".docx",
    ".gz",
    ".ods",
    ".odt",
    ".pdf",
    ".rar",
    ".tar",
    ".xls",
    ".xlsx",
    ".xml",
    ".zip",
}
REDIRECT_STATUSES = {301, 302, 303, 307, 308}
RETRYABLE_STATUSES = {429, 500, 502, 503, 504}
AUDITABLE_SOURCE_STATUSES = {
    "verified",
    "partial",
    "temporarily_unavailable",
}
SKIPPED_SOURCE_STATUSES = {
    "manual_review",
    "unsupported",
    "inactive",
    "source_not_found",
}
NOTICE_TERMS = (
    "edital",
    "chamada",
    "concurso",
    "processo seletivo",
    "selecao",
    "seleção",
    "bolsa",
    "retificacao",
    "retificação",
    "resultado",
)
SPIDER_SELECTORS: dict[str, tuple[str, ...]] = {
    "generic": ("a[href]",),
    "wordpress": ("article", ".post", ".entry-title", ".wp-block-post"),
    "govbr": ("article", ".collection-item", ".tileItem", ".conteudo"),
    "sigaa": ("table", "form", ".listagem", "a[href*='processo_seletivo']"),
    "pagination": ("table", ".pagination", ".paginacao", "a[href*='page=']"),
}


class ResponseLike(Protocol):
    status_code: int
    headers: Mapping[str, Any]

    def iter_content(self, chunk_size: int) -> Iterable[bytes]: ...

    def close(self) -> None: ...


Requester = Callable[..., ResponseLike]
Resolver = Callable[..., list[tuple[Any, ...]]]


@dataclass(frozen=True)
class AuditPolicy:
    """Network limits for a controlled source audit."""

    timeout_seconds: float = 10.0
    max_retries: int = 2
    min_host_interval_seconds: float = 1.0
    max_connections_per_host: int = 2
    max_redirects: int = 5
    max_body_bytes: int = 1_000_000
    user_agent: str = AUDIT_USER_AGENT
    robots_user_agent: str = ROBOTS_USER_AGENT
    obey_robots: bool = True

    def __post_init__(self) -> None:
        if not 0 < self.timeout_seconds <= 30:
            raise ValueError("timeout_seconds must be between 0 and 30")
        if not 0 <= self.max_retries <= 2:
            raise ValueError("max_retries must be between 0 and 2")
        if self.min_host_interval_seconds < 0:
            raise ValueError("min_host_interval_seconds must not be negative")
        if not 1 <= self.max_connections_per_host <= 2:
            raise ValueError("max_connections_per_host must be 1 or 2")
        if not 0 <= self.max_redirects <= 5:
            raise ValueError("max_redirects must be between 0 and 5")
        if not 1_024 <= self.max_body_bytes <= 5_000_000:
            raise ValueError("max_body_bytes must be between 1024 and 5000000")
        if "MonitorDeEditais" not in self.user_agent or "http" not in self.user_agent:
            raise ValueError("user_agent must identify Monitor de Editais and its URL")


@dataclass
class AuditResult:
    source_id: str
    institution_code: str
    institution_name: str
    region: str
    state: str
    requested_url: str
    recommended_spider: str
    status: str
    checked_at: str
    http_status: int | None = None
    final_url: str | None = None
    redirect_chain: list[str] = field(default_factory=list)
    page_title: str | None = None
    content_type: str | None = None
    dns_addresses: list[str] = field(default_factory=list)
    html_valid: bool = False
    expected_elements_found: bool = False
    notice_terms_found: bool = False
    domain_matches_institution: bool | None = None
    attempts: int = 0
    error_code: str | None = None
    evidence: str = ""
    observations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SamplePlan:
    selections: tuple[dict[str, Any], ...]
    target_regions: tuple[str, ...]
    target_spiders: tuple[str, ...]
    represented_regions: tuple[str, ...]
    represented_spiders: tuple[str, ...]
    missing_regions: tuple[str, ...]
    missing_spiders: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_count": len(self.selections),
            "target_regions": list(self.target_regions),
            "target_spiders": list(self.target_spiders),
            "represented_regions": list(self.represented_regions),
            "represented_spiders": list(self.represented_spiders),
            "missing_regions": list(self.missing_regions),
            "missing_spiders": list(self.missing_spiders),
            "selections": [
                {
                    "official_code": item["institution"].get("official_code"),
                    "institution": item["institution"].get("official_name"),
                    "region": item["institution"].get("region"),
                    "state": item["institution"].get("state"),
                    "catalog_source_id": item["source"].get("catalog_source_id"),
                    "url": item["source"].get("url"),
                    "recommended_spider": item["source"].get("recommended_spider"),
                    "source_status": item["source"].get("status"),
                }
                for item in self.selections
            ],
        }


@dataclass
class _FetchedPage:
    status_code: int
    final_url: str
    redirect_chain: list[str]
    headers: dict[str, str]
    body: bytes
    dns_addresses: list[str]
    attempts: int


@dataclass(frozen=True)
class _RobotsRules:
    state: str
    parser: RobotFileParser | None
    evidence: str


class _AuditFailure(RuntimeError):
    def __init__(self, code: str, status: str, message: str, *, attempts: int = 0):
        super().__init__(message)
        self.code = code
        self.status = status
        self.attempts = attempts


class _HostLease:
    def __init__(
        self,
        semaphore: threading.BoundedSemaphore,
        timing_lock: threading.Lock,
        last_request: dict[str, float],
        host: str,
        interval: float,
        clock: Callable[[], float],
        sleeper: Callable[[float], None],
    ) -> None:
        self._semaphore = semaphore
        self._timing_lock = timing_lock
        self._last_request = last_request
        self._host = host
        self._interval = interval
        self._clock = clock
        self._sleeper = sleeper

    def __enter__(self) -> "_HostLease":
        self._semaphore.acquire()
        with self._timing_lock:
            now = self._clock()
            previous = self._last_request.get(self._host)
            if previous is not None:
                wait_for = previous + self._interval - now
                if wait_for > 0:
                    self._sleeper(wait_for)
                    now = self._clock()
            self._last_request[self._host] = now
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._semaphore.release()


class SafeSourceAuditor:
    """Audit source landing pages without expanding into linked documents."""

    def __init__(
        self,
        policy: AuditPolicy | None = None,
        *,
        requester: Requester | None = None,
        resolver: Resolver = socket.getaddrinfo,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.policy = policy or AuditPolicy()
        self._injected_requester = requester
        self._resolver = resolver
        self._clock = clock
        self._sleeper = sleeper
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._thread_local = threading.local()
        self._state_lock = threading.Lock()
        self._host_semaphores: dict[str, threading.BoundedSemaphore] = {}
        self._host_timing_locks: dict[str, threading.Lock] = {}
        self._last_request: dict[str, float] = {}
        self._dns_cache: dict[tuple[str, int], tuple[str, ...]] = {}
        self._robots_cache: dict[str, _RobotsRules] = {}

    def close(self) -> None:
        session = getattr(self._thread_local, "session", None)
        if session is not None:
            session.close()
            self._thread_local.session = None

    def _requester(self) -> Requester:
        if self._injected_requester is not None:
            return self._injected_requester
        session = getattr(self._thread_local, "session", None)
        if session is None:
            session = requests.Session()
            adapter = HTTPAdapter(
                pool_connections=10,
                pool_maxsize=self.policy.max_connections_per_host,
                max_retries=0,
                pool_block=True,
            )
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            self._thread_local.session = session
        return session.request

    def _lease(self, host: str) -> _HostLease:
        with self._state_lock:
            semaphore = self._host_semaphores.setdefault(
                host,
                threading.BoundedSemaphore(self.policy.max_connections_per_host),
            )
            timing_lock = self._host_timing_locks.setdefault(host, threading.Lock())
        return _HostLease(
            semaphore,
            timing_lock,
            self._last_request,
            host,
            self.policy.min_host_interval_seconds,
            self._clock,
            self._sleeper,
        )

    def _checked_at(self) -> str:
        return self._now().astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _normalized_target(url: str) -> tuple[str, str, int]:
        if not isinstance(url, str) or not url.strip():
            raise _AuditFailure("invalid_url", "manual_review", "URL ausente ou vazia")
        if len(url) > 2_048:
            raise _AuditFailure("invalid_url", "manual_review", "URL excede 2048 caracteres")
        parsed = urlsplit(url.strip())
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
            raise _AuditFailure("invalid_url", "manual_review", "somente URLs HTTP(S) são aceitas")
        if parsed.username is not None or parsed.password is not None:
            raise _AuditFailure("credentials_in_url", "manual_review", "URL contém credenciais")
        try:
            port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
        except ValueError as exc:
            raise _AuditFailure("invalid_port", "manual_review", str(exc)) from exc
        if port not in {80, 443}:
            raise _AuditFailure(
                "non_standard_port",
                "manual_review",
                f"porta {port} não é permitida na auditoria automática",
            )
        path = unquote(parsed.path).lower().rstrip("/")
        if any(path.endswith(extension) for extension in DOCUMENT_EXTENSIONS):
            raise _AuditFailure(
                "document_url",
                "unsupported",
                "a auditoria não abre documentos ou arquivos compactados",
            )
        hostname = parsed.hostname.encode("idna").decode("ascii").lower()
        netloc = hostname
        if parsed.port and parsed.port != (443 if parsed.scheme.lower() == "https" else 80):
            netloc = f"{hostname}:{parsed.port}"
        normalized = urlunsplit(
            (parsed.scheme.lower(), netloc, parsed.path or "/", parsed.query, "")
        )
        return normalized, hostname, port

    def _resolve_public(self, host: str, port: int) -> tuple[str, ...]:
        key = (host, port)
        with self._state_lock:
            cached = self._dns_cache.get(key)
        if cached is not None:
            return cached
        try:
            records = self._resolver(host, port, 0, socket.SOCK_STREAM)
        except OSError as exc:
            raise _AuditFailure(
                "dns_failure", "temporarily_unavailable", f"falha DNS para {host}: {exc}"
            ) from exc
        addresses = sorted(
            {
                str(record[4][0]).split("%", 1)[0]
                for record in records
                if len(record) > 4 and record[4]
            }
        )
        if not addresses:
            raise _AuditFailure(
                "dns_failure", "temporarily_unavailable", f"DNS sem endereços para {host}"
            )
        for address in addresses:
            try:
                parsed_address = ipaddress.ip_address(address)
            except ValueError as exc:
                raise _AuditFailure(
                    "invalid_dns_address", "manual_review", f"endereço DNS inválido: {address}"
                ) from exc
            if not parsed_address.is_global:
                raise _AuditFailure(
                    "non_public_destination",
                    "manual_review",
                    f"destino não público recusado: {address}",
                )
        result = tuple(addresses)
        with self._state_lock:
            self._dns_cache[key] = result
        return result

    def _request_once(self, url: str, host: str) -> tuple[int, dict[str, str], bytes]:
        with self._lease(host):
            response = self._requester()(
                "GET",
                url,
                headers={
                    "User-Agent": self.policy.user_agent,
                    "Accept": "text/html,text/plain;q=0.9,*/*;q=0.1",
                    "Accept-Encoding": "gzip, deflate",
                },
                timeout=self.policy.timeout_seconds,
                allow_redirects=False,
                stream=True,
            )
            try:
                status_code = int(response.status_code)
                headers = {str(key).lower(): str(value) for key, value in response.headers.items()}
                if status_code in REDIRECT_STATUSES:
                    return status_code, headers, b""
                content_length = headers.get("content-length")
                if content_length and content_length.isdigit():
                    if int(content_length) > self.policy.max_body_bytes:
                        raise _AuditFailure(
                            "body_too_large",
                            "unsupported",
                            f"Content-Length excede {self.policy.max_body_bytes} bytes",
                        )
                chunks: list[bytes] = []
                size = 0
                for chunk in response.iter_content(chunk_size=65_536):
                    if not chunk:
                        continue
                    size += len(chunk)
                    if size > self.policy.max_body_bytes:
                        raise _AuditFailure(
                            "body_too_large",
                            "unsupported",
                            f"corpo excede {self.policy.max_body_bytes} bytes",
                        )
                    chunks.append(chunk)
                return status_code, headers, b"".join(chunks)
            finally:
                response.close()

    def _request_with_retries(
        self, url: str, host: str
    ) -> tuple[int, dict[str, str], bytes, int]:
        attempts = 0
        last_exception: BaseException | None = None
        for attempt_index in range(self.policy.max_retries + 1):
            attempts += 1
            try:
                status, headers, body = self._request_once(url, host)
            except (requests.Timeout, requests.ConnectionError) as exc:
                last_exception = exc
                if attempt_index == self.policy.max_retries:
                    code = "timeout" if isinstance(exc, requests.Timeout) else "connection_failure"
                    raise _AuditFailure(
                        code,
                        "temporarily_unavailable",
                        f"{code} após {attempts} tentativa(s): {exc}",
                        attempts=attempts,
                    ) from exc
            else:
                if status not in RETRYABLE_STATUSES or attempt_index == self.policy.max_retries:
                    return status, headers, body, attempts
            self._sleeper(0.5 * (2**attempt_index))
        raise _AuditFailure(
            "connection_failure",
            "temporarily_unavailable",
            f"falha após {attempts} tentativa(s): {last_exception}",
            attempts=attempts,
        )

    def _fetch_url(self, requested_url: str) -> _FetchedPage:
        current_url = requested_url
        redirects: list[str] = []
        all_addresses: set[str] = set()
        total_attempts = 0
        for redirect_index in range(self.policy.max_redirects + 1):
            normalized, host, port = self._normalized_target(current_url)
            all_addresses.update(self._resolve_public(host, port))
            status, headers, body, attempts = self._request_with_retries(normalized, host)
            total_attempts += attempts
            if status not in REDIRECT_STATUSES:
                return _FetchedPage(
                    status_code=status,
                    final_url=normalized,
                    redirect_chain=redirects,
                    headers=headers,
                    body=body,
                    dns_addresses=sorted(all_addresses),
                    attempts=total_attempts,
                )
            location = headers.get("location", "").strip()
            if not location:
                raise _AuditFailure(
                    "redirect_without_location",
                    "manual_review",
                    f"HTTP {status} sem cabeçalho Location",
                    attempts=total_attempts,
                )
            if redirect_index == self.policy.max_redirects:
                raise _AuditFailure(
                    "too_many_redirects",
                    "manual_review",
                    f"mais de {self.policy.max_redirects} redirects",
                    attempts=total_attempts,
                )
            current_url = urljoin(normalized, location)
            redirects.append(current_url)
        raise AssertionError("redirect loop guard is unreachable")

    def _robots_rules(self, target_url: str) -> _RobotsRules:
        parsed = urlsplit(target_url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        with self._state_lock:
            cached = self._robots_cache.get(origin)
        if cached is not None:
            return cached
        try:
            fetched = self._fetch_url(f"{origin}/robots.txt")
        except _AuditFailure as exc:
            rules = _RobotsRules(
                "unavailable", None, f"robots.txt não pôde ser verificado: {exc}"
            )
        else:
            if fetched.status_code == 404:
                rules = _RobotsRules("allow", None, "robots.txt ausente (HTTP 404)")
            elif fetched.status_code in {401, 403}:
                rules = _RobotsRules(
                    "deny", None, f"robots.txt recusou acesso (HTTP {fetched.status_code})"
                )
            elif not 200 <= fetched.status_code < 300:
                rules = _RobotsRules(
                    "unavailable",
                    None,
                    f"robots.txt retornou HTTP {fetched.status_code}",
                )
            else:
                parser = RobotFileParser()
                parser.set_url(f"{origin}/robots.txt")
                text = fetched.body.decode("utf-8", errors="replace")
                parser.parse(text.splitlines())
                rules = _RobotsRules("parsed", parser, "robots.txt lido e aplicado")
        with self._state_lock:
            self._robots_cache[origin] = rules
        return rules

    def _check_robots(self, target_url: str) -> str:
        if not self.policy.obey_robots:
            return "verificação de robots.txt desabilitada explicitamente"
        rules = self._robots_rules(target_url)
        if rules.state == "unavailable":
            raise _AuditFailure("robots_unavailable", "temporarily_unavailable", rules.evidence)
        if rules.state == "deny":
            raise _AuditFailure("robots_disallowed", "manual_review", rules.evidence)
        if rules.parser is not None and not rules.parser.can_fetch(
            self.policy.robots_user_agent, target_url
        ):
            raise _AuditFailure(
                "robots_disallowed",
                "manual_review",
                "robots.txt não permite esta URL para o agente da auditoria",
            )
        return rules.evidence

    @staticmethod
    def _content_type(headers: Mapping[str, str]) -> str:
        raw = headers.get("content-type", "").strip()
        return raw.split(";", 1)[0].strip().lower()

    @staticmethod
    def _domain_family(hostname: str | None) -> str | None:
        if not hostname:
            return None
        labels = hostname.lower().strip(".").split(".")
        if len(labels) <= 2:
            return ".".join(labels)
        if labels[-1] == "br" and labels[-2] in {
            "com",
            "edu",
            "gov",
            "org",
            "net",
            "mil",
        }:
            return ".".join(labels[-3:])
        return ".".join(labels[-2:])

    @staticmethod
    def _title(soup: BeautifulSoup) -> str | None:
        if soup.title is None:
            return None
        title = re.sub(r"\s+", " ", soup.title.get_text(" ", strip=True)).strip()
        return title[:300] or None

    @staticmethod
    def _blocking_signal(soup: BeautifulSoup, headers: Mapping[str, str]) -> str | None:
        title = (SafeSourceAuditor._title(soup) or "").lower()
        text = soup.get_text(" ", strip=True).lower()[:50_000]
        if soup.select_one("input[type='password']") is not None:
            return "authentication_required"
        if any(token in title or token in text for token in ("captcha", "recaptcha", "hcaptcha")):
            return "captcha_detected"
        if headers.get("cf-mitigated", "").lower() == "challenge":
            return "cloudflare_challenge"
        if "just a moment" in title and (
            "cloudflare" in text or headers.get("cf-ray") is not None
        ):
            return "cloudflare_challenge"
        return None

    def _base_result(
        self,
        source: Mapping[str, Any],
        institution: Mapping[str, Any],
        *,
        status: str,
        error_code: str | None,
        evidence: str,
    ) -> AuditResult:
        return AuditResult(
            source_id=str(source.get("catalog_source_id") or ""),
            institution_code=str(institution.get("official_code") or ""),
            institution_name=str(institution.get("official_name") or ""),
            region=str(institution.get("region") or ""),
            state=str(institution.get("state") or ""),
            requested_url=str(source.get("url") or ""),
            recommended_spider=str(source.get("recommended_spider") or "generic"),
            status=status,
            checked_at=self._checked_at(),
            error_code=error_code,
            evidence=evidence,
        )

    def audit_source(
        self, source: Mapping[str, Any], institution: Mapping[str, Any]
    ) -> AuditResult:
        """Validate one source landing page and return structured evidence."""

        declared_status = str(source.get("status") or "manual_review")
        if declared_status in SKIPPED_SOURCE_STATUSES:
            return self._base_result(
                source,
                institution,
                status=declared_status,
                error_code=f"declared_{declared_status}",
                evidence=(
                    "fonte não acessada automaticamente porque o manifesto a classifica "
                    f"como {declared_status}"
                ),
            )
        if declared_status not in AUDITABLE_SOURCE_STATUSES:
            return self._base_result(
                source,
                institution,
                status="manual_review",
                error_code="unknown_source_status",
                evidence=f"status de origem desconhecido: {declared_status}",
            )

        requested_url = str(source.get("url") or "")
        try:
            normalized, requested_host, _ = self._normalized_target(requested_url)
            robots_evidence = self._check_robots(normalized)
            fetched = self._fetch_url(normalized)
        except _AuditFailure as exc:
            result = self._base_result(
                source,
                institution,
                status=exc.status,
                error_code=exc.code,
                evidence=str(exc),
            )
            result.attempts = exc.attempts
            return result

        content_type = self._content_type(fetched.headers)
        result = self._base_result(
            source,
            institution,
            status="partial",
            error_code=None,
            evidence=robots_evidence,
        )
        result.http_status = fetched.status_code
        result.final_url = fetched.final_url
        result.redirect_chain = fetched.redirect_chain
        result.content_type = content_type or None
        result.dns_addresses = fetched.dns_addresses
        result.attempts = fetched.attempts

        if fetched.status_code in {401, 403}:
            result.status = "manual_review"
            result.error_code = "authentication_or_access_blocked"
            result.evidence = f"acesso recusado sem tentativa de contorno (HTTP {fetched.status_code})"
            return result
        if fetched.status_code == 410:
            result.status = "inactive"
            result.error_code = "http_410"
            result.evidence = "a fonte respondeu HTTP 410 (Gone)"
            return result
        if fetched.status_code == 404:
            result.status = "manual_review"
            result.error_code = "http_404"
            result.evidence = "a fonte respondeu HTTP 404"
            return result
        if fetched.status_code in RETRYABLE_STATUSES:
            result.status = "temporarily_unavailable"
            result.error_code = f"http_{fetched.status_code}"
            result.evidence = (
                f"a fonte respondeu HTTP {fetched.status_code} após "
                f"{fetched.attempts} tentativa(s)"
            )
            return result
        if not 200 <= fetched.status_code < 300:
            result.status = "manual_review"
            result.error_code = f"unexpected_http_{fetched.status_code}"
            result.evidence = f"resposta HTTP inesperada: {fetched.status_code}"
            return result
        if content_type and content_type not in {
            "text/html",
            "application/xhtml+xml",
        }:
            result.status = "unsupported"
            result.error_code = "non_html_content"
            result.evidence = f"conteúdo não HTML recusado: {content_type}"
            return result

        soup = BeautifulSoup(fetched.body, "html.parser")
        result.page_title = self._title(soup)
        result.html_valid = soup.html is not None and soup.body is not None
        spider = result.recommended_spider.lower()
        selectors = SPIDER_SELECTORS.get(spider, SPIDER_SELECTORS["generic"])
        result.expected_elements_found = any(soup.select_one(selector) for selector in selectors)
        normalized_text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True).lower())
        result.notice_terms_found = any(term in normalized_text for term in NOTICE_TERMS)

        block = self._blocking_signal(soup, fetched.headers)
        if block:
            result.status = "manual_review"
            result.error_code = block
            result.evidence = f"bloqueio detectado ({block}); nenhum contorno foi tentado"
            return result

        final_host = urlsplit(fetched.final_url).hostname
        if fetched.redirect_chain and self._domain_family(requested_host) != self._domain_family(
            final_host
        ):
            result.status = "manual_review"
            result.error_code = "cross_domain_redirect"
            result.evidence = "redirect terminou em família de domínio diferente"
            return result

        official_site = institution.get("official_site_url")
        if isinstance(official_site, str) and official_site:
            official_host = urlsplit(official_site).hostname
            result.domain_matches_institution = self._domain_family(
                official_host
            ) == self._domain_family(final_host)
            if not result.domain_matches_institution:
                result.observations.append(
                    "domínio da fonte difere do domínio institucional; requer conferência da evidência oficial"
                )

        missing: list[str] = []
        if not result.html_valid:
            missing.append("estrutura html/body")
        if not result.page_title:
            missing.append("título")
        if not result.expected_elements_found:
            missing.append(f"elementos esperados para spider {spider}")
        if not result.notice_terms_found:
            missing.append("termos de edital/seleção")
        if missing:
            result.status = "partial"
            result.error_code = "structure_partial"
            result.evidence = "HTML acessível, mas faltam: " + ", ".join(missing)
        else:
            result.status = "verified"
            result.evidence = (
                "HTML, título, termos de editais e elementos esperados confirmados; "
                "compatibilidade do spider é provável, sem executar coleta"
            )
        return result


def _priority(value: Any) -> int:
    if isinstance(value, bool):
        return 99
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return 99


def _candidate_key(item: dict[str, Any], uncovered_spiders: set[str]) -> tuple[Any, ...]:
    source = item["source"]
    institution = item["institution"]
    status_rank = {"verified": 0, "partial": 1, "temporarily_unavailable": 2}
    spider = str(source.get("recommended_spider") or "generic")
    code = str(institution.get("official_code") or "")
    numeric_code = int(code) if code.isdigit() else 10**12
    return (
        0 if spider in uncovered_spiders else 1,
        status_rank.get(str(source.get("status")), 9),
        _priority(source.get("priority")),
        numeric_code,
        code,
        str(source.get("catalog_source_id") or ""),
    )


def select_controlled_sample(
    institutions: Iterable[Mapping[str, Any]],
    *,
    regions: Iterable[str] | None = None,
    max_samples: int = 10,
) -> SamplePlan:
    """Select a deterministic set covering every requested region and spider.

    At most ten landing pages are selected.  Sources requiring manual review,
    unsupported sources and inactive sources are deliberately not requested.
    """

    if not 1 <= max_samples <= 10:
        raise ValueError("max_samples must be between 1 and 10")
    institution_list = [dict(item) for item in institutions]
    requested_regions = (
        tuple(dict.fromkeys(str(region) for region in regions))
        if regions is not None
        else tuple(sorted({str(item.get("region")) for item in institution_list if item.get("region")}))
    )
    candidates: list[dict[str, Any]] = []
    for institution in institution_list:
        if not str(institution.get("eligibility_status", "included")).startswith("included"):
            continue
        if str(institution.get("region")) not in requested_regions:
            continue
        for raw_source in institution.get("sources") or []:
            source = dict(raw_source)
            if source.get("status") not in AUDITABLE_SOURCE_STATUSES or not source.get("url"):
                continue
            candidates.append({"institution": institution, "source": source})

    target_spiders = tuple(
        sorted({str(item["source"].get("recommended_spider") or "generic") for item in candidates})
    )
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    represented_spiders: set[str] = set()

    def add(item: dict[str, Any]) -> None:
        source_id = str(item["source"].get("catalog_source_id") or "")
        if source_id in selected_ids:
            return
        if len(selected) >= max_samples:
            return
        selected.append(item)
        selected_ids.add(source_id)
        represented_spiders.add(
            str(item["source"].get("recommended_spider") or "generic")
        )

    for region in requested_regions:
        options = [item for item in candidates if item["institution"].get("region") == region]
        if options:
            add(min(options, key=lambda item: _candidate_key(item, set(target_spiders) - represented_spiders)))

    for spider in target_spiders:
        if spider in represented_spiders:
            continue
        options = [
            item
            for item in candidates
            if str(item["source"].get("recommended_spider") or "generic") == spider
            and str(item["source"].get("catalog_source_id") or "") not in selected_ids
        ]
        if options:
            add(min(options, key=lambda item: _candidate_key(item, {spider})))

    represented_regions = tuple(
        sorted({str(item["institution"].get("region")) for item in selected})
    )
    represented_spiders_tuple = tuple(
        sorted({str(item["source"].get("recommended_spider") or "generic") for item in selected})
    )
    return SamplePlan(
        selections=tuple(selected),
        target_regions=requested_regions,
        target_spiders=target_spiders,
        represented_regions=represented_regions,
        represented_spiders=represented_spiders_tuple,
        missing_regions=tuple(sorted(set(requested_regions) - set(represented_regions))),
        missing_spiders=tuple(sorted(set(target_spiders) - set(represented_spiders_tuple))),
    )


__all__ = [
    "AUDIT_USER_AGENT",
    "AUDITABLE_SOURCE_STATUSES",
    "AuditPolicy",
    "AuditResult",
    "SafeSourceAuditor",
    "SamplePlan",
    "select_controlled_sample",
]
