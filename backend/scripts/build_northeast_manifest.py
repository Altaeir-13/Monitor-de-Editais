"""Convert the legacy Northeast seed into the national manifest schema.

This is an offline, deterministic conversion.  Legacy URLs are classified as
``partial`` rather than promoted to ``verified``.  Five researched corrections
and the UFAPE/UFDPar additions are explicit below; institutions for which no
official source is available remain represented with ``source_not_found``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.catalog.urls import URLNormalizationError, normalize_url  # noqa: E402


DEFAULT_LEGACY = BACKEND_DIR / "app" / "seeds" / "northeast_institutions.json"
DEFAULT_CATALOG = BACKEND_DIR / "app" / "catalog" / "institutions_2024.json"
DEFAULT_OUTPUT = BACKEND_DIR / "app" / "catalog" / "sources" / "northeast.json"
VERIFIED_AT = "2026-07-13"
EXPECTED_LEGACY_INSTITUTIONS = 44
EXPECTED_REGION_INSTITUTIONS = 66


class BuildError(RuntimeError):
    """Raised when the legacy seed cannot be converted without ambiguity."""


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BuildError(f"input file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise BuildError(f"invalid JSON in {path}: {exc}") from exc


def _token(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(character for character in text if character.isalnum()).casefold()


def _slug(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value)
    ascii_value = folded.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")
    return slug[:48] or "source"


def _safe_url(value: Any, context: str) -> str:
    try:
        return normalize_url(str(value or ""))
    except URLNormalizationError as exc:
        raise BuildError(f"{context}: {exc}") from exc


def _as_replaces(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        raise BuildError(f"legacy replaces must be a string or list, got {value!r}")
    result: list[str] = []
    for item in value:
        text = str(item).strip()
        if not text:
            continue
        if text.lower().startswith(("http://", "https://")):
            text = _safe_url(text, "legacy replaces URL")
        if text not in result:
            result.append(text)
    return result


def _stable_source_id(code: str, name: str, url: str) -> str:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:10]
    return f"inep-{code}-{_slug(name)}-{digest}"


def _legacy_source(code: str, raw: dict[str, Any], index: int) -> dict[str, Any]:
    name = str(raw.get("name") or f"Fonte legada {index + 1}").strip()
    url = _safe_url(raw.get("url"), f"institution {code} legacy source[{index}]")
    source_type = str(raw.get("source_type") or "editais").strip()
    return {
        "catalog_source_id": _stable_source_id(code, name, url),
        "name": name,
        "url": url,
        "source_type": source_type,
        "content_type": source_type.replace("_", " "),
        "recommended_spider": "sigaa" if "sigaa" in url.casefold() else "generic",
        "status": "partial",
        "last_verified_at": None,
        "http_status": None,
        "final_url": None,
        "redirect_chain": [],
        "page_title": None,
        "verification_evidence": "Migrada do seed Nordeste anterior; confirmação de domínio não equivale a verificação estrutural atual.",
        "verification_notes": "Mantida como partial até auditoria HTTP e validação controlada de captura.",
        "priority": 2,
        "categories": [source_type],
        "is_active": False,
        "capture_validated_at": None,
        "capture_evidence": None,
        "replaces": _as_replaces(raw.get("replaces")),
    }


def _researched_source(
    code: str,
    source_id_suffix: str,
    name: str,
    url: str,
    *,
    source_type: str = "editais",
    content_type: str = "editais institucionais",
    spider: str = "generic",
    evidence: str,
    categories: list[str],
    replaces: list[str] | None = None,
    page_title: str | None = None,
) -> dict[str, Any]:
    normalized = _safe_url(url, f"researched source {code}/{source_id_suffix}")
    return {
        "catalog_source_id": f"inep-{code}-{source_id_suffix}",
        "name": name,
        "url": normalized,
        "source_type": source_type,
        "content_type": content_type,
        "recommended_spider": spider,
        "status": "partial",
        "last_verified_at": VERIFIED_AT,
        "http_status": 200,
        "final_url": normalized,
        "redirect_chain": [],
        "page_title": page_title,
        "verification_evidence": evidence,
        "verification_notes": "URL oficial confirmada; cobertura temática parcial e captura ainda não validada.",
        "priority": 2,
        "categories": categories,
        "is_active": False,
        "capture_validated_at": None,
        "capture_evidence": None,
        "replaces": sorted(set(replaces or [])),
    }


def _legacy_replacement_targets(sources: list[dict[str, Any]]) -> list[str]:
    targets: list[str] = []
    for source in sources:
        for value in [source["catalog_source_id"], source["url"], *source["replaces"]]:
            if value not in targets:
                targets.append(value)
    return targets


def _apply_researched_corrections(
    institution: dict[str, Any], legacy_sources: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    code = str(institution["official_code"])
    initials = _token(institution.get("official_initials") or institution.get("initials"))
    replaces = _legacy_replacement_targets(legacy_sources)

    if initials == "uemasul":
        return [
            _researched_source(
                code,
                "uemasul-publicacoes-editais",
                "Publicações - Editais UEMASUL",
                "https://www.uemasul.edu.br/publicacoes/?td=1",
                evidence="Filtro oficial de publicações direcionado a editais da UEMASUL.",
                categories=["editais"],
                replaces=replaces,
                page_title="Publicações",
            )
        ]
    if initials == "ifsertaope":
        return [
            _researched_source(
                code,
                "ifsertaope-editais",
                "Editais IFSertãoPE",
                "https://ifsertaope.edu.br/editais/",
                evidence="Página oficial dedicada a editais do IFSertãoPE.",
                categories=["editais", "ensino", "pesquisa", "extensao"],
                replaces=replaces,
                page_title="Editais",
            )
        ]
    if initials == "ifba":
        definitions = [
            (
                "ifba-proex-editais",
                "Editais PROEX IFBA",
                "https://portal.ifba.edu.br/proex/editais",
                "extensao",
            ),
            (
                "ifba-proen-editais",
                "Editais PROEN IFBA",
                "https://portal.ifba.edu.br/proen/editais",
                "ensino",
            ),
            (
                "ifba-prpgi-editais-2026",
                "Editais 2026 PRPGI IFBA",
                "https://portal.ifba.edu.br/prpgi/editais/2026",
                "pesquisa-e-pos-graduacao",
            ),
        ]
        return [
            _researched_source(
                code,
                suffix,
                name,
                url,
                evidence="Página temática oficial de editais do IFBA; substitui a homepage genérica do seed legado.",
                categories=[category],
                replaces=replaces if index == 0 else [],
                page_title="Editais",
            )
            for index, (suffix, name, url, category) in enumerate(definitions)
        ]
    if initials == "ifs":
        return [
            _researched_source(
                code,
                "ifs-editais-propex",
                "Editais PROPEX IFS",
                "https://www.ifs.edu.br/editais-propex",
                evidence="Página oficial dedicada aos editais da Pró-Reitoria de Pesquisa e Extensão do IFS.",
                categories=["pesquisa", "extensao"],
                replaces=replaces,
                page_title="Editais PROPEX",
            )
        ]
    if initials == "ifbaiano":
        return [
            _researched_source(
                code,
                "ifbaiano-ingresso-editais",
                "Editais de Processo Seletivo - Portal de Ingresso IF Baiano",
                "https://ingresso.ifbaiano.edu.br/concursos/",
                source_type="processos_seletivos",
                content_type="editais de ingresso",
                spider="wordpress",
                evidence="Portal oficial de ingresso lista processos, incluindo graduação, com acesso aos editais.",
                categories=["ingresso", "graduacao", "cursos-tecnicos"],
                replaces=replaces,
                page_title="Editais de Processos Seletivos",
            ),
            _researched_source(
                code,
                "ifbaiano-concursos-selecoes",
                "Concursos e Seleções IF Baiano",
                "https://ifbaiano.edu.br/portal/concursos/",
                source_type="concursos_e_selecoes",
                content_type="concursos, chamadas e seleções",
                spider="wordpress",
                evidence="Página institucional oficial reúne concursos e seleções por ano e categoria.",
                categories=["concursos", "pessoal", "bolsas", "assistencia-estudantil"],
                page_title="Concursos e Seleções",
            ),
        ]
    return legacy_sources


def _newly_mapped_sources(institution: dict[str, Any]) -> list[dict[str, Any]]:
    code = str(institution["official_code"])
    initials = _token(institution.get("official_initials") or institution.get("initials"))
    if initials == "ufape":
        return [
            _researched_source(
                code,
                "ufape-editais-selecoes",
                "Editais e Seleções UFAPE",
                "https://ufape.edu.br/editais-e-sele%C3%A7%C3%B5es",
                content_type="editais e seleções institucionais",
                evidence="Página oficial apresentou editais e seleções correntes em 2026.",
                categories=["assistencia-estudantil", "ingresso", "ensino"],
                page_title="Editais e Seleções",
            )
        ]
    if initials == "ufdpar":
        return [
            _researched_source(
                code,
                "ufdpar-editais",
                "Editais UFDPar",
                "https://ufdpar.edu.br/ufdpar/editais-1",
                content_type="editais institucionais",
                spider="govbr",
                evidence="Índice oficial paginado apresentou editais correntes de 2026 de diferentes pró-reitorias.",
                categories=["ensino", "pesquisa", "extensao", "assistencia-estudantil", "pessoal"],
                page_title="Editais",
            )
        ]
    return []


def _index_catalog(catalog: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[tuple[str, str], list[dict[str, Any]]]]:
    institutions = catalog.get("institutions")
    if not isinstance(institutions, list):
        raise BuildError("catalog institutions must be a list")
    northeast = [item for item in institutions if item.get("region") == "Nordeste"]
    if len(northeast) != EXPECTED_REGION_INSTITUTIONS:
        raise BuildError(
            f"expected {EXPECTED_REGION_INSTITUTIONS} Northeast census institutions, got {len(northeast)}"
        )
    index: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for institution in northeast:
        state = str(institution.get("state") or "").upper()
        for value in {
            institution.get("official_initials"),
            institution.get("initials"),
            institution.get("official_name"),
        }:
            token = _token(value)
            if token:
                index.setdefault((token, state), []).append(institution)
    return northeast, index


def _match_legacy(
    raw: dict[str, Any], index: dict[tuple[str, str], list[dict[str, Any]]]
) -> dict[str, Any]:
    state = str(raw.get("state") or "").strip().upper()
    candidates: dict[str, dict[str, Any]] = {}
    for value in [raw.get("initials"), raw.get("name")]:
        for institution in index.get((_token(value), state), []):
            candidates[str(institution["official_code"])] = institution
    if len(candidates) != 1:
        raise BuildError(
            f"legacy institution {raw.get('initials')!r}/{state} matched "
            f"{sorted(candidates)}; expected exactly one census institution"
        )
    return next(iter(candidates.values()))


def build_manifest(legacy_payload: Any, catalog: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(legacy_payload, list):
        raise BuildError("legacy Northeast seed root must be a list")
    if len(legacy_payload) != EXPECTED_LEGACY_INSTITUTIONS:
        raise BuildError(
            f"expected {EXPECTED_LEGACY_INSTITUTIONS} legacy institutions, got {len(legacy_payload)}"
        )
    northeast, index = _index_catalog(catalog)
    legacy_by_code: dict[str, dict[str, Any]] = {}
    for raw in legacy_payload:
        if not isinstance(raw, dict):
            raise BuildError("each legacy institution must be an object")
        matched = _match_legacy(raw, index)
        code = str(matched["official_code"])
        if code in legacy_by_code:
            raise BuildError(f"more than one legacy institution matched INEP code {code}")
        legacy_by_code[code] = raw

    output: list[dict[str, Any]] = []
    added_partial = 0
    source_not_found = 0
    for institution in sorted(northeast, key=lambda item: int(str(item["official_code"]))):
        code = str(institution["official_code"])
        legacy = legacy_by_code.get(code)
        if legacy is not None:
            raw_sources = legacy.get("sources", [])
            if not isinstance(raw_sources, list):
                raise BuildError(f"legacy institution {code} sources must be a list")
            sources = [
                _legacy_source(code, raw_source, index_value)
                for index_value, raw_source in enumerate(raw_sources)
            ]
            sources = _apply_researched_corrections(institution, sources)
            site = (
                _safe_url(legacy.get("official_site_url"), f"institution {code} official site")
                if legacy.get("official_site_url")
                else None
            )
            coverage_status = "partial" if sources else "source_not_found"
            coverage_notes = (
                "Fontes migradas do seed regional e mantidas como partial até auditoria estrutural controlada."
                if sources
                else "Seed legado não continha fonte oficial utilizável."
            )
        else:
            sources = _newly_mapped_sources(institution)
            if sources:
                added_partial += 1
                site = _safe_url(sources[0]["url"].split("/", 3)[0] + "//" + sources[0]["url"].split("/", 3)[2], f"institution {code} site")
                coverage_status = "partial"
                coverage_notes = "Instituição ausente no seed legado; fonte oficial localizada e mantida partial até validação de captura."
            else:
                source_not_found += 1
                site = None
                coverage_status = "source_not_found"
                coverage_notes = "Instituição presente no inventário oficial, mas sem fonte oficial de editais localizada nesta rodada."

        output.append(
            {
                "official_code": code,
                "official_site_url": site,
                "coverage_status": coverage_status,
                "coverage_notes": coverage_notes,
                "sources": sorted(sources, key=lambda item: item["catalog_source_id"]),
            }
        )

    if len(legacy_by_code) != EXPECTED_LEGACY_INSTITUTIONS:
        raise BuildError("not every legacy institution was represented")
    if added_partial != 2:
        raise BuildError(f"expected UFAPE and UFDPar additions, got {added_partial}")
    if source_not_found != 20:
        raise BuildError(f"expected 20 institutions without sources, got {source_not_found}")
    return {
        "schema_version": 1,
        "region": "Nordeste",
        "verified_at": VERIFIED_AT,
        "institutions": output,
    }


def _write_json(payload: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    temporary = output.with_name(f".{output.name}.tmp")
    temporary.write_text(serialized, encoding="utf-8", newline="\n")
    temporary.replace(output)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the Northeast source manifest.")
    parser.add_argument("--legacy", type=Path, default=DEFAULT_LEGACY)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        manifest = build_manifest(_load_json(args.legacy), _load_json(args.catalog))
        _write_json(manifest, args.output)
    except BuildError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    source_total = sum(len(item["sources"]) for item in manifest["institutions"])
    print(
        f"Wrote {len(manifest['institutions'])} Northeast institutions and "
        f"{source_total} sources to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
