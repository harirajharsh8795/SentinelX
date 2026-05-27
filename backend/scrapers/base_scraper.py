"""
Phase 8 — Base scraper for regulatory circular discovery.
"""
import hashlib
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from utils.logger import get_logger

logger = get_logger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (compatible; SentinelXBot/1.0; +https://sentinelx.internal/bot)"
)
REQUEST_TIMEOUT = 25


@dataclass
class ScrapedItem:
    title: str
    url: str
    regulator: str
    content_type: str = "pdf"  # pdf | html


class BaseScraper(ABC):
    regulator: str = ""
    base_url: str = ""
    max_items_per_run: int = 5

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def fetch_page(self, url: str) -> Optional[str]:
        try:
            resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.text
        except Exception as exc:
            logger.warning("[%s] Failed to fetch %s: %s", self.regulator, url, exc)
            return None

    def download_bytes(self, url: str) -> Optional[bytes]:
        try:
            resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "")
            if "pdf" in content_type.lower() or url.lower().endswith(".pdf"):
                return resp.content
            return None
        except Exception as exc:
            logger.warning("[%s] Failed to download %s: %s", self.regulator, url, exc)
            return None

    def extract_pdf_links(self, html: str, base_url: str) -> List[ScrapedItem]:
        soup = BeautifulSoup(html, "html.parser")
        items: List[ScrapedItem] = []
        seen = set()

        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()
            if not href or href.startswith("#"):
                continue
            full_url = urljoin(base_url, href)
            if full_url in seen:
                continue
            lower = full_url.lower()
            if not (lower.endswith(".pdf") or "pdf" in lower or "notification" in lower):
                continue
            if not lower.endswith(".pdf"):
                continue
            title = tag.get_text(strip=True) or urlparse(full_url).path.split("/")[-1]
            if len(title) < 5:
                title = urlparse(full_url).path.split("/")[-1]
            seen.add(full_url)
            items.append(ScrapedItem(title=title[:200], url=full_url, regulator=self.regulator))
            if len(items) >= self.max_items_per_run:
                break
        return items

    @staticmethod
    def url_hash(url: str) -> str:
        return hashlib.sha256(url.encode()).hexdigest()[:32]

    @abstractmethod
    def discover(self) -> List[ScrapedItem]:
        """Discover new regulatory PDFs from the source website."""
        ...
