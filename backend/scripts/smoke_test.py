import argparse
import os
import sys
from typing import Any

import requests


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is required.")
    return value


def assert_status(response: requests.Response, expected: int, label: str) -> Any:
    if response.status_code != expected:
        raise RuntimeError(f"{label} failed with HTTP {response.status_code}.")
    if response.content:
        try:
            return response.json()
        except ValueError as exc:
            raise RuntimeError(f"{label} returned non-JSON response.") from exc
    return None


def run_smoke_test(base_url: str, admin_email: str, admin_password: str, timeout: float) -> dict[str, str]:
    base_url = base_url.rstrip("/")
    session = requests.Session()
    results: dict[str, str] = {}

    assert_status(session.get(f"{base_url}/health", timeout=timeout), 200, "health")
    results["health"] = "ok"

    assert_status(session.get(f"{base_url}/ready", timeout=timeout), 200, "ready")
    results["ready"] = "ok"

    assert_status(session.get(f"{base_url}/openapi.json", timeout=timeout), 200, "openapi")
    results["openapi"] = "ok"

    token_response = session.post(
        f"{base_url}/auth/login",
        data={"username": admin_email, "password": admin_password},
        timeout=timeout,
    )
    token_payload = assert_status(token_response, 200, "admin login")
    token = token_payload.get("access_token")
    if not token:
        raise RuntimeError("admin login did not return an access token.")

    headers = {"Authorization": f"Bearer {token}"}
    results["admin_login"] = "ok"

    assert_status(session.get(f"{base_url}/admin/sources/", headers=headers, timeout=timeout), 200, "admin sources")
    results["admin_sources"] = "ok"

    assert_status(
        session.get(f"{base_url}/admin/crawler/status", headers=headers, timeout=timeout),
        200,
        "crawler status",
    )
    results["crawler_status"] = "ok"

    assert_status(session.get(f"{base_url}/notices/", timeout=timeout), 200, "public notices")
    results["public_notices"] = "ok"

    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run staging smoke checks against the API.")
    parser.add_argument("--base-url", default=os.getenv("SMOKE_BASE_URL", "http://localhost:8000"))
    parser.add_argument("--timeout", type=float, default=float(os.getenv("SMOKE_TIMEOUT", "10")))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        results = run_smoke_test(
            base_url=args.base_url,
            admin_email=require_env("SMOKE_ADMIN_EMAIL"),
            admin_password=require_env("SMOKE_ADMIN_PASSWORD"),
            timeout=args.timeout,
        )
    except Exception as exc:
        print(f"Smoke test failed: {exc}", file=sys.stderr)
        return 1

    for name, status in results.items():
        print(f"{name}: {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


