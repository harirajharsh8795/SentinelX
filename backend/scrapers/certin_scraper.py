from typing import List
from scrapers.base_scraper import BaseScraper, ScrapedItem


class CERTINScraper(BaseScraper):
    regulator = "CERTIN"
    base_url = "https://www.cert-in.org.in/"
    listing_urls = [
        "https://www.cert-in.org.in/",
        "https://www.cert-in.org.in/pdf/",
    ]

    def discover(self) -> List[ScrapedItem]:
        all_items: List[ScrapedItem] = []
        for url in self.listing_urls:
            html = self.fetch_page(url)
            if html:
                all_items.extend(self.extract_pdf_links(html, url))
            if len(all_items) >= self.max_items_per_run:
                break
        return all_items[: self.max_items_per_run]
