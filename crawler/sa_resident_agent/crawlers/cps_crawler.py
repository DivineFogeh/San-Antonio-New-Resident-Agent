"""
sa_resident_agent/crawlers/cps_crawler.py

CPS Energy crawler — targets residential service pages:
rates, start/stop service, billing, and new customer enrollment.
"""

from __future__ import annotations

import logging
from urllib.parse import urljoin, urlparse

from playwright.sync_api import Browser, Page
from bs4 import BeautifulSoup

from sa_resident_agent.crawlers.base_crawler import BaseCrawler, CrawledPage

logger = logging.getLogger(__name__)

# Pages most relevant to a new resident setting up electricity
SEED_URLS = [
    "https://www.cpsenergy.com/",
    "https://www.cpsenergy.com/en/my-home.html",
    "https://www.cpsenergy.com/en/my-home/moving.html",
    "https://www.cpsenergy.com/startservice",
    "https://www.cpsenergy.com/en/customer-support/manage-my-account.html",
    "https://www.cpsenergy.com/en/customer-support/ways-to-pay-my-bill.html",
    "https://www.cpsenergy.com/en/my-home/redirect-request-services-home.html",
    "https://www.cpsenergy.com/en/customer-support/contact-us.html",
]

ALLOWED_DOMAIN = "cpsenergy.com"
ALLOWED_PATH_PREFIXES = [
    "/",
    "/en/my-home",
    "/en/customer-support",
    "/en/forms",
    "/en/external-sites",
    "/startservice",
    "/mma",
]


class CPSCrawler(BaseCrawler):
    provider = "CPS_ENERGY"
    seed_urls = SEED_URLS
    MAX_PAGES = 25

    def should_follow(self, url: str) -> bool:
        parsed = urlparse(url)
        if ALLOWED_DOMAIN not in parsed.netloc:
            return False
        return any(parsed.path.startswith(prefix) for prefix in ALLOWED_PATH_PREFIXES)

    # Override fetch to also extract links while we have the HTML
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

        # Store discovered links as metadata
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
        # Attach links so base crawler can queue them
        result._links = links  # type: ignore[attr-defined]
        return result

    def _extract_links(self, page_text: str, base_url: str) -> list[str]:
        # Links already extracted in _fetch_page and stored on the result object
        # Find the last result we added
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
