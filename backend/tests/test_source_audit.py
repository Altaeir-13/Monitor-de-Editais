"""Offline tests for the conservative national source audit."""

from __future__ import annotations

import os
import socket
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.source_audit import (  # noqa: E402
    AUDIT_USER_AGENT,
    AuditPolicy,
    SafeSourceAuditor,
    select_controlled_sample,
)


FIXED_NOW = datetime(2026, 7, 13, 15, 30, tzinfo=timezone.utc)
PUBLIC_ADDRESS = "93.184.216.34"


class FakeResponse:
    def __init__(
        self,
        status_code: int = 200,
        *,
        body: bytes | str = b"",
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.body = body.encode("utf-8") if isinstance(body, str) else body
        self.headers = headers or {"Content-Type": "text/html; charset=utf-8"}
        self.closed = False

    def iter_content(self, chunk_size: int):
        for offset in range(0, len(self.body), chunk_size):
            yield self.body[offset : offset + chunk_size]

    def close(self) -> None:
        self.closed = True


class FakeRequester:
    def __init__(self, outcomes: list[Any]) -> None:
        self.outcomes = list(outcomes)
        self.calls: list[dict[str, Any]] = []

    def __call__(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        if not self.outcomes:
            raise AssertionError(f"unexpected network call: {url}")
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


def public_resolver(host: str, port: int, *args: Any):
    del host, port, args
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (PUBLIC_ADDRESS, 443))]


def policy(*, robots: bool = False, retries: int = 2, max_body: int = 10_000) -> AuditPolicy:
    return AuditPolicy(
        timeout_seconds=3,
        max_retries=retries,
        min_host_interval_seconds=0,
        max_connections_per_host=2,
        max_redirects=3,
        max_body_bytes=max_body,
        obey_robots=robots,
    )


def source(**overrides: Any) -> dict[str, Any]:
    result = {
        "catalog_source_id": "inep-1-editais",
        "name": "Editais oficiais",
        "url": "https://editais.example.edu.br/editais",
        "recommended_spider": "generic",
        "status": "verified",
        "priority": 1,
    }
    result.update(overrides)
    return result


def institution(**overrides: Any) -> dict[str, Any]:
    result = {
        "official_code": "1",
        "official_name": "Universidade Pública de Exemplo",
        "official_site_url": "https://www.example.edu.br/",
        "region": "Sudeste",
        "state": "SP",
        "eligibility_status": "included_in_census_2024",
        "sources": [],
    }
    result.update(overrides)
    return result


def valid_html(title: str = "Editais 2026") -> str:
    return (
        "<!doctype html><html><head><title>"
        + title
        + "</title></head><body><main><a href='/edital-1.pdf'>"
        "Edital 1 — processo seletivo</a></main></body></html>"
    )


class SourceAuditTests(unittest.TestCase):
    def make_auditor(
        self,
        requester: FakeRequester,
        *,
        audit_policy: AuditPolicy | None = None,
        resolver=public_resolver,
        sleeps: list[float] | None = None,
    ) -> SafeSourceAuditor:
        recorded_sleeps = sleeps if sleeps is not None else []
        return SafeSourceAuditor(
            audit_policy or policy(),
            requester=requester,
            resolver=resolver,
            sleeper=recorded_sleeps.append,
            now=lambda: FIXED_NOW,
        )

    def test_valid_html_title_and_redirect_are_recorded(self) -> None:
        requester = FakeRequester(
            [
                FakeResponse(302, headers={"Location": "/editais/atuais"}),
                FakeResponse(200, body=valid_html("Seleções e Editais")),
            ]
        )
        auditor = self.make_auditor(requester)

        result = auditor.audit_source(source(), institution())

        self.assertEqual(result.status, "verified")
        self.assertEqual(result.page_title, "Seleções e Editais")
        self.assertTrue(result.html_valid)
        self.assertTrue(result.expected_elements_found)
        self.assertTrue(result.notice_terms_found)
        self.assertEqual(result.http_status, 200)
        self.assertEqual(
            result.redirect_chain,
            ["https://editais.example.edu.br/editais/atuais"],
        )
        self.assertEqual(result.attempts, 2)
        self.assertEqual(result.checked_at, "2026-07-13T15:30:00Z")
        self.assertTrue(result.domain_matches_institution)
        self.assertEqual(requester.calls[0]["headers"]["User-Agent"], AUDIT_USER_AGENT)
        self.assertFalse(requester.calls[0]["allow_redirects"])
        self.assertTrue(requester.calls[0]["stream"])

    def test_timeout_is_retried_twice_and_can_recover(self) -> None:
        sleeps: list[float] = []
        requester = FakeRequester(
            [
                requests.Timeout("first"),
                requests.Timeout("second"),
                FakeResponse(200, body=valid_html()),
            ]
        )
        auditor = self.make_auditor(requester, sleeps=sleeps)

        result = auditor.audit_source(source(), institution())

        self.assertEqual(result.status, "verified")
        self.assertEqual(result.attempts, 3)
        self.assertEqual(len(requester.calls), 3)
        self.assertEqual(sleeps, [0.5, 1.0])

    def test_exhausted_timeout_is_temporarily_unavailable(self) -> None:
        requester = FakeRequester(
            [requests.Timeout("one"), requests.Timeout("two"), requests.Timeout("three")]
        )
        auditor = self.make_auditor(requester)

        result = auditor.audit_source(source(), institution())

        self.assertEqual(result.status, "temporarily_unavailable")
        self.assertEqual(result.error_code, "timeout")
        self.assertEqual(result.attempts, 3)

    def test_retryable_http_status_is_retried(self) -> None:
        requester = FakeRequester(
            [
                FakeResponse(503, body="temporarily down"),
                FakeResponse(200, body=valid_html()),
            ]
        )
        auditor = self.make_auditor(requester)

        result = auditor.audit_source(source(), institution())

        self.assertEqual(result.status, "verified")
        self.assertEqual(result.attempts, 2)

    def test_dns_failure_prevents_every_http_request(self) -> None:
        requester = FakeRequester([])

        def failing_resolver(*args: Any):
            del args
            raise socket.gaierror("name not known")

        auditor = self.make_auditor(requester, resolver=failing_resolver)

        result = auditor.audit_source(source(), institution())

        self.assertEqual(result.status, "temporarily_unavailable")
        self.assertEqual(result.error_code, "dns_failure")
        self.assertEqual(requester.calls, [])

    def test_private_dns_destination_is_refused(self) -> None:
        requester = FakeRequester([])

        def private_resolver(*args: Any):
            del args
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))]

        auditor = self.make_auditor(requester, resolver=private_resolver)

        result = auditor.audit_source(source(), institution())

        self.assertEqual(result.status, "manual_review")
        self.assertEqual(result.error_code, "non_public_destination")
        self.assertEqual(requester.calls, [])

    def test_robots_disallow_stops_before_source_page(self) -> None:
        requester = FakeRequester(
            [
                FakeResponse(
                    200,
                    body="User-agent: *\nDisallow: /private\n",
                    headers={"Content-Type": "text/plain"},
                )
            ]
        )
        auditor = self.make_auditor(requester, audit_policy=policy(robots=True))

        result = auditor.audit_source(
            source(url="https://editais.example.edu.br/private/lista"),
            institution(),
        )

        self.assertEqual(result.status, "manual_review")
        self.assertEqual(result.error_code, "robots_disallowed")
        self.assertEqual(len(requester.calls), 1)
        self.assertTrue(requester.calls[0]["url"].endswith("/robots.txt"))

    def test_missing_robots_file_allows_one_landing_page(self) -> None:
        requester = FakeRequester(
            [
                FakeResponse(404, headers={"Content-Type": "text/plain"}),
                FakeResponse(200, body=valid_html()),
            ]
        )
        auditor = self.make_auditor(requester, audit_policy=policy(robots=True))

        result = auditor.audit_source(source(), institution())

        self.assertEqual(result.status, "verified")
        self.assertEqual(len(requester.calls), 2)

    def test_manual_review_and_unsupported_are_never_requested(self) -> None:
        requester = FakeRequester([])
        auditor = self.make_auditor(requester)

        manual = auditor.audit_source(source(status="manual_review"), institution())
        unsupported = auditor.audit_source(source(status="unsupported"), institution())

        self.assertEqual(manual.status, "manual_review")
        self.assertEqual(manual.error_code, "declared_manual_review")
        self.assertEqual(unsupported.status, "unsupported")
        self.assertEqual(unsupported.error_code, "declared_unsupported")
        self.assertEqual(requester.calls, [])

    def test_document_url_is_unsupported_without_request(self) -> None:
        requester = FakeRequester([])
        auditor = self.make_auditor(requester)

        result = auditor.audit_source(
            source(url="https://editais.example.edu.br/Edital.PDF?download=1"),
            institution(),
        )

        self.assertEqual(result.status, "unsupported")
        self.assertEqual(result.error_code, "document_url")
        self.assertEqual(requester.calls, [])

    def test_non_html_response_is_unsupported(self) -> None:
        requester = FakeRequester(
            [FakeResponse(200, body=b"%PDF", headers={"Content-Type": "application/pdf"})]
        )
        auditor = self.make_auditor(requester)

        result = auditor.audit_source(source(), institution())

        self.assertEqual(result.status, "unsupported")
        self.assertEqual(result.error_code, "non_html_content")

    def test_body_limit_stops_large_response(self) -> None:
        requester = FakeRequester([FakeResponse(200, body=b"x" * 1_500)])
        auditor = self.make_auditor(
            requester,
            audit_policy=policy(max_body=1_024),
        )

        result = auditor.audit_source(source(), institution())

        self.assertEqual(result.status, "unsupported")
        self.assertEqual(result.error_code, "body_too_large")

    def test_html_without_title_is_partial(self) -> None:
        requester = FakeRequester(
            [
                FakeResponse(
                    200,
                    body=(
                        "<html><body><a href='/edital.pdf'>"
                        "Edital de processo seletivo</a></body></html>"
                    ),
                )
            ]
        )
        auditor = self.make_auditor(requester)

        result = auditor.audit_source(source(), institution())

        self.assertEqual(result.status, "partial")
        self.assertEqual(result.error_code, "structure_partial")
        self.assertIsNone(result.page_title)
        self.assertIn("título", result.evidence)

    def test_captcha_is_manual_review_without_bypass(self) -> None:
        requester = FakeRequester(
            [
                FakeResponse(
                    200,
                    body=(
                        "<html><head><title>Captcha</title></head><body>"
                        "<div class='g-recaptcha'>Confirme que você é humano</div>"
                        "</body></html>"
                    ),
                )
            ]
        )
        auditor = self.make_auditor(requester)

        result = auditor.audit_source(source(), institution())

        self.assertEqual(result.status, "manual_review")
        self.assertEqual(result.error_code, "captcha_detected")
        self.assertEqual(len(requester.calls), 1)

    def test_authentication_response_is_manual_review_without_retry(self) -> None:
        requester = FakeRequester([FakeResponse(403, body="Access denied")])
        auditor = self.make_auditor(requester)

        result = auditor.audit_source(source(), institution())

        self.assertEqual(result.status, "manual_review")
        self.assertEqual(result.error_code, "authentication_or_access_blocked")
        self.assertEqual(len(requester.calls), 1)

    def test_cross_domain_redirect_requires_manual_review(self) -> None:
        requester = FakeRequester(
            [
                FakeResponse(302, headers={"Location": "https://unrelated.example.net/list"}),
                FakeResponse(200, body=valid_html()),
            ]
        )
        auditor = self.make_auditor(requester)

        result = auditor.audit_source(source(), institution())

        self.assertEqual(result.status, "manual_review")
        self.assertEqual(result.error_code, "cross_domain_redirect")

    def test_policy_never_allows_more_than_two_connections_per_host(self) -> None:
        with self.assertRaises(ValueError):
            AuditPolicy(max_connections_per_host=3)

    def test_controlled_sample_covers_regions_and_spiders(self) -> None:
        pairs = [
            ("Norte", "AC", "generic"),
            ("Nordeste", "BA", "wordpress"),
            ("Centro-Oeste", "DF", "govbr"),
            ("Sudeste", "SP", "sigaa"),
            ("Sul", "RS", "pagination"),
        ]
        institutions: list[dict[str, Any]] = []
        for index, (region, state, spider) in enumerate(pairs, start=1):
            item_source = source(
                catalog_source_id=f"source-{index}",
                url=f"https://ies{index}.example.edu.br/editais",
                recommended_spider=spider,
            )
            institutions.append(
                institution(
                    official_code=str(index),
                    official_name=f"IES {index}",
                    region=region,
                    state=state,
                    sources=[item_source, source(catalog_source_id=f"manual-{index}", status="manual_review")],
                )
            )

        plan = select_controlled_sample(institutions, max_samples=10)

        self.assertEqual(len(plan.selections), 5)
        self.assertEqual(plan.missing_regions, ())
        self.assertEqual(plan.missing_spiders, ())
        self.assertEqual(set(plan.represented_regions), {item[0] for item in pairs})
        self.assertEqual(set(plan.represented_spiders), {item[2] for item in pairs})
        selected_ids = {
            item["source"]["catalog_source_id"] for item in plan.selections
        }
        self.assertFalse(any(source_id.startswith("manual-") for source_id in selected_ids))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SourceAuditTests)
    outcome = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if outcome.wasSuccessful() else 1)
