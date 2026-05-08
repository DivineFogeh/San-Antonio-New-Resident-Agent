"""
sa_resident_agent/crawlers/city_crawler.py

City of San Antonio crawler — targets new resident registration,
permits, and municipal service pages.
"""

from __future__ import annotations

import logging
from urllib.parse import urljoin, urlparse

from playwright.sync_api import Browser, Page
from bs4 import BeautifulSoup

from sa_resident_agent.crawlers.base_crawler import BaseCrawler, CrawledPage

logger = logging.getLogger(__name__)

SEED_URLS = [
    "https://www.sanantonio.gov/",
    "https://www.sa.gov/Community/Housing-Neighborhoods",
    "https://www.sanantonio.gov/DSD/Permits",
    "https://www.sanantonio.gov/311",
    "https://www.sa.gov/Directory/Departments/NHSD",
]

ALLOWED_DOMAINS = ["sanantonio.gov", "sa.gov"]
ALLOWED_PATH_PREFIXES = [
    "/Housing-Neighborhoods/",
    "/DSD/",
    "/311",
    "/finance/",
    "/publicworks/",
    "/solidwaste/",
    "/Community/",
    "/Directory/",
]


class CitySACrawler(BaseCrawler):
    provider = "CITY_SA"
    seed_urls = SEED_URLS
    MAX_PAGES = 20

    def should_follow(self, url: str) -> bool:
        parsed = urlparse(url)
        domain_ok = any(d in parsed.netloc for d in ALLOWED_DOMAINS)
        if not domain_ok:
            return False
        return any(parsed.path.startswith(prefix) for prefix in ALLOWED_PATH_PREFIXES)

    def _fetch_page(self, browser: Browser, url: str) -> CrawledPage:
        from datetime import datetime, timezone

        page: Page = browser.new_page()
        page.set_extra_http_headers({"User-Agent": "SA-Resident-Agent-Bot/1.0 (educational project)"})

        try:
            page.goto(url, timeout=self.TIMEOUT_MS, wait_until="domcontentloaded")
            # City site sometimes lazy-loads — wait a beat for JS
            page.wait_for_timeout(1500)
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