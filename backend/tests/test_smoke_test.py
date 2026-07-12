import json
import os
import sys
from urllib.parse import urlparse

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from scripts.smoke_test import build_api_base_url, run_smoke_test


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.content = b"{}"

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, *, include_token=True):
        self.calls = []
        self.include_token = include_token
        self.verify = None

    def get(self, url, **kwargs):
        self.calls.append(("GET", url))
        path = urlparse(url).path
        if path in {"/health", "/ready"}:
            return FakeResponse(200, {"status": "ok"})
        if path.endswith("/openapi.json"):
            return FakeResponse(200, {"openapi": "3.1.0"})
        if path.endswith("/admin/sources/") or path.endswith("/notices/"):
            return FakeResponse(200, [])
        if path.endswith("/admin/crawler/status"):
            return FakeResponse(200, {"total_sources": 0})
        return FakeResponse(404, {"detail": "not found"})

    def post(self, url, **kwargs):
        self.calls.append(("POST", url))
        if urlparse(url).path.endswith("/auth/login"):
            payload = {"access_token": "fake-token"} if self.include_token else {}
            return FakeResponse(200, payload)
        return FakeResponse(404, {"detail": "not found"})


session = FakeSession()
smoke_results = run_smoke_test(
    base_url="https://editais-staging.example.net",
    admin_email="admin@example.net",
    admin_password="not-printed",
    timeout=1,
    api_prefix="/api",
    expect_openapi=True,
    verify_tls=True,
    session=session,
)

session_without_openapi = FakeSession()
results_without_openapi = run_smoke_test(
    base_url="https://editais-staging.example.net/",
    admin_email="admin@example.net",
    admin_password="not-printed",
    timeout=1,
    expect_openapi=False,
    verify_tls=False,
    session=session_without_openapi,
)

missing_token_rejected = False
try:
    run_smoke_test(
        base_url="https://editais-staging.example.net",
        admin_email="admin@example.net",
        admin_password="not-printed",
        timeout=1,
        session=FakeSession(include_token=False),
    )
except RuntimeError:
    missing_token_rejected = True

origin_with_path_rejected = False
try:
    build_api_base_url("https://editais-staging.example.net/api", "/api")
except RuntimeError:
    origin_with_path_rejected = True

paths = [urlparse(url).path for _, url in session.calls]
api_paths = [path for path in paths if path not in {"/health", "/ready"}]
results = {
    "1_all_smoke_checks_pass": all(value == "ok" for value in smoke_results.values()),
    "2_public_health_routes_used": "/health" in paths and "/ready" in paths,
    "3_api_prefix_applied_to_api_calls": all(path.startswith("/api/") for path in api_paths),
    "4_tls_verification_enabled": session.verify is True,
    "5_openapi_skipped_when_disabled": results_without_openapi["openapi"] == "skipped",
    "6_openapi_not_requested_when_disabled": all(
        not url.endswith("/openapi.json") for _, url in session_without_openapi.calls
    ),
    "7_local_tls_opt_out_is_explicit": session_without_openapi.verify is False,
    "8_missing_token_rejected": missing_token_rejected,
    "9_origin_with_api_path_rejected": origin_with_path_rejected,
}

print(json.dumps(results, indent=2))
failures = {name: value for name, value in results.items() if value is not True}
assert not failures, failures
