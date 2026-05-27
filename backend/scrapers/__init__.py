from scrapers.rbi_scraper import RBIScraper
from scrapers.sebi_scraper import SEBIScraper
from scrapers.certin_scraper import CERTINScraper

SCRAPERS = {
    "RBI": RBIScraper(),
    "SEBI": SEBIScraper(),
    "CERTIN": CERTINScraper(),
}
