"""Phase 8: Scraper unit tests (no live network required)."""
from scrapers.base_scraper import BaseScraper, ScrapedItem
from scrapers.rbi_scraper import RBIScraper


SAMPLE_HTML = """
<html><body>
<a href="/docs/circular_2026.pdf">RBI KYC Master Direction 2026</a>
<a href="https://www.rbi.org.in/pdf/AML_Guidelines.pdf">AML Guidelines</a>
<a href="/about">About Us</a>
</body></html>
"""


def test_extract_pdf_links():
    scraper = RBIScraper()
    items = scraper.extract_pdf_links(SAMPLE_HTML, "https://www.rbi.org.in/")
    assert len(items) == 2
    assert all(i.url.endswith(".pdf") for i in items)
    assert items[0].regulator == "RBI"


def test_url_hash_stable():
    h1 = BaseScraper.url_hash("https://example.com/doc.pdf")
    h2 = BaseScraper.url_hash("https://example.com/doc.pdf")
    assert h1 == h2


def test_scrape_status_api():
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    response = client.get("/api/scrape/status")
    assert response.status_code == 200
    assert "stats" in response.json()
