from typing import List
from scrapers.base_scraper import BaseScraper, ScrapedItem


class SEBIScraper(BaseScraper):
    regulator = "SEBI"
    base_url = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1"
    listing_urls = [
        "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1",
        "https://www.sebi.gov.in/legal/circulars.html",
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
