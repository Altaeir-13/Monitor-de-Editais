from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent

INITIAL_INSTITUTIONS = [
    "UFPI",
    "UFMA",
    "UFC",
    "UFRN",
    "UFPE",
    "UFBA",
    "IFPI",
    "IFCE",
    "IFRN",
    "UEMA",
    "UESPI",
    "UEPB",
    "UNEB",
    "UPE",
    "IFBA",
]

EXPECTED_NOTICE_TYPES = [
    "edital",
    "concurso",
    "processo_seletivo",
    "licitacao",
    "pregao",
    "resultado",
    "retificacao",
    "homologacao",
    "convocacao",
    "bolsa",
]

NOTICE_KEYWORDS = (
    "edital",
    "chamada",
    "selecao",
    "seletivo",
    "concurso",
    "licitac",
    "pregao",
    "resultado",
    "retificac",
    "homologac",
    "convocac",
    "bolsa",
)

GENERIC_LISTING_TITLES = {
    "edital",
    "editais",
    "concurso",
    "concursos",
    "processo seletivo",
    "processos seletivos",
    "selecao",
    "selecoes",
    "licitacao",
    "licitacoes",
    "pregao",
    "pregoes",
    "resultado",
    "resultados",
    "chamada publica",
    "chamadas publicas",
}

DOCUMENT_EXTENSIONS = (".pdf", ".doc", ".docx", ".odt", ".xls", ".xlsx", ".csv", ".zip")
USER_AGENT = "MonitorDeEditaisAudit/1.0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit Northeast monitored sources.")
    parser.add_argument(
        "--institutions",
        default=",".join(INITIAL_INSTITUTIONS),
        help="Comma-separated institution initials. Ignored when --all is used.",
    )
    parser.add_argument("--all", action="store_true", help="Audit all catalog institutions.")
    parser.add_argument("--skip-seed", action="store_true", help="Do not run the seed step.")
    parser.add_argument("--database-url", default=None, help="Override DATABASE_URL before importing the app.")
    parser.add_argument(
        "--output",
        default=str(REPO_ROOT / "docs" / "auditoria_fontes_nordeste.md"),
        help="Markdown report path.",
    )
    parser.add_argument("--sample-size", type=int, default=3, help="Sample links to validate per source.")
    parser.add_argument("--timeout", type=int, default=15, help="HTTP timeout in seconds.")
    parser.add_argument("--no-link-check", action="store_true", help="Skip sample URL opening checks.")
    return parser.parse_args()


def configure_env(database_url: Optional[str]) -> str:
    db_url = database_url or os.environ.get("DATABASE_URL")
    if not db_url:
        db_path = BACKEND_DIR / "audit_northeast.db"
        db_url = f"sqlite:///{db_path.as_posix()}"

    os.environ.setdefault("POSTGRES_USER", "audit")
    os.environ.setdefault("POSTGRES_PASSWORD", "audit")
    os.environ.setdefault("POSTGRES_DB", "monitor_editais_audit")
    os.environ["DATABASE_URL"] = db_url
    os.environ.setdefault("SECRET_KEY", "audit-secret-key-for-local-source-audit")
    os.environ.setdefault("ALGORITHM", "HS256")
    os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")

    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))
    return db_url


def normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""
    without_accents = unicodedata.normalize("NFKD", value)
    without_accents = "".join(char for char in without_accents if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", without_accents.lower()).strip()


def is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def is_document_url(value: str) -> bool:
    return urlparse(value).path.lower().endswith(DOCUMENT_EXTENSIONS)


def item_looks_like_notice(item: Dict[str, Any]) -> bool:
    title = str(item.get("title") or "").strip()
    url = str(item.get("url") or "").strip()
    description = str(item.get("description") or "")

    if not title or not is_http_url(url):
        return False

    normalized_title = normalize_text(title)
    if normalized_title in GENERIC_LISTING_TITLES and not is_document_url(url):
        return False

    searchable = normalize_text(" ".join([title, url, description]))
    return any(keyword in searchable for keyword in NOTICE_KEYWORDS)


def fix_mojibake(value: str) -> str:
    for _ in range(2):
        if "Ã" not in value and "Â" not in value:
            break
        try:
            repaired = value.encode("latin-1").decode("utf-8")
        except UnicodeError:
            break
        if repaired == value:
            break
        value = repaired
    return value


def truncate(value: Optional[str], max_len: int = 180) -> str:
    value = fix_mojibake(re.sub(r"\s+", " ", str(value or "")).strip())
    if len(value) <= max_len:
        return value
    return value[: max_len - 3].rstrip() + "..."


def escape_cell(value: Any) -> str:
    return truncate(str(value if value is not None else "")).replace("|", "\\|")



def curl_get_text(url: str, timeout: int) -> Optional[Dict[str, Any]]:
    curl_path = shutil.which("curl.exe") or shutil.which("curl")
    if not curl_path:
        return None

    marker = "\n__AUDIT_CURL_META__"
    command = [
        curl_path,
        "-L",
        "--silent",
        "--show-error",
        "--max-time",
        str(timeout),
        "-A",
        USER_AGENT,
        "-w",
        marker + "%{http_code}\t%{url_effective}\t%{content_type}",
        url,
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout + 5,
        check=False,
    )
    if completed.returncode != 0 or marker not in completed.stdout:
        return {"error": completed.stderr.strip() or f"curl exited with {completed.returncode}"}

    body, meta = completed.stdout.rsplit(marker, 1)
    status, final_url, content_type = (meta.split("\t") + ["", "", ""])[:3]
    try:
        status_code = int(status)
    except ValueError:
        status_code = None
    return {
        "text": body,
        "status_code": status_code,
        "final_url": final_url or url,
        "content_type": content_type,
    }


def curl_check_url(url: str, timeout: int) -> Optional[Dict[str, Any]]:
    curl_path = shutil.which("curl.exe") or shutil.which("curl")
    if not curl_path:
        return None

    command = [
        curl_path,
        "-L",
        "--silent",
        "--show-error",
        "--max-time",
        str(timeout),
        "-A",
        USER_AGENT,
        "-o",
        "NUL" if os.name == "nt" else "/dev/null",
        "-w",
        "%{http_code}",
        url,
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout + 5,
        check=False,
    )
    if completed.returncode != 0:
        return {"error": completed.stderr.strip() or f"curl exited with {completed.returncode}"}
    try:
        status_code = int(completed.stdout.strip()[-3:])
    except ValueError:
        status_code = None
    return {"status_code": status_code}


def decode_response_text(response) -> str:
    encoding = response.encoding
    if not encoding or encoding.lower() in {"iso-8859-1", "latin-1"}:
        encoding = response.apparent_encoding or "utf-8"
    return response.content.decode(encoding or "utf-8", errors="replace")


def make_session(timeout: int) -> requests.Session:
    from app.crawler.certificates import get_requests_verify_path

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    session.verify = get_requests_verify_path()
    session.request_timeout = timeout  # type: ignore[attr-defined]
    return session


def probe_source(session: requests.Session, url: str, timeout: int) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "opens": False,
        "status_code": None,
        "final_url": url,
        "content_type": "",
        "html_useful": False,
        "html_length": 0,
        "link_count": 0,
        "keyword_count": 0,
        "error": None,
        "curl_fallback": False,
    }
    try:
        try:
            response = session.get(url, timeout=timeout, allow_redirects=True)
            result["status_code"] = response.status_code
            result["final_url"] = response.url
            result["content_type"] = response.headers.get("content-type", "")
            result["opens"] = response.status_code < 400
            text = decode_response_text(response)
        except requests.exceptions.SSLError:
            curl_result = curl_get_text(url, timeout)
            if not curl_result or curl_result.get("error"):
                raise
            result["curl_fallback"] = True
            result["status_code"] = curl_result.get("status_code")
            result["final_url"] = curl_result.get("final_url", url)
            result["content_type"] = curl_result.get("content_type", "")
            result["opens"] = bool(result["status_code"] and result["status_code"] < 400)
            text = curl_result.get("text") or ""
        result["html_length"] = len(text)
        normalized = normalize_text(text[:200000])
        result["keyword_count"] = sum(1 for keyword in NOTICE_KEYWORDS if keyword in normalized)
        soup = BeautifulSoup(text, "html.parser")
        result["link_count"] = len(soup.find_all("a", href=True))
        is_html = "html" in result["content_type"].lower() or "<html" in text[:1000].lower()
        result["html_useful"] = bool(result["opens"] and is_html and result["link_count"] > 0)
    except Exception as exc:  # noqa: BLE001 - audit must keep going.
        result["error"] = str(exc)
    return result


def check_item_link(session: requests.Session, url: str, timeout: int) -> Dict[str, Any]:
    result = {"url": url, "opens": False, "status_code": None, "error": None, "curl_fallback": False}
    try:
        try:
            response = session.get(
                url,
                timeout=timeout,
                allow_redirects=True,
                stream=True,
                headers={"Range": "bytes=0-2048", "User-Agent": USER_AGENT},
            )
            result["status_code"] = response.status_code
            result["opens"] = response.status_code < 400
            response.close()
        except requests.exceptions.SSLError:
            curl_result = curl_check_url(url, timeout)
            if not curl_result or curl_result.get("error"):
                raise
            result["curl_fallback"] = True
            result["status_code"] = curl_result.get("status_code")
            result["opens"] = bool(result["status_code"] and result["status_code"] < 400)
    except Exception as exc:  # noqa: BLE001 - audit must keep going.
        result["error"] = str(exc)
    return result


def choose_status(probe: Dict[str, Any], crawl: Dict[str, Any], valid_count: int, link_checks: List[Dict[str, Any]]) -> str:
    status_code = probe.get("status_code")
    error_text = " ".join(str(value or "") for value in [probe.get("error"), crawl.get("error_message")]).lower()

    if crawl.get("failed"):
        if status_code in {401, 403} or "forbidden" in error_text or "unauthorized" in error_text:
            return "bloqueio_acesso"
        if status_code in {404, 410} or "name or service not known" in error_text or "no address associated" in error_text:
            return "url_invalida"
        if "javascript" in error_text:
            return "exige_javascript"
        return "url_invalida" if not probe.get("opens") else "funcional_parcial"

    if not probe.get("opens"):
        if valid_count > 0:
            return "funcional_parcial"
        if status_code in {401, 403}:
            return "bloqueio_acesso"
        return "url_invalida"

    if not probe.get("html_useful"):
        return "exige_javascript" if probe.get("html_length", 0) > 0 else "url_invalida"

    if crawl.get("items_found", 0) == 0:
        if probe.get("keyword_count", 0) > 0:
            return "exige_spider_especifico"
        return "sem_editais_encontrados"

    if valid_count == 0:
        return "funcional_parcial"

    checked = len(link_checks)
    opened = sum(1 for item in link_checks if item.get("opens"))
    if checked and opened < checked:
        return "funcional_parcial"

    if valid_count < crawl.get("items_found", 0):
        return "funcional_parcial"

    return "funcional"


def summarize_action(status: str) -> str:
    if status == "funcional":
        return "Mantida; crawler recuperou editais validos."
    if status == "funcional_parcial":
        return "Mantida parcialmente; requer revisao fina de fonte/spider."
    if status == "sem_editais_encontrados":
        return "Mantida por ora; sem edital detectado na execucao."
    if status == "exige_spider_especifico":
        return "Requer spider especifico ou seletor dedicado."
    if status == "exige_javascript":
        return "Requer alternativa oficial sem JavaScript ou spider com renderizacao."
    if status == "bloqueio_acesso":
        return "Requer avaliacao de bloqueio/headers ou fonte alternativa oficial."
    if status == "url_invalida":
        return "Requer substituicao por URL oficial funcional."
    return "Auditada."


def load_catalog_counts() -> Dict[str, int]:
    from app.services.northeast_seed import load_northeast_catalog

    catalog = load_northeast_catalog()
    return {
        "institutions": len(catalog),
        "sources": sum(len(item.get("sources", [])) for item in catalog),
    }


def selected_initials(all_sources: bool, institutions_arg: str) -> List[str]:
    if all_sources:
        from app.services.northeast_seed import load_northeast_catalog

        return [item["initials"].strip().upper() for item in load_northeast_catalog()]
    return [item.strip().upper() for item in institutions_arg.split(",") if item.strip()]


def get_sources(db, initials: Iterable[str]):
    from app.models.institution import Institution
    from app.models.monitored_source import MonitoredSource

    return (
        db.query(MonitoredSource)
        .join(Institution)
        .filter(Institution.initials.in_(list(initials)))
        .filter(Institution.is_active == True, MonitoredSource.is_active == True)  # noqa: E712
        .order_by(Institution.initials.asc(), MonitoredSource.name.asc())
        .all()
    )


def audit_once(db, sources, args: argparse.Namespace, run_label: str) -> Dict[str, Any]:
    from app.crawler.runner import run_source_crawler
    from app.crawler.spider_factory import get_spider_for_source

    session = make_session(args.timeout)
    source_results = []
    summary = {
        "sources_checked": len(sources),
        "items_found": 0,
        "new_items": 0,
        "failed_sources": 0,
    }

    for index, source in enumerate(sources, start=1):
        institution = source.institution
        spider_name = get_spider_for_source(source).__class__.__name__
        print(f"[{run_label}] {index}/{len(sources)} {institution.initials} - {source.name}", flush=True)

        probe = probe_source(session, source.url, args.timeout)
        crawl = run_source_crawler(db, source)
        raw_items = crawl.get("items", [])
        valid_items = [item for item in raw_items if item_looks_like_notice(item)]

        link_checks: List[Dict[str, Any]] = []
        if not args.no_link_check:
            for item in valid_items[: max(args.sample_size, 0)]:
                link_checks.append(check_item_link(session, item.get("url", ""), args.timeout))

        status = choose_status(probe, crawl, len(valid_items), link_checks)
        samples = [
            {
                "title": truncate(item.get("title"), 220),
                "url": item.get("url"),
                "notice_type": item.get("notice_type", "edital"),
            }
            for item in valid_items[: max(args.sample_size, 0)]
        ]

        result = {
            "institution": institution.initials,
            "institution_name": institution.name,
            "source_id": source.id,
            "source_name": source.name,
            "url": source.url,
            "source_type": source.source_type,
            "spider": spider_name,
            "status": status,
            "items_found": crawl.get("items_found", 0),
            "new_items": crawl.get("new_items", 0),
            "valid_items": len(valid_items),
            "probe": probe,
            "link_checks": link_checks,
            "samples": samples,
            "error": crawl.get("error_message") or probe.get("error"),
            "action": summarize_action(status),
        }
        source_results.append(result)

        summary["items_found"] += crawl.get("items_found", 0)
        summary["new_items"] += crawl.get("new_items", 0)
        if crawl.get("failed"):
            summary["failed_sources"] += 1

    return {"summary": summary, "sources": source_results}


def filter_results(db, initials: Iterable[str]) -> Dict[str, Dict[str, Any]]:
    from app.models.institution import Institution
    from app.models.notice import Notice
    from app.services.notice import get_notices

    results: Dict[str, Dict[str, Any]] = {}
    initials = list(initials)
    for notice_type in EXPECTED_NOTICE_TYPES:
        query = (
            db.query(Notice)
            .join(Institution)
            .filter(Notice.is_active == True)  # noqa: E712
            .filter(Institution.initials.in_(initials))
            .filter(Notice.notice_type == notice_type)
            .order_by(Notice.detected_at.desc())
        )
        examples = query.limit(3).all()
        public_samples = get_notices(db=db, notice_type=notice_type, skip=0, limit=5)
        results[notice_type] = {
            "count": query.count(),
            "public_sample_count": len(public_samples),
            "examples": [truncate(notice.title, 140) for notice in examples],
        }
    return results


def notice_type_counts(db, initials: Iterable[str]) -> Counter:
    from app.models.institution import Institution
    from app.models.notice import Notice

    rows = (
        db.query(Notice.notice_type)
        .join(Institution)
        .filter(Notice.is_active == True)  # noqa: E712
        .filter(Institution.initials.in_(list(initials)))
        .all()
    )
    return Counter(row[0] for row in rows)


def active_notice_count(db, initials: Iterable[str]) -> int:
    from app.models.institution import Institution
    from app.models.notice import Notice

    return (
        db.query(Notice)
        .join(Institution)
        .filter(Notice.is_active == True)  # noqa: E712
        .filter(Institution.initials.in_(list(initials)))
        .count()
    )


def institutions_with_notices(db, initials: Iterable[str]) -> List[str]:
    from app.models.institution import Institution
    from app.models.notice import Notice

    rows = (
        db.query(Institution.initials)
        .join(Notice, Notice.institution_id == Institution.id)
        .filter(Notice.is_active == True)  # noqa: E712
        .filter(Institution.initials.in_(list(initials)))
        .distinct()
        .order_by(Institution.initials.asc())
        .all()
    )
    return [row[0] for row in rows]


def scoped_notice_ids(db, initials: Iterable[str]) -> set[int]:
    from app.models.institution import Institution
    from app.models.notice import Notice

    rows = (
        db.query(Notice.id)
        .join(Institution)
        .filter(Notice.is_active == True)  # noqa: E712
        .filter(Institution.initials.in_(list(initials)))
        .all()
    )
    return {row[0] for row in rows}


def notice_samples(db, initials: Iterable[str], limit: int = 12) -> List[Dict[str, Any]]:
    from app.models.institution import Institution
    from app.models.notice import Notice

    rows = (
        db.query(Notice, Institution.initials)
        .join(Institution)
        .filter(Notice.is_active == True)  # noqa: E712
        .filter(Institution.initials.in_(list(initials)))
        .order_by(Notice.detected_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": notice.id,
            "institution": initials,
            "notice_type": notice.notice_type,
            "title": truncate(notice.title, 180),
            "url": notice.url,
        }
        for notice, initials in rows
    ]


def describe_notice_ids(db, notice_ids: Iterable[int]) -> List[Dict[str, Any]]:
    from app.models.institution import Institution
    from app.models.notice import Notice

    ids = list(notice_ids)
    if not ids:
        return []

    rows = (
        db.query(Notice, Institution.initials)
        .join(Institution)
        .filter(Notice.id.in_(ids))
        .order_by(Notice.id.asc())
        .all()
    )
    return [
        {
            "id": notice.id,
            "institution": initials,
            "notice_type": notice.notice_type,
            "title": truncate(notice.title, 180),
            "url": notice.url,
            "normalized_title": notice.normalized_title,
            "normalized_url": notice.normalized_url,
        }
        for notice, initials in rows
    ]


def duplicate_investigation(db, new_notice_ids: Iterable[int]) -> List[Dict[str, Any]]:
    from app.models.notice import Notice

    ids = list(new_notice_ids)
    if not ids:
        return []

    findings = []
    new_notices = db.query(Notice).filter(Notice.id.in_(ids)).all()
    for notice in new_notices:
        same_url = (
            db.query(Notice)
            .filter(Notice.id != notice.id)
            .filter(Notice.institution_id == notice.institution_id)
            .filter(Notice.normalized_url == notice.normalized_url)
            .limit(5)
            .all()
        )
        same_title = (
            db.query(Notice)
            .filter(Notice.id != notice.id)
            .filter(Notice.institution_id == notice.institution_id)
            .filter(Notice.normalized_title == notice.normalized_title)
            .limit(5)
            .all()
        )
        if same_url or same_title:
            findings.append(
                {
                    "new_id": notice.id,
                    "title": truncate(notice.title, 180),
                    "url": notice.url,
                    "same_url_ids": [item.id for item in same_url],
                    "same_title_ids": [item.id for item in same_title],
                }
            )
    return findings


def render_report(
    output_path: Path,
    db_url: str,
    initials: List[str],
    catalog_counts: Dict[str, int],
    seed_first: Optional[Dict[str, int]],
    seed_second: Optional[Dict[str, int]],
    first_run: Dict[str, Any],
    second_run: Dict[str, Any],
    filters: Dict[str, Dict[str, Any]],
    type_counts: Counter,
    notices_total: int,
    institutions_with_notice: List[str],
    saved_examples: List[Dict[str, Any]],
    second_new_notices: List[Dict[str, Any]],
    duplicate_findings: List[Dict[str, Any]],
) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    status_counts = Counter(item["status"] for item in first_run["sources"])
    functional = status_counts.get("funcional", 0)
    partial = status_counts.get("funcional_parcial", 0)
    failed = len(first_run["sources"]) - functional - partial

    lines: List[str] = []
    lines.append("# Auditoria de fontes do Nordeste")
    lines.append("")
    lines.append(f"Gerado em: {now}")
    lines.append(f"Banco usado: `{db_url}`")
    lines.append("")
    lines.append("## Escopo")
    lines.append("")
    lines.append(f"Instituicoes auditadas: {', '.join(initials)}")
    lines.append(f"Catalogo carregado: {catalog_counts['institutions']} instituicoes, {catalog_counts['sources']} fontes.")
    lines.append(f"Fontes testadas neste relatorio: {len(first_run['sources'])}")
    lines.append("")
    lines.append("## Seed")
    lines.append("")
    if seed_first is None:
        lines.append("Seed nao executado (`--skip-seed`).")
    else:
        lines.append(f"Primeira execucao: `{json.dumps(seed_first, ensure_ascii=False)}`")
        lines.append(f"Segunda execucao: `{json.dumps(seed_second, ensure_ascii=False)}`")
        duplicated = bool(seed_second and (seed_second.get("institutions_created") or seed_second.get("sources_created")))
        lines.append(f"Idempotencia: {'falhou' if duplicated else 'ok, sem novas instituicoes/fontes na segunda execucao'}.")
    lines.append("")
    lines.append("## Resumo do crawler")
    lines.append("")
    lines.append(f"Primeira execucao: `{json.dumps(first_run['summary'], ensure_ascii=False)}`")
    lines.append(f"Segunda execucao (duplicidade): `{json.dumps(second_run['summary'], ensure_ascii=False)}`")
    lines.append(f"Instituicoes com pelo menos 1 edital salvo: {len(institutions_with_notice)} ({', '.join(institutions_with_notice) if institutions_with_notice else 'nenhuma'})")
    lines.append(f"Editais ativos recuperados para o escopo: {notices_total}")
    lines.append(f"Fontes funcionais: {functional}")
    lines.append(f"Fontes funcionais parciais: {partial}")
    lines.append(f"Fontes falhas/sem captura util: {failed}")
    lines.append("")
    lines.append("Tipos encontrados: " + (", ".join(f"{key}={value}" for key, value in sorted(type_counts.items())) or "nenhum"))
    lines.append("")
    lines.append("## Amostras de editais salvos")
    lines.append("")
    if saved_examples:
        for sample in saved_examples:
            lines.append(f"- `{sample['notice_type']}` {sample['institution']} - {escape_cell(sample['title'])} - {sample['url']}")
    else:
        lines.append("- Nenhum edital salvo no escopo.")
    lines.append("")
    lines.append("## Verificacao de duplicidade")
    lines.append("")
    lines.append(f"Novos itens na segunda execucao: {second_run['summary']['new_items']}")
    if not second_new_notices:
        lines.append("A segunda execucao nao criou novos registros no escopo; nao houve duplicidade indevida detectada.")
    else:
        lines.append("Novos registros criados na segunda execucao:")
        for notice in second_new_notices:
            lines.append(f"- #{notice['id']} `{notice['notice_type']}` {notice['institution']} - {escape_cell(notice['title'])} - {notice['url']}")
        if duplicate_findings:
            lines.append("Possiveis duplicatas por `normalized_url` ou `normalized_title`:")
            for finding in duplicate_findings:
                lines.append(
                    f"- Novo #{finding['new_id']} - {escape_cell(finding['title'])} | "
                    f"same_url_ids={finding['same_url_ids']} | same_title_ids={finding['same_title_ids']}"
                )
        else:
            lines.append("Nenhuma duplicata exata por `institution_id + normalized_url` ou `institution_id + normalized_title` foi detectada entre os novos registros.")
    lines.append("")
    lines.append("## Filtros por tipo")
    lines.append("")
    lines.append("| notice_type | Registros no escopo | Amostra via listagem publica | Exemplos |")
    lines.append("| --- | ---: | ---: | --- |")
    for notice_type in EXPECTED_NOTICE_TYPES:
        item = filters[notice_type]
        examples = "; ".join(item["examples"]) if item["examples"] else "-"
        lines.append(
            f"| `{notice_type}` | {item['count']} | {item['public_sample_count']} | {escape_cell(examples)} |"
        )
    lines.append("")
    lines.append("## Fontes auditadas")
    lines.append("")

    for item in first_run["sources"]:
        probe = item["probe"]
        link_ok = sum(1 for check in item["link_checks"] if check.get("opens"))
        link_total = len(item["link_checks"])
        lines.append(f"### {item['institution']} - {item['source_name']}")
        lines.append("")
        lines.append(f"- Instituicao: {item['institution_name']} ({item['institution']})")
        lines.append(f"- Fonte: {item['source_name']}")
        lines.append(f"- URL: {item['url']}")
        lines.append(f"- Tipo configurado: `{item['source_type']}`")
        lines.append(f"- Spider usado: `{item['spider']}`")
        lines.append(f"- Status: `{item['status']}`")
        lines.append(f"- Pagina abre: {probe.get('opens')} (HTTP {probe.get('status_code')}, final `{probe.get('final_url')}`)")
        lines.append(f"- Fallback curl por TLS/OpenSSL: {probe.get('curl_fallback', False)}")
        lines.append(f"- HTML util: {probe.get('html_useful')} ({probe.get('html_length')} bytes, {probe.get('link_count')} links)")
        lines.append(f"- Itens encontrados: {item['items_found']}")
        lines.append(f"- Novos itens salvos: {item['new_items']}")
        lines.append(f"- Editais validos: {item['valid_items']}")
        lines.append(f"- Links de amostra que abriram: {link_ok}/{link_total}")
        lines.append(f"- Problemas: {escape_cell(item['error']) if item['error'] else '-'}")
        lines.append(f"- Acao tomada: {item['action']}")
        lines.append("- Observacao:")
        if item["samples"]:
            for sample in item["samples"]:
                lines.append(
                    f"  - `{sample.get('notice_type')}` {escape_cell(sample.get('title'))} - {sample.get('url')}"
                )
        else:
            lines.append("  - Sem amostra valida capturada.")
        lines.append("")

    lines.append("## Limitacoes e proximos passos")
    lines.append("")
    lines.append("- Fontes com `exige_spider_especifico` devem ser analisadas no HTML para seletor dedicado ou fonte oficial alternativa.")
    lines.append("- Fontes com `url_invalida` ou `bloqueio_acesso` precisam de confirmacao manual antes de troca no catalogo.")
    lines.append("- A validacao de links abre somente amostras por fonte para evitar baixar grandes PDFs em massa.")
    lines.append("- Algumas fontes exigiram fallback via `curl` por falha de cadeia TLS no OpenSSL/requests; `curl` foi usado com verificacao TLS padrao, sem `--insecure`.")
    lines.append("- Para expandir a auditoria, rode o script com `--all`.")
    lines.append("")
    lines.append("## Reproducao")
    lines.append("")
    lines.append("```bash")
    lines.append("cd backend")
    lines.append("python scripts/audit_northeast_sources.py")
    lines.append("python scripts/audit_northeast_sources.py --all")
    lines.append("```")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    db_url = configure_env(args.database_url)

    from app.db.base import Base
    from app.db.session import SessionLocal, engine
    from app.services.northeast_seed import seed_northeast_institutions

    if db_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        catalog_counts = load_catalog_counts()
        initials = selected_initials(args.all, args.institutions)

        seed_first = None
        seed_second = None
        if not args.skip_seed:
            seed_first = seed_northeast_institutions(db)
            seed_second = seed_northeast_institutions(db)

        sources = get_sources(db, initials)
        if not sources:
            raise RuntimeError("No active sources found for selected institutions.")

        first_run = audit_once(db, sources, args, "run-1")
        notice_ids_before_second = scoped_notice_ids(db, initials)
        sources = get_sources(db, initials)
        second_run = audit_once(db, sources, args, "run-2")
        notice_ids_after_second = scoped_notice_ids(db, initials)
        second_new_ids = sorted(notice_ids_after_second - notice_ids_before_second)
        filters = filter_results(db, initials)
        types = notice_type_counts(db, initials)
        notices_total = active_notice_count(db, initials)
        institutions_with_notice = institutions_with_notices(db, initials)
        saved_examples = notice_samples(db, initials)
        second_new_notices = describe_notice_ids(db, second_new_ids)
        duplicate_findings = duplicate_investigation(db, second_new_ids)

        render_report(
            Path(args.output),
            db_url,
            initials,
            catalog_counts,
            seed_first,
            seed_second,
            first_run,
            second_run,
            filters,
            types,
            notices_total,
            institutions_with_notice,
            saved_examples,
            second_new_notices,
            duplicate_findings,
        )

        status_counts = Counter(item["status"] for item in first_run["sources"])
        console_summary = {
            "sources_checked": len(first_run["sources"]),
            "first_run": first_run["summary"],
            "second_run": second_run["summary"],
            "statuses": dict(status_counts),
            "institutions_with_notices": len(institutions_with_notice),
            "institutions": institutions_with_notice,
            "active_notices_in_scope": notices_total,
            "second_new_notice_ids": second_new_ids,
            "duplicate_findings": duplicate_findings,
            "notice_types": dict(types),
            "report": str(Path(args.output).resolve()),
        }
        print(json.dumps(console_summary, indent=2, ensure_ascii=False))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
