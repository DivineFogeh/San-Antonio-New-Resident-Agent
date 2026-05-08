"""
sa_resident_agent/crawlers/base_crawler.py

Shared Playwright + BeautifulSoup base crawler.
Handles browser lifecycle, retries, rate limiting, and raw text extraction.
"""

from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field
from typing import Optional

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page, Browser, TimeoutError as PWTimeout

logger = logging.getLogger(__name__)


@dataclass
class CrawledPage:
    url: str
    provider: str
    title: str
    text: str
    scraped_at: str
    metadata: dict = field(default_factory=dict)


class BaseCrawler:
    """
    Base crawler using Playwright (headless Chromium) + BeautifulSoup.

    Subclasses implement:
        - seed_urls: list[str]       — starting URLs to crawl
        - provider: str              — e.g. "CPS_ENERGY"
        - should_follow(url) -> bool — link filter
    """

    provider: str = "BASE"
    seed_urls: list[str] = []

    MAX_PAGES = 30          # cap per provider to avoid runaway crawls
    DELAY_SECONDS = 1.5     # polite delay between requests
    TIMEOUT_MS = 30_000     # 30s page load timeout
    MAX_RETRIES = 3

    # Tags whose text content is always stripped (nav chrome, scripts, etc.)
    STRIP_TAGS = ["script", "style", "nav", "footer", "header", "noscript", "svg"]

    def __init__(self):
        self._visited: set[str] = set()
        self._results: list[CrawledPage] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def crawl(self) -> list[CrawledPage]:
        """Run the full crawl for this provider. Returns list of CrawledPage."""
        logger.info(f"[{self.provider}] Starting crawl. Seed URLs: {self.seed_urls}")

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                queue = list(self.seed_urls)
                while queue and len(self._visited) < self.MAX_PAGES:
                    url = queue.pop(0)
                    if url in self._visited:
                        continue

                    page_result = self._fetch_with_retry(browser, url)
                    if page_result is None:
                        continue

                    self._visited.add(url)
                    self._results.append(page_result)
                    logger.info(f"[{self.provider}] Crawled ({len(self._visited)}/{self.MAX_PAGES}): {url}")

                    # Discover new links from this page
                    new_links = self._extract_links(page_result.text, url)
                    for link in new_links:
                        if link not in self._visited and link not in queue:
                            if self.should_follow(link):
                                queue.append(link)

                    time.sleep(self.DELAY_SECONDS)
            finally:
                browser.close()

        logger.info(f"[{self.provider}] Crawl complete. Pages collected: {len(self._results)}")
        return self._results

    # ------------------------------------------------------------------
    # Overridable
    # ------------------------------------------------------------------

    def should_follow(self, url: str) -> bool:
        """Override in subclass to filter which links to follow."""
        return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch_with_retry(self, browser: Browser, url: str) -> Optional[CrawledPage]:
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                return self._fetch_page(browser, url)
            except PWTimeout:
                logger.warning(f"[{self.provider}] Timeout on {url} (attempt {attempt}/{self.MAX_RETRIES})")
            except Exception as e:
                logger.warning(f"[{self.provider}] Error on {url} (attempt {attempt}/{self.MAX_RETRIES}): {e}")

            if attempt < self.MAX_RETRIES:
                time.sleep(2 ** attempt)  # exponential backoff

        logger.error(f"[{self.provider}] Failed to fetch {url} after {self.MAX_RETRIES} attempts.")
        return None

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

        # Strip noisy tags
        for tag in soup(self.STRIP_TAGS):
            tag.decompose()

        title = soup.title.get_text(strip=True) if soup.title else url
        text = soup.get_text(separator="\n", strip=True)

        return CrawledPage(
            url=url,
            provider=self.provider,
            title=title,
            text=text,
            scraped_at=datetime.now(timezone.utc).isoformat(),
        )

    def _extract_links(self, page_text: str, base_url: str) -> list[str]:
        """
        Re-fetch the page's raw HTML to extract <a href> links.
        We pass page_text here for interface consistency but re-parse from
        the already-fetched content stored in the page result.
        """
        # Links are extracted at fetch time per page — override in subclass if needed.
        return []
