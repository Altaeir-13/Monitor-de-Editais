import re
import urllib.parse
import hashlib

def normalize_title(title: str) -> str:
    """
    Normalizes a title string.
    - Removes double/extra spaces
    - Replaces newlines (\n, \r) with simple spaces
    - Strips leading/trailing spaces
    """
    if not title:
        return ""
    # Replace \n and \r with spaces
    title = title.replace("\n", " ").replace("\r", " ")
    # Replace multiple spaces with a single space
    title = re.sub(r'\s+', ' ', title)
    return title.strip().lower()

def normalize_url(url: str, base_url: str) -> str:
    """
    Normalizes a URL.
    - Resolves relative URLs using base_url
    - Removes leading/trailing spaces
    - Removes fragments (hashtags like #anchor)
    """
    if not url:
        return ""
    url = url.strip()
    # Join with base_url
    joined_url = urllib.parse.urljoin(base_url, url)
    # Remove fragments
    parsed = urllib.parse.urlparse(joined_url)
    normalized = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, parsed.query, ''))
    return normalized

def generate_fingerprint(institution_id: int, normalized_title: str, normalized_url: str) -> str:
    """
    Generates a SHA-256 fingerprint from institution_id, normalized_title, and normalized_url.
    """
    raw_str = f"{institution_id}|{normalized_title}|{normalized_url}"
    return hashlib.sha256(raw_str.encode('utf-8')).hexdigest()
