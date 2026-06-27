import shutil
import subprocess

import requests
from abc import ABC, abstractmethod
from typing import List, Dict, Any

from app.crawler.certificates import get_requests_verify_path

class BaseScraper(ABC):
    """
    Abstract base class for all scrapers/crawlers.
    Provides common functionality like fetching HTML content safely.
    """
    def __init__(self, source_url: str):
        self.source_url = source_url
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "MonitorDeEditaisBot/1.0 (+https://seusite.com)"
        })
        self.session.verify = get_requests_verify_path()
        self.timeout = 15

    def fetch(self, url: str) -> str:
        """
        Fetches the HTML content of the given URL.
        Raises an exception if the request fails.
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return self._decode_response(response)
        except requests.exceptions.SSLError as exc:
            return self._fetch_with_curl(url, exc)

    def _fetch_with_curl(self, url: str, original_error: Exception) -> str:
        curl_path = shutil.which("curl.exe") or shutil.which("curl")
        if not curl_path:
            raise original_error

        command = [
            curl_path,
            "-L",
            "--fail",
            "--silent",
            "--show-error",
            "--max-time",
            str(self.timeout),
            "-A",
            self.session.headers.get("User-Agent", "MonitorDeEditaisBot/1.0"),
            url,
        ]
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=self.timeout + 5,
            check=False,
        )
        if completed.returncode != 0:
            raise requests.exceptions.SSLError(
                f"{original_error}; curl fallback failed: {completed.stderr.strip()}"
            )
        return completed.stdout

    def _decode_response(self, response) -> str:
        encoding = response.encoding
        if not encoding or encoding.lower() in {"iso-8859-1", "latin-1"}:
            encoding = response.apparent_encoding or "utf-8"
        return response.content.decode(encoding or "utf-8", errors="replace")

    @abstractmethod
    def extract(self, html: str) -> List[Dict[str, Any]]:
        """
        Parses the HTML and extracts a list of raw notices.
        Must be implemented by subclasses.
        Returns a list of dicts with at least 'title' and 'url'.
        """
        pass

    def run(self) -> List[Dict[str, Any]]:
        """
        Executes the scraping process: fetch -> extract.
        """
        html = self.fetch(self.source_url)
        return self.extract(html)
