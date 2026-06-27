import os
import ssl
from pathlib import Path

import certifi

_BUNDLE_PATH = Path(__file__).resolve().parents[2] / ".cache" / "windows_ca_bundle.pem"


def get_requests_verify_path() -> str:
    """Return a CA bundle for requests without disabling TLS verification.

    On Windows, certifi can miss roots/intermediates trusted by the OS for
    Brazilian institutional sites. We merge certifi with the Windows ROOT and
    CA stores into a local bundle. On other platforms, certifi is used as-is.
    """
    if os.name != "nt":
        return certifi.where()

    try:
        return _build_windows_bundle()
    except Exception:
        return certifi.where()


def _build_windows_bundle() -> str:
    certifi_path = Path(certifi.where())
    certs = [certifi_path.read_text(encoding="ascii")]
    seen = set(certs)

    for store_name in ("ROOT", "CA"):
        for cert, encoding, _trust in ssl.enum_certificates(store_name):
            if encoding != "x509_asn":
                continue
            pem = ssl.DER_cert_to_PEM_cert(cert)
            if pem not in seen:
                seen.add(pem)
                certs.append(pem)

    _BUNDLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _BUNDLE_PATH.write_text("\n".join(certs), encoding="ascii")
    return str(_BUNDLE_PATH)
