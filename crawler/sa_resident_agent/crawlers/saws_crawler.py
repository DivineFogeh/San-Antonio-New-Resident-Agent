"""
sa_resident_agent/crawlers/saws_crawler.py

SAWS (San Antonio Water System) crawler — targets new service,
rates, billing, and account setup pages.
"""

from __future__ import annotations

import logging
from urllib.parse import urljoin, urlparse

from playwright.sync_api import Browser, Page
from bs4 import BeautifulSoup

from sa_resident_agent.crawlers.base_crawler import BaseCrawler, CrawledPage

logger = logging.getLogger(__name__)

SEED_URLS = [
    "https://www.saws.org/",
    "https://www.saws.org/service/",
    "https://www.saws.org/service/start-stop-service/",
    "https://www.saws.org/customer-self-service-options/i-need-to-start-stop-saws-service/",
    "https://www.saws.org/service/pay-bill/",
    "https://www.saws.org/service/water-sewer-rates/",
    "https://www.saws.org/service/water-sewer-rates/residential-water-service/",
    "https://www.saws.org/service/pay-bill/payment-arrangements/",
    "https://www.saws.org/conservation/",
]

ALLOWED_DOMAIN = "saws.org"
ALLOWED_PATH_PREFIXES = [
    "/service/",
    "/your-account/",
    "/conservation/",
]


class SAWSCrawler(BaseCrawler):
    provider = "SAWS"
    seed_urls = SEED_URLS
    MAX_PAGES = 25

    def should_follow(self, url: str) -> bool:
        parsed = urlparse(url)
        if ALLOWED_DOMAIN not in parsed.netloc:
            return False
        return any(parsed.path.startswith(prefix) for prefix in ALLOWED_PATH_PREFIXES)

    def _fetch_page(self, browser: Browser, url: str) -> CrawledPage:
        from datetime import datetime, timezone

        page: Page = browser.new_page()
        page.set_extra_http_headers({"User-Agent": "SA-Resident-Agent-Bot/1.0 (educational project)"})

        try:
            page.goto(url, timeout=self.TIMEOUT_MS, wait_until="domcontentloaded")
            html = page.content()
        finally:
            page.close()

        soup = BeautifulSoup(html, "lxml")
        links = self._links_from_soup(soup, url)

        for tag in soup(self.STRIP_TAGS):
            tag.decompose()

        title = soup.title.get_text(strip=True) if soup.title else url
        text = soup.get_text(separator="\n", strip=True)

        result = CrawledPage(
            url=url,
            provider=self.provider,
            title=title,
            text=text,
            scraped_at=datetime.now(timezone.utc).isoformat(),
            metadata={"discovered_links": links},
        )
        result._links = links  # type: ignore[attr-defined]
        return result

    def _extract_links(self, page_text: str, base_url: str) -> list[str]:
        if self._results:
            last = self._results[-1]
            return getattr(last, "_links", [])
        return []

    def _links_from_soup(self, soup: BeautifulSoup, base_url: str) -> list[str]:
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
                continue
            full_url = urljoin(base_url, href).split("#")[0].rstrip("/")
            if self.should_follow(full_url) and full_url not in links:
                links.append(full_url)
        return links
