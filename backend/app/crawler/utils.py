import re
import urllib.parse
import hashlib

TRACKING_QUERY_PREFIXES = ("utm_",)
TRACKING_QUERY_PARAMS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
}

def normalize_title(title: str) -> str:
    """
    Normalizes a title string.
    - Removes double/extra spaces
    - Replaces newlines (\n, \r) with simple spaces
    - Strips leading/trailing spaces
    """
    if not title:
        return ""
    title = title.replace("\n", " ").replace("\r", " ")
    title = re.sub(r'\s+', ' ', title)
    return title.strip().lower()

def normalize_url(url: str, base_url: str) -> str:
    """
    Normalizes a URL.
    - Resolves relative URLs using base_url
    - Removes leading/trailing spaces
    - Removes fragments and common tracking query params
    - Sorts remaining query params for stable duplicate detection
    """
    if not url:
        return ""
    url = url.strip()
    joined_url = urllib.parse.urljoin(base_url, url)
    parsed = urllib.parse.urlparse(joined_url)

    netloc = parsed.netloc.lower()
    if parsed.scheme == "http" and netloc.endswith(":80"):
        netloc = netloc[:-3]
    if parsed.scheme == "https" and netloc.endswith(":443"):
        netloc = netloc[:-4]

    path = parsed.path or "/"
    if len(path) > 1:
        path = path.rstrip("/")

    query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    filtered_pairs = [
        (key, value)
        for key, value in query_pairs
        if key.lower() not in TRACKING_QUERY_PARAMS
        and not key.lower().startswith(TRACKING_QUERY_PREFIXES)
    ]
    query = urllib.parse.urlencode(sorted(filtered_pairs), doseq=True)

    return urllib.parse.urlunparse(
        (parsed.scheme.lower(), netloc, path, parsed.params, query, "")
    )

def generate_fingerprint(institution_id: int, normalized_title: str, normalized_url: str) -> str:
    """
    Generates a SHA-256 fingerprint from institution_id, normalized_title, and normalized_url.
    """
    raw_str = f"{institution_id}|{normalized_title}|{normalized_url}"
    return hashlib.sha256(raw_str.encode('utf-8')).hexdigest()
