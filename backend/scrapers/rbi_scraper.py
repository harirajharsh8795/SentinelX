from typing import List
from scrapers.base_scraper import BaseScraper, ScrapedItem


class RBIScraper(BaseScraper):
    regulator = "RBI"
    base_url = "https://www.rbi.org.in/Scripts/NotificationUser.aspx"
    listing_urls = [
        "https://www.rbi.org.in/Scripts/NotificationUser.aspx",
        "https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx",
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
