"""Run a small, reproducible audit sample of national source landing pages.

The command is a dry run unless ``--execute-network`` is supplied.  There is
deliberately no ``--all`` option: the selection is capped at ten pages and must
cover regions and recommended spider families instead of crawling the catalog.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.catalog.loader import REGION_MANIFESTS, load_national_catalog  # noqa: E402
from app.services.source_audit import (  # noqa: E402
    AuditPolicy,
    SafeSourceAuditor,
    SamplePlan,
    select_controlled_sample,
)


DEFAULT_JSON = REPO_ROOT / "docs" / "auditoria_fontes_nacional.json"
DEFAULT_MARKDOWN = REPO_ROOT / "docs" / "auditoria_fontes_nacional.md"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Select and optionally audit a controlled national sample. "
            "Without --execute-network no HTTP request is made."
        )
    )
    parser.add_argument(
        "--execute-network",
        action="store_true",
        help="Explicitly authorize requests for only the selected landing pages and robots.txt.",
    )
    parser.add_argument(
        "--regions",
        default=",".join(REGION_MANIFESTS),
        help="Comma-separated regions. Default: all five official regions.",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=10,
        help="Hard cap from 1 to 10 landing pages (default: 10).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Per-request timeout, from 1 to 30 seconds (default: 10).",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=DEFAULT_JSON,
        help=f"Structured report path (default: {DEFAULT_JSON}).",
    )
    parser.add_argument(
        "--output-markdown",
        type=Path,
        default=DEFAULT_MARKDOWN,
        help=f"Human-readable report path (default: {DEFAULT_MARKDOWN}).",
    )
    args = parser.parse_args(argv)
    if not 1 <= args.max_samples <= 10:
        parser.error("--max-samples must be between 1 and 10")
    if not 1 <= args.timeout <= 30:
        parser.error("--timeout must be between 1 and 30 seconds")
    requested = [region.strip() for region in args.regions.split(",") if region.strip()]
    unknown = set(requested) - set(REGION_MANIFESTS)
    if not requested or unknown:
        parser.error(
            "--regions must contain known regions; "
            f"allowed={list(REGION_MANIFESTS)}, unknown={sorted(unknown)}"
        )
    args.regions = list(dict.fromkeys(requested))
    return args


def _plan_payload(plan: SamplePlan) -> dict[str, Any]:
    payload = plan.to_dict()
    payload["network_requested"] = False
    payload["safety_note"] = (
        "A seleção cobre regiões e spiders sem abrir links de documentos nem executar spiders."
    )
    return payload


def _escape_cell(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def _markdown_report(report: dict[str, Any]) -> str:
    metadata = report["metadata"]
    selection = report["selection"]
    counts = report["status_counts"]
    lines = [
        "# Auditoria controlada de fontes nacionais",
        "",
        f"- Gerado em: `{metadata['generated_at']}`",
        f"- Páginas selecionadas: **{selection['selected_count']}** (limite: {metadata['max_samples']})",
        f"- Regiões representadas: {', '.join(selection['represented_regions']) or 'nenhuma'}",
        f"- Spiders representados: {', '.join(selection['represented_spiders']) or 'nenhum'}",
        "- Escopo: somente a página HTML inicial e o `robots.txt`; nenhum documento ou link listado foi aberto.",
        "- Rede: execução sequencial, no máximo duas conexões simultâneas por host, intervalo mínimo de 1 segundo, timeout e dois retries.",
        "",
        "## Resultado",
        "",
    ]
    if counts:
        for status, count in sorted(counts.items()):
            lines.append(f"- `{status}`: {count}")
    else:
        lines.append("Nenhum resultado: esta estrutura só é gravada após `--execute-network`.")

    if selection["missing_regions"] or selection["missing_spiders"]:
        lines.extend(
            [
                "",
                "## Lacunas da amostra",
                "",
                f"- Regiões sem fonte auditável: {', '.join(selection['missing_regions']) or 'nenhuma'}",
                f"- Spiders sem fonte auditável: {', '.join(selection['missing_spiders']) or 'nenhum'}",
            ]
        )

    lines.extend(
        [
            "",
            "## Evidências por fonte",
            "",
            "| Região | UF | Instituição | Fonte | Spider | Status | HTTP | Título | Evidência |",
            "|---|---|---|---|---|---|---:|---|---|",
        ]
    )
    for result in report["results"]:
        lines.append(
            "| "
            + " | ".join(
                _escape_cell(value)
                for value in (
                    result["region"],
                    result["state"],
                    result["institution_name"],
                    result["source_id"],
                    result["recommended_spider"],
                    result["status"],
                    result["http_status"],
                    result["page_title"],
                    result["evidence"],
                )
            )
            + " |"
        )

    pending = [result for result in report["results"] if result["status"] != "verified"]
    lines.extend(["", "## Pendências explícitas", ""])
    if not pending:
        lines.append("Nenhuma pendência na amostra controlada.")
    for result in pending:
        reason = result["error_code"] or result["evidence"]
        lines.append(
            f"- `{result['source_id']}` ({result['institution_name']}): "
            f"`{result['status']}` — {reason}."
        )

    lines.extend(
        [
            "",
            "## Interpretação",
            "",
            "`verified` nesta auditoria confirma DNS, HTTP, HTML, título, termos e elementos estruturais prováveis. Não equivale a captura validada nem a monitoramento ativo. `partial`, `manual_review`, `unsupported` e indisponibilidades permanecem pendentes, sem tentativa de evasão.",
            "",
        ]
    )
    return "\n".join(lines)


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    temporary.replace(path)


def execute(args: argparse.Namespace) -> tuple[SamplePlan, dict[str, Any] | None]:
    catalog = load_national_catalog(regions=args.regions, include_post_census=True)
    plan = select_controlled_sample(
        catalog["institutions"],
        regions=args.regions,
        max_samples=args.max_samples,
    )
    if not args.execute_network:
        return plan, None

    policy = AuditPolicy(
        timeout_seconds=args.timeout,
        max_retries=2,
        min_host_interval_seconds=1.0,
        max_connections_per_host=2,
        max_redirects=5,
        max_body_bytes=1_000_000,
        obey_robots=True,
    )
    auditor = SafeSourceAuditor(policy)
    try:
        results = [
            auditor.audit_source(item["source"], item["institution"])
            for item in plan.selections
        ]
    finally:
        auditor.close()

    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    result_payloads = [result.to_dict() for result in results]
    report = {
        "schema_version": 1,
        "metadata": {
            "generated_at": generated_at,
            "inventory_reference_date": catalog["metadata"].get("reference_date"),
            "selected_regions": args.regions,
            "max_samples": args.max_samples,
            "network_scope": "selected_landing_pages_and_robots_only",
            "policy": asdict(policy),
        },
        "selection": plan.to_dict(),
        "status_counts": dict(sorted(Counter(item["status"] for item in result_payloads).items())),
        "results": result_payloads,
    }
    return plan, report


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    plan, report = execute(args)
    if report is None:
        print(json.dumps(_plan_payload(plan), ensure_ascii=False, indent=2))
        print("\nDry run: nenhuma requisição foi feita. Use --execute-network para a amostra acima.")
        return 0

    _atomic_write(
        args.output_json,
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _atomic_write(args.output_markdown, _markdown_report(report))
    print(f"Auditoria amostral concluída: {len(report['results'])} fonte(s).")
    print(f"JSON: {args.output_json}")
    print(f"Markdown: {args.output_markdown}")
    if plan.missing_regions or plan.missing_spiders:
        print(
            "Amostra com lacunas: "
            f"regiões={list(plan.missing_regions)}, spiders={list(plan.missing_spiders)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
