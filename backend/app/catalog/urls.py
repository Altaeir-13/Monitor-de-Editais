"""URL normalization shared by catalog validation and national seeding."""

from __future__ import annotations

from urllib.parse import SplitResult, urlsplit, urlunsplit


class URLNormalizationError(ValueError):
    """Raised when a catalog URL is not a valid public HTTP(S) URL."""


def normalize_url(value: str) -> str:
    """Return a stable HTTP(S) URL suitable for deduplication.

    Scheme and host are lower-cased, IDNs are converted to ASCII, default ports
    and fragments are removed, and trailing slashes are removed consistently.
    Query strings are preserved verbatim because they can select a real source.
    """

    if not isinstance(value, str) or not value.strip():
        raise URLNormalizationError("URL must be a non-empty string")
    raw = value.strip()
    if any(character.isspace() for character in raw):
        raise URLNormalizationError(f"URL must not contain whitespace: {value!r}")

    try:
        parsed = urlsplit(raw)
        port = parsed.port
    except ValueError as exc:
        raise URLNormalizationError(f"invalid URL {value!r}: {exc}") from exc

    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        raise URLNormalizationError(
            f"URL scheme must be http or https, got {parsed.scheme!r}"
        )
    if not parsed.hostname:
        raise URLNormalizationError(f"URL must include a host: {value!r}")
    if parsed.username is not None or parsed.password is not None:
        raise URLNormalizationError("catalog URLs must not contain credentials")

    try:
        hostname = parsed.hostname.encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise URLNormalizationError(f"invalid URL host {parsed.hostname!r}") from exc
    if ":" in hostname:  # IPv6 literals require brackets in a URL authority.
        hostname = f"[{hostname}]"

    default_port = (scheme == "http" and port == 80) or (
        scheme == "https" and port == 443
    )
    netloc = hostname if port is None or default_port else f"{hostname}:{port}"
    path = parsed.path.rstrip("/")
    normalized = SplitResult(scheme, netloc, path, parsed.query, "")
    return urlunsplit(normalized)


__all__ = ["URLNormalizationError", "normalize_url"]
