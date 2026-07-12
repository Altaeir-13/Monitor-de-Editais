import argparse
import os
import sys
from typing import Any
from urllib.parse import urlparse

import requests


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is required.")
    return value


def parse_bool(value: str, *, name: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"{name} must be true or false.")


def normalize_public_origin(base_url: str) -> str:
    base_url = base_url.strip().rstrip("/")
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RuntimeError("SMOKE_BASE_URL must be an absolute HTTP or HTTPS origin.")
    if parsed.path not in {"", "/"} or parsed.params or parsed.query or parsed.fragment:
        raise RuntimeError("SMOKE_BASE_URL must contain only the public origin, without /api or query parameters.")
    return base_url


def build_api_base_url(base_url: str, api_prefix: str) -> str:
    base_url = normalize_public_origin(base_url)
    prefix = api_prefix.strip()
    if prefix in {"", "/"}:
        return base_url
    if not prefix.startswith("/"):
        prefix = f"/{prefix}"
    return f"{base_url}{prefix.rstrip('/')}"


def assert_status(response: requests.Response, expected: int, label: str) -> Any:
    if response.status_code != expected:
        raise RuntimeError(f"{label} failed with HTTP {response.status_code}.")
    if response.content:
        try:
            return response.json()
        except ValueError as exc:
            raise RuntimeError(f"{label} returned non-JSON response.") from exc
    return None


def assert_ok_payload(payload: Any, label: str) -> None:
    if not isinstance(payload, dict) or payload.get("status") != "ok":
        raise RuntimeError(f"{label} returned an unexpected payload.")


def run_smoke_test(
    base_url: str,
    admin_email: str,
    admin_password: str,
    timeout: float,
    *,
    api_prefix: str = "/api",
    expect_openapi: bool = True,
    verify_tls: bool = True,
    session: requests.Session | None = None,
) -> dict[str, str]:
    origin_url = normalize_public_origin(base_url)
    api_base_url = build_api_base_url(origin_url, api_prefix)
    session = session or requests.Session()
    session.verify = verify_tls
    results: dict[str, str] = {}

    health_payload = assert_status(session.get(f"{origin_url}/health", timeout=timeout), 200, "health")
    assert_ok_payload(health_payload, "health")
    results["health"] = "ok"

    ready_payload = assert_status(session.get(f"{origin_url}/ready", timeout=timeout), 200, "ready")
    assert_ok_payload(ready_payload, "ready")
    results["ready"] = "ok"

    if expect_openapi:
        openapi_payload = assert_status(
            session.get(f"{api_base_url}/openapi.json", timeout=timeout),
            200,
            "openapi",
        )
        if not isinstance(openapi_payload, dict) or "openapi" not in openapi_payload:
            raise RuntimeError("openapi returned an unexpected payload.")
        results["openapi"] = "ok"
    else:
        results["openapi"] = "skipped"

    token_response = session.post(
        f"{api_base_url}/auth/login",
        data={"username": admin_email, "password": admin_password},
        timeout=timeout,
    )
    token_payload = assert_status(token_response, 200, "admin login")
    if not isinstance(token_payload, dict):
        raise RuntimeError("admin login returned an unexpected payload.")
    token = token_payload.get("access_token")
    if not token:
        raise RuntimeError("admin login did not return an access token.")

    headers = {"Authorization": f"Bearer {token}"}
    results["admin_login"] = "ok"

    assert_status(
        session.get(f"{api_base_url}/admin/sources/", headers=headers, timeout=timeout),
        200,
        "admin sources",
    )
    results["admin_sources"] = "ok"

    assert_status(
        session.get(f"{api_base_url}/admin/crawler/status", headers=headers, timeout=timeout),
        200,
        "crawler status",
    )
    results["crawler_status"] = "ok"

    assert_status(session.get(f"{api_base_url}/notices/", timeout=timeout), 200, "public notices")
    results["public_notices"] = "ok"

    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run staging smoke checks against the public origin.")
    parser.add_argument("--base-url", default=os.getenv("SMOKE_BASE_URL", "https://localhost"))
    parser.add_argument("--api-prefix", default=os.getenv("SMOKE_API_PREFIX", "/api"))
    parser.add_argument("--timeout", type=float, default=float(os.getenv("SMOKE_TIMEOUT", "10")))
    parser.add_argument("--verify-tls", default=os.getenv("SMOKE_TLS_VERIFY", "true"))
    parser.add_argument(
        "--expect-openapi",
        default=os.getenv("SMOKE_EXPECT_OPENAPI", "false"),
        help="Whether /api/openapi.json must be available (true/false).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        results = run_smoke_test(
            base_url=args.base_url,
            admin_email=require_env("SMOKE_ADMIN_EMAIL"),
            admin_password=require_env("SMOKE_ADMIN_PASSWORD"),
            timeout=args.timeout,
            api_prefix=args.api_prefix,
            expect_openapi=parse_bool(args.expect_openapi, name="SMOKE_EXPECT_OPENAPI"),
            verify_tls=parse_bool(args.verify_tls, name="SMOKE_TLS_VERIFY"),
        )
    except Exception as exc:
        print(f"Smoke test failed: {exc}", file=sys.stderr)
        return 1

    for name, status in results.items():
        print(f"{name}: {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
